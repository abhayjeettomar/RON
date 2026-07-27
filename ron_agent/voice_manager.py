import time
import threading
import tempfile
import os
import pyttsx3
import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
import numpy as np
import winsound
import queue

class VoiceState:
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"

class VoiceManager:
    def __init__(self):
        self.is_listening = False
        self.is_speaking = False
        self.post_speak_cooldown = 0.0
        self.state = VoiceState.IDLE
        self.override_status = None
        self.recognizer = sr.Recognizer()
        
        # Expand phonetic wake words to catch Google STT misinterpretations
        self.wake_words = [
            "hey ron", "hi ron", "hello ron", "ron", 
            "hey run", "hey aaron", "aaron", "iron",
            "heron", "hero", "hair on", "hey rom",
            "hey rowan", "rowan", "hey juan", "juan",
            "he ran", "hey wrong", "wrong"
        ]
        self._audio_queue = queue.Queue()
        self._tts_queue = queue.Queue()
        threading.Thread(target=self._tts_worker, daemon=True).start()

    def wake_up(self, silent=False):
        self.state = VoiceState.ACTIVE
        if not silent:
            try:
                import winsound
                winsound.Beep(800, 200)
            except Exception:
                pass

    def _tts_worker(self):
        try:
            import ctypes
            ctypes.windll.ole32.CoInitialize(None)
        except Exception:
            pass
            
        try:
            import win32com.client
            engine = win32com.client.Dispatch("SAPI.SpVoice")
            engine.Rate = 2  # Slightly faster than default
        except Exception:
            engine = None
            
        while True:
            item = self._tts_queue.get()
            if item is None: break
            text, on_complete = item
            
            self.is_speaking = True
            try:
                if engine:
                    engine.Speak(text)
                else:
                    time.sleep(1) # mock delay if engine failed
            except Exception as e:
                print(f"[Voice] TTS Error: {e}")
                try:
                    engine = win32com.client.Dispatch("SAPI.SpVoice")
                    engine.Rate = 2
                except: pass
            finally:
                self.post_speak_cooldown = time.time() + 1.0
                self.is_speaking = False
                if on_complete:
                    on_complete()
            self._tts_queue.task_done()

    def speak(self, text: str, on_complete=None):
        self._tts_queue.put((text, on_complete))

    def start_listening(self, text_callback, status_callback, mic_name=None):
        if self.is_listening:
            return
            
        self.is_listening = True
        self.state = VoiceState.IDLE
        threading.Thread(target=self._listen_loop, args=(text_callback, status_callback, mic_name), daemon=True).start()

    def stop_listening(self):
        self.is_listening = False

    def _listen_loop(self, text_callback, status_callback, mic_name=None):
        fs = 16000
        chunk_duration = 0.1
        chunk_samples = int(fs * chunk_duration)
        
        try:
            import ctypes
            ctypes.windll.ole32.CoInitialize(None)
            
            import soundcard as sc
            mic = sc.default_microphone()
            if mic_name:
                for m in sc.all_microphones():
                    if m.name == mic_name:
                        mic = m
                        break
            
            noise_baseline = None
            is_recording_speech = False
            silence_counter = 0
            manual_override_timer = 0
            speech_buffer = []
            
            with mic.recorder(samplerate=fs, channels=1) as rec:
                while self.is_listening:
                    if self.is_speaking or time.time() < self.post_speak_cooldown:
                        if self.is_speaking:
                            status_callback("Speaking...")
                        time.sleep(0.1)
                        # Flush the recorder queue
                        try:
                            rec.record(numframes=chunk_samples)
                        except Exception:
                            pass
                        is_recording_speech = False
                        speech_buffer.clear()
                        continue
                        
                    chunk = rec.record(numframes=chunk_samples)
                    
                    # soundcard returns floats from -1.0 to 1.0. Scale to 0-32767 for our VAD logic.
                    rms = np.sqrt(np.mean(np.square(chunk))) * 32767.0
                    
                    if noise_baseline is None:
                        noise_baseline = max(rms, 10.0)
                        continue
                        
                    # Dynamic threshold requires RMS to be 300% louder than background + 1000 fixed units
                    threshold = (noise_baseline * 3.0) + 1000.0  
                    
                    if self.override_status:
                        status_callback(self.override_status, rms)
                    elif not is_recording_speech:
                        if self.state == VoiceState.IDLE:
                            status_callback("Listening for 'Hey Ron'...", rms)
                        else:
                            status_callback("Listening for command...", rms)
                            
                        if rms > threshold:
                            is_recording_speech = True
                            speech_buffer = [chunk]
                            silence_counter = 0
                        else:
                            noise_baseline = (noise_baseline * 0.95) + (rms * 0.05)
                    else:
                        if not self.override_status:
                            if self.state == VoiceState.IDLE:
                                status_callback("Listening for 'Hey Ron'...", rms)
                            else:
                                status_callback("Hearing you...", rms)
                        
                        speech_buffer.append(chunk)
                        
                        if rms < threshold:
                            silence_counter += 1
                        else:
                            silence_counter = 0
                                
                        # Dual Silence Threshold:
                        # If IDLE (waiting for wake word), trigger fast (0.5s)
                        # If ACTIVE (recording command), trigger after 0.8s of silence (down from 1.5s for speed)
                        silence_limit = 5 if self.state == VoiceState.IDLE else 8
                        
                        if silence_counter >= silence_limit:
                            is_recording_speech = False
                            
                            if len(speech_buffer) > 5:
                                if not self.override_status:
                                    if self.state == VoiceState.IDLE:
                                        pass # Don't spam Processing when checking background for wake word
                                    else:
                                        status_callback("Processing...", rms)
                                        
                                recording = np.concatenate(speech_buffer, axis=0)
                                # Convert float32 to int16 PCM before saving
                                pcm_data = (recording * 32767.0).astype(np.int16)
                                
                                temp_wav = tempfile.mktemp(suffix=".wav")
                                sf.write(temp_wav, pcm_data, fs)
                                
                                with sr.AudioFile(temp_wav) as source:
                                    audio = self.recognizer.record(source)
                                
                                try:
                                    was_active = (self.state == VoiceState.ACTIVE)
                                    text = self.recognizer.recognize_google(audio)
                                    if text and text.strip():
                                        text_clean = text.strip()
                                        text_lower = text_clean.lower()
                                        
                                        if self.state == VoiceState.IDLE:
                                            for ww in self.wake_words:
                                                if text_lower.startswith(ww):
                                                    command = text_clean[len(ww):].strip()
                                                    while command and command[0] in ".,!?-":
                                                        command = command[1:].strip()
                                                    if command:
                                                        self.wake_up()
                                                        self.state = VoiceState.IDLE
                                                        text_callback(command)
                                                    else:
                                                        self.wake_up()
                                                    break
                                        else:
                                            self.state = VoiceState.IDLE
                                            text_callback(text_clean)
                                    else:
                                        if was_active:
                                            self.state = VoiceState.IDLE
                                except sr.UnknownValueError:
                                    if was_active:
                                        self.state = VoiceState.IDLE
                                except sr.RequestError as e:
                                    if was_active:
                                        self.state = VoiceState.IDLE
                                    print(f"STT Error: {e}")
                                    
                                try:
                                    os.remove(temp_wav)
                                except OSError:
                                    pass
                                    
                            speech_buffer.clear()
                            silence_counter = 0

        except Exception as e:
            print(f"Audio Stream Error: {e}")
            try:
                status_callback(f"Error: {e}")
            except Exception:
                pass
            self.is_listening = False
        finally:
            try:
                ctypes.windll.ole32.CoUninitialize()
            except Exception:
                pass
