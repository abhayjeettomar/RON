import re
import json
import urllib.request
import urllib.parse
import urllib.error
import os

class IntentParser:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.system_prompt = (
            "You are Ron, an offline desktop AI assistant with direct system integration.\n"
            "You can control the user's computer: open apps, type text, press keys, run commands, etc.\n\n"
            "CRITICAL RULES:\n"
            "1. When the user asks you to DO something (open app, type text, write code, etc.), you MUST output a JSON block with executable actions. NEVER just describe what you would do.\n"
            "2. Output EXACTLY ONE JSON block at the END of your response. Never multiple.\n"
            "3. Keep your text explanation SHORT — one or two sentences max before the JSON.\n"
            "4. NEVER show intermediate steps, progress updates, or partial action lists.\n"
            "5. NEVER make up system specs, file paths, or hardware info.\n"
            "6. To type text INTO an already-open app (like notepad, vscode, etc.), use type_text. The text will be typed into whatever app is currently focused.\n"
            "7. To clear existing text in an app, use press_key with ctrl+a then backspace BEFORE typing new text.\n"
            "8. If the user references an app that is already open (e.g. 'write code in vscode that is open'), do NOT open it again — just use type_text directly.\n"
            "9. When asked to write code, generate the ACTUAL code as the type_text details. Do not describe the code — type it.\n"
            "10. NEVER output JSON as a description or example. Every JSON block you output WILL be executed.\n"
            "11. If the user asks you to write a long text, hypothesis, or story but DOES NOT ask to type it into an app, DO NOT output any JSON. Just output the text naturally.\n\n"
            "Available actions:\n"
            "- {\"type\": \"open_app\", \"details\": \"notepad\"} (supports ANY installed app: chrome, gta 5, spotify, vscode, etc.)\n"
            "- {\"type\": \"close_app\", \"details\": \"notepad\"}\n"
            "- {\"type\": \"open_camera\", \"details\": \"\"}\n"
            "- {\"type\": \"type_text\", \"details\": \"the actual text or code to type into the focused app\"}\n"
            "- {\"type\": \"press_key\", \"details\": \"ctrl+a\"} (or enter, tab, backspace, ctrl+c, ctrl+v, ctrl+s, etc.)\n"
            "- {\"type\": \"open_url\", \"details\": \"google.com\"}\n"
            "- {\"type\": \"open_folder\", \"details\": \"C:\\\\Users\"}\n"
            "- {\"type\": \"change_volume\", \"details\": \"up\"}\n"
            "- {\"type\": \"take_screenshot\", \"details\": \"\"}\n"
            "- {\"type\": \"run_command\", \"details\": \"ipconfig\"}\n"
            "- {\"type\": \"write_file\", \"details\": \"C:\\\\path\\\\file.txt\", \"content\": \"text\"}\n"
            "- {\"type\": \"read_file\", \"details\": \"C:\\\\path\\\\file.txt\"}\n"
            "- {\"type\": \"wait\", \"details\": \"10\"}\n\n"
            "EXAMPLES:\n\n"
            "User: 'open notepad and type hello'\n"
            "Opening Notepad and typing for you.\n"
            "```json\n"
            "{\"actions\": [{\"type\": \"open_app\", \"details\": \"notepad\"}, "
            "{\"type\": \"type_text\", \"details\": \"hello\"}], "
            "\"explanation\": \"Opening Notepad and typing hello.\"}\n"
            "```\n\n"
            "User: 'can you write a python code to take input and print it in the open app'\n"
            "Typing the code for you now.\n"
            "```json\n"
            "{\"actions\": [{\"type\": \"type_text\", \"details\": \"name = input('Enter your name: ')\\nprint(f'Hello, {name}!')\"}], "
            "\"explanation\": \"Typing Python input/print code.\"}\n"
            "```\n\n"
            "User: 'you just opened notepad right? now type a poem in it'\n"
            "Typing a poem into the open Notepad.\n"
            "```json\n"
            "{\"actions\": [{\"type\": \"type_text\", \"details\": \"Roses are red,\\nViolets are blue,\\nRon is your assistant,\\nAlways here for you.\"}], "
            "\"explanation\": \"Typing a poem.\"}\n"
            "```\n\n"
            "For general chat (hi, how are you, what time is it, etc.), respond naturally without any JSON."
        )
        
        self.chat_prompt = (
            "You are Ron, an incredibly smart, fast, and helpful AI desktop assistant. "
            "Respond to the user naturally and conversationally. Keep your answers brief (1-3 sentences) "
            "so they can be spoken quickly."
        )

    def parse_instruction(self, text: str, chat_history: list = None) -> dict:
        """Parses user instruction. Tries fast local rule-based parser first, then falls back to Gemini/Ollama."""
        # 1. Try fast local rule-based parsing first (0ms latency for simple commands)
        try:
            rules_res = self.parse_with_rules(text)
            if rules_res and rules_res.get("actions"):
                return rules_res
        except Exception:
            pass
            
        # 2. Check if this is a purely conversational prompt (no automation verbs)
        verbs = ["launch", "execute", "screenshot", "volume", "cmd", "shell", "capture", "terminate", "delete", "search"]
        text_lower = text.lower()
        is_chat = not any(re.search(rf"\b{verb}\b", text_lower) for verb in verbs)
        
        # Override strict regex if the prompt is obviously a conversational question
        if text_lower.startswith(("what", "who", "why", "how", "when", "where", "hi", "hello", "hey", "yo")):
            is_chat = True
            
        # 3. Try Gemini API first for instant generation (if key exists AND we are in Online Mode)
        app_mode = os.environ.get("RON_APP_MODE", "offline")
        if app_mode == "online":
            try:
                return self.parse_with_gemini(text, chat_history, is_chat)
            except Exception as e:
                return {
                    "actions": [],
                    "explanation": f"Gemini API Error: {str(e)}\n\nPlease check your API key or network connection.",
                    "mode": "Error"
                }
            
        # 4. Try Ollama (slower, ~15s timeout for automation, fast for chat)
        try:
            return self.parse_with_ollama(text, chat_history, is_chat)
        except Exception as e:
            # Fallback if Ollama fails entirely (or times out)
            return {"actions": [], "explanation": f"Failed to parse with Ollama ({e}). And no simple rules matched. For instant 1-second responses, please add a gemini_api_key.txt file to your antigravity folder!", "mode": "Error"}

    def check_ollama_status(self) -> bool:
        """Checks if the local Ollama service is running."""
        try:
            req = urllib.request.Request(self.ollama_url, method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as response:
                return response.status == 200
        except Exception:
            return False

    def get_best_model_name(self) -> str:
        """Queries local Ollama tags and returns the best model name available."""
        try:
            url = f"{self.ollama_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = data.get("models", [])
                if models:
                    for m in models:
                        name = m.get("name", "")
                        if "llama3" in name:
                            return name
                    for m in models:
                        name = m.get("name", "")
                        if "phi3" in name or "phi" in name:
                            return name
                    return models[0].get("name", "llama3")
        except Exception:
            pass
        return "llama3"

    def extract_all_json_objects(self, text: str) -> list:
        """Finds ALL top-level JSON objects in the text using stack-based bracket matching."""
        results = []
        i = 0
        while i < len(text):
            if text[i] == '{':
                start = i
                stack = []
                for j in range(i, len(text)):
                    if text[j] == '{':
                        stack.append('{')
                    elif text[j] == '}':
                        stack.pop()
                        if not stack:
                            results.append(text[start:j+1])
                            i = j + 1
                            break
                else:
                    break
            else:
                i += 1
        return results

    def _clean_explanation(self, raw_text: str, json_blocks: list) -> str:
        """Aggressively strips ALL JSON blocks, code fences, and noise from explanation text."""
        cleaned = raw_text
        # Remove all JSON blocks
        for block in json_blocks:
            cleaned = cleaned.replace(block, "")
        # Remove code fences
        cleaned = re.sub(r"```(?:json)?", "", cleaned)
        # Remove noise patterns the model likes to output
        cleaned = re.sub(r"Actions:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"Action:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'"[^"]*\.\.\.\s*done!"', "", cleaned)
        cleaned = re.sub(r"Here'?s? (?:the|what'?s?) (?:happening|going on):?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"That'?s? it!.*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"Let me (?:know|correct|do).*", "", cleaned, flags=re.IGNORECASE)
        # Collapse whitespace
        cleaned = re.sub(r"\n{2,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        return cleaned.strip()

    def parse_with_gemini(self, text: str, chat_history: list = None, is_chat: bool = False) -> dict:
        """Sends prompt to Gemini API for instant generation."""
        import os
        key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gemini_api_key.txt")
        if not os.path.exists(key_path):
            raise ValueError("No gemini_api_key.txt found")
            
        with open(key_path, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
            
        if not api_key:
            raise ValueError("Empty gemini_api_key.txt")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={api_key}"
        
        prompt_to_use = self.chat_prompt if is_chat else self.system_prompt
        
        # Build contents array with alternating roles for Gemini
        contents = []
        if chat_history:
            for msg in chat_history[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                # Gemini rejects consecutive messages with the same role. We must merge them.
                if contents and contents[-1]["role"] == role:
                    contents[-1]["parts"][0]["text"] += "\n" + msg["content"]
                else:
                    contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        # Append current user text
        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"][0]["text"] += "\n" + text
        else:
            contents.append({"role": "user", "parts": [{"text": text}]})
            
        payload = {
            "systemInstruction": {"parts": [{"text": prompt_to_use}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.2}
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, 
                                     headers={"Content-Type": "application/json"}, method="POST")
        
        import time
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                with urllib.request.urlopen(req, timeout=10.0) as response:
                    res_body = response.read().decode("utf-8")
                    res_json = json.loads(res_body)
                break
            except urllib.error.HTTPError as e:
                error_msg = e.read().decode()
                if e.code == 503 and attempt < max_attempts - 1:
                    time.sleep(1.5)  # Wait 1.5s before retrying server spikes
                    continue
                elif e.code == 429:
                    # Rate limit hit! Seamlessly failover to local Ollama so the user sees no error
                    print("Gemini API Rate Limit Hit! Failing over to local Ollama.")
                    try:
                        fallback_res = self.parse_with_ollama(text, chat_history, is_chat)
                        fallback_res["mode"] = fallback_res.get("mode", "Ollama LLM") + " (Cloud Limit Failover)"
                        return fallback_res
                    except Exception as ollama_e:
                        raise RuntimeError(f"Google API rate limit exceeded, and local failover failed: {ollama_e}")
                
                print(f"Gemini API HTTP Error: {error_msg}")
                raise RuntimeError(f"Gemini API Error: {error_msg}")
            
        try:
            message_content = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError):
            return {
                "actions": [],
                "explanation": f"Failed to parse Gemini response. Raw JSON: {res_json}",
                "mode": "Error"
            }
            
        if is_chat:
            return {
                "actions": [],
                "explanation": message_content,
                "mode": "Gemini 1.5 Flash (Cloud)"
            }
            
        # Extract ALL JSON objects from the response
        json_blocks = self.extract_all_json_objects(message_content)
        
        if json_blocks:
            # Get the LAST valid json block
            for block in reversed(json_blocks):
                try:
                    parsed = json.loads(block)
                    if "actions" in parsed:
                        actions = parsed["actions"]
                        if not isinstance(actions, list):
                            continue
                            
                        exp = parsed.get("explanation", "")
                        if not exp:
                            exp = message_content
                            
                        # Clean explanation
                        final_explanation = self._clean_explanation(exp, json_blocks)
                        
                        return {
                            "actions": actions,
                            "explanation": final_explanation if final_explanation else "I have completed the task.",
                            "mode": "Gemini 1.5 Flash (Cloud)"
                        }
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
        
        # No valid action blocks found
        clean_text = self._clean_explanation(message_content, json_blocks)
        return {
            "actions": [],
            "explanation": clean_text if clean_text else message_content,
            "mode": "Gemini 1.5 Flash (Cloud)"
        }

    def parse_with_ollama(self, text: str, chat_history: list = None, is_chat: bool = False) -> dict:
        """Sends prompt to Ollama and extracts the LAST valid JSON action block."""
        model_name = self.get_best_model_name()
        url = f"{self.ollama_url}/api/chat"
        
        prompt_to_use = self.chat_prompt if is_chat else self.system_prompt
        messages = [{"role": "system", "content": prompt_to_use}]
        if chat_history:
            messages.extend(chat_history[-10:])
        else:
            messages.append({"role": "user", "content": text})
            
        payload = {"model": model_name, "messages": messages, "stream": False}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, 
                                     headers={"Content-Type": "application/json"}, method="POST")
        
        with urllib.request.urlopen(req, timeout=20.0) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            message_content = res_json.get("message", {}).get("content", "").strip()
            
            if is_chat:
                return {
                    "actions": [],
                    "explanation": message_content,
                    "mode": f"Ollama Chat ({model_name})"
                }
            
            # Extract ALL JSON objects from the response
            json_blocks = self.extract_all_json_objects(message_content)
            
            # Try blocks in REVERSE order — the last complete one is usually the best
            if json_blocks:
                for json_str in reversed(json_blocks):
                    try:
                        parsed = json.loads(json_str)
                        if "actions" in parsed and isinstance(parsed["actions"], list) and len(parsed["actions"]) > 0:
                            actions = parsed["actions"]
                            explanation = parsed.get("explanation", "").strip()
                            
                            # Clean ALL json blocks and noise from the text
                            clean_text = self._clean_explanation(message_content, json_blocks)
                            
                            # Use the clean text if short, otherwise prefer the JSON explanation
                            if clean_text and len(clean_text) < 200:
                                final_explanation = clean_text
                            elif explanation:
                                final_explanation = explanation
                            elif clean_text:
                                final_explanation = clean_text[:200]
                            else:
                                final_explanation = "Executing your request."
                            
                            return {
                                "actions": actions,
                                "explanation": final_explanation,
                                "mode": f"Ollama LLM ({model_name})"
                            }
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue
            
            # No valid action blocks found — treat as conversational response
            clean_text = self._clean_explanation(message_content, json_blocks)
            return {
                "actions": [],
                "explanation": clean_text if clean_text else message_content,
                "mode": f"Ollama LLM Chat ({model_name})"
            }

    def split_clauses(self, text: str) -> list:
        """Splits instructions by conjunctions and boundaries between parameters and verbs."""
        conj_pattern = r"\b(?:and\s+then|then|and|after\s+that|after\s+this|,|;)\s+(?=(?:open|launch|start|run|execute|type|write|press|screenshot|volume|read|view|cmd|shell|show|change|take|capture|increase|decrease|mute|unmute|raise|lower|close|kill|terminate|stop|exit|clear|delete)\b)"
        parts = re.split(conj_pattern, text, flags=re.IGNORECASE)
        
        final_clauses = []
        verbs = ["open", "launch", "start", "run", "execute", "type", "write", "press", "screenshot", "volume", "read", "view", "cmd", "shell", "show", "change", "take", "capture", "close", "kill", "terminate", "stop", "exit", "clear", "delete"]
        param_words = ["notepad", "chrome", "calculator", "paint", "cmd", "spotify", "discord", "it", "file", "folder", "before", "befor", "window", "screen", "app", "application", "website", "url", "text", "volume", "screenshot", "key", "button"]
        
        for part in parts:
            words = part.split()
            current_clause = []
            for i, word in enumerate(words):
                word_clean = re.sub(r"[^\w-]", "", word.lower())
                if i > 0 and word_clean in verbs:
                    prev_word_clean = re.sub(r"[^\w-]", "", words[i-1].lower())
                    if prev_word_clean in param_words:
                        if current_clause:
                            final_clauses.append(" ".join(current_clause))
                        current_clause = [word]
                        continue
                current_clause.append(word)
            if current_clause:
                final_clauses.append(" ".join(current_clause))
                
        return [c.strip() for c in final_clauses if c.strip()]

    def parse_with_rules(self, text: str) -> dict:
        """Rule-based parser supporting multi-command split chaining and pronoun resolution."""
        text_raw = text.strip()
        clauses = self.split_clauses(text_raw)
        
        actions = []
        explanations = []
        
        for clause in clauses:
            clause_clean = clause.lower().strip()
            if not clause_clean:
                continue
            
            res = self._parse_single_clause(clause, clause_clean)
            if res and res["actions"]:
                new_actions = []
                for action in res["actions"]:
                    # Anaphora resolution for pronouns in close commands (e.g. "open notepad and close it")
                    if action["type"] == "close_app":
                        target = action["details"].lower()
                        if target == "it":
                            # Search previous actions inside the same chain for any opening action
                            resolved = False
                            for prev_act in reversed(actions):
                                if prev_act["type"] in ["open_app", "open_folder", "open_url", "run_command", "read_file"]:
                                    action["details"] = prev_act["details"]
                                    if "'it'" in res["explanation"]:
                                        res["explanation"] = res["explanation"].replace("'it'", f"'{prev_act['details']}'")
                                    resolved = True
                                    break
                                elif prev_act["type"] == "open_camera":
                                    action["details"] = "camera"
                                    if "'it'" in res["explanation"]:
                                        res["explanation"] = res["explanation"].replace("'it'", "'camera'")
                                    resolved = True
                                    break
                            # If no previous context was found, we leave it as "it" and let automation.py close the Active Window
                            new_actions.append(action)
                        elif target in ["them", "both", "all"]:
                            # Find ALL things opened in this command chain
                            opened_apps = []
                            for prev_act in actions:
                                if prev_act["type"] in ["open_app", "open_folder", "open_url", "run_command", "read_file"]:
                                    opened_apps.append(str(prev_act["details"]))
                                elif prev_act["type"] == "open_camera":
                                    opened_apps.append("camera")
                            
                            if opened_apps:
                                for app in opened_apps:
                                    new_actions.append({"type": "close_app", "details": app})
                                if f"'{target}'" in res["explanation"]:
                                    res["explanation"] = res["explanation"].replace(f"'{target}'", f"'{', '.join(opened_apps)}'")
                            else:
                                new_actions.append(action)
                        else:
                            new_actions.append(action)
                    else:
                        new_actions.append(action)
                
                actions.extend(new_actions)
                explanations.append(res["explanation"])
            elif res and not res["actions"] and res["explanation"]:
                explanations.append(res["explanation"])
        
        if not actions and not explanations:
            explanation = "I didn't understand that instruction. Try asking 'help' to see my capabilities, or start Ollama to enable full conversational AI."
        elif not actions and explanations:
            explanation = "  ".join(explanations)
        else:
            explanation = " then ".join(explanations)
            
        return {
            "actions": actions,
            "explanation": explanation,
            "mode": "Local Rules (Ollama Offline)"
        }

    def _parse_single_clause(self, raw_clause: str, clause_clean: str) -> dict:
        """Wrapper method that intercepts time delay suffixes (e.g. 'after 10 seconds') and prepends wait actions."""
        # 0. Strip conversational prefixes to ensure strict anchoring
        prefix_pattern = r"^(?:please|can you|could you|would you|will you|ron|hey ron|hi ron|just|kindly|now)\s+"
        clause_clean = re.sub(prefix_pattern, "", clause_clean).strip()
        raw_clause = re.sub(prefix_pattern, "", raw_clause, flags=re.IGNORECASE).strip()
        
        # 1. Scan for delay suffixes (now supporting decimals and proper units)
        delay_match = re.search(r"\b(?:after|in|for)\s+([0-9.]+)\s*(seconds|sec|s|m|min|minutes|minute|h|hr|hours|hour)?\s*(?:of\s+\w+(?:\s+\w+)*)?\b", clause_clean)
        delay_seconds = 0.0
        if delay_match:
            try:
                base_val = float(delay_match.group(1))
                unit = delay_match.group(2)
                if unit:
                    unit = unit.lower()
                    if unit in ["m", "min", "minutes", "minute"]:
                        base_val *= 60
                    elif unit in ["h", "hr", "hours", "hour"]:
                        base_val *= 3600
                delay_seconds = base_val
                
                # Strip the suffix from rule clean strings (including trailing noise like "of doing this")
                clause_clean = clause_clean.replace(delay_match.group(0), "").strip()
                raw_clause = re.sub(r"\b(?:after|in|for)\s+[0-9.]+\s*(?:seconds|sec|s|m|min|minutes|minute|h|hr|hours|hour)?\s*(?:of\s+\w+(?:\s+\w+)*)?\b", "", raw_clause, flags=re.IGNORECASE).strip()
            except Exception:
                pass

        # 2. Call core parser
        res = self._parse_single_clause_inner(raw_clause, clause_clean)

        # 3. Prepend wait action if delay exists
        if delay_seconds > 0 and res and res["actions"]:
            res["actions"].insert(0, {"type": "wait", "details": str(delay_seconds)})
            if res["explanation"]:
                res["explanation"] = f"wait for {delay_seconds} seconds then " + res["explanation"]
                
        return res

    def _parse_single_clause_inner(self, raw_clause: str, clause_clean: str) -> dict:
        """Core parsing logic matching single actions."""
        actions = []
        explanation = ""

        # A. Conversational Greetings
        if any(keyword == clause_clean for keyword in ["hi", "hello", "hey", "whats up", "what's up", "yo"]):
            explanation = "Hi there! I am Ron, your local system assistant. How can I help you automate your computer today?"
            return {"actions": [], "explanation": explanation}
        elif "how are you" in clause_clean or "how's it going" in clause_clean:
            explanation = "I'm doing great, thank you! Operating fully locally, offline, and ready for your automation commands."
            return {"actions": [], "explanation": explanation}

        # B. Clock / Time System Queries
        elif any(k in clause_clean for k in ["what time is it", "what is the time", "show time", "current time", "what date is it", "what is the date", "show date", "current date"]) or clause_clean in ["time", "date"]:
            import datetime
            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d, %Y")
            explanation = f"The current system time is {time_str} and the date is {date_str}."
            return {"actions": [], "explanation": explanation}

        # C. Help Menu
        elif clause_clean in ["help", "what can you do", "commands", "features"]:
            explanation = (
                "Here are some of the things I can do:\n\n"
                "1. Apps: 'open notepad', 'open chrome', 'open gta 5', 'launch spotify'\n"
                "2. Camera: 'open camera', 'take a photo'\n"
                "3. Web: 'search python variables', 'open google.com'\n"
                "4. Automation: 'type [text]', 'press enter', 'screenshot'\n"
                "5. System: 'volume up', 'volume down', 'mute', 'time', 'date'\n"
                "6. Terminal: 'run command ipconfig'\n"
                "7. Files: 'read file C:\\test.txt', 'write hello to file C:\\test.txt'\n\n"
                "I can open ANY installed app on your PC — games, browsers, tools, you name it!\n"
                "You can chain instructions, like: 'open notepad and type a paragraph about you then close notepad'!"
            )
            return {"actions": [], "explanation": explanation}

        # D. Who Are You / Introduction
        elif clause_clean in ["who are you", "what is your name", "introduce yourself", "about yourself"]:
            explanation = "Hello! I am Ron, your local system agent. I live directly on your computer to help you automate tasks safely and completely offline."
            return {"actions": [], "explanation": explanation}

        # System Information / Settings Query Rule
        sys_info_phrases = ["system info", "systeminfo", "system information", "system settings", "settings info", "my system specs", "pc specs", "laptop specs", "system specs", "about my pc", "about my computer", "find my system info", "about pc", "about system", "pc info", "computer info"]
        if any(phrase in clause_clean for phrase in sys_info_phrases):
            actions.append({"type": "open_app", "details": "systeminfo"})
            explanation = "opening System Information for you."
            return {"actions": actions, "explanation": explanation}

        # Settings Panel Launch
        if "open settings" in clause_clean or "launch settings" in clause_clean or clause_clean == "settings":
            actions.append({"type": "open_app", "details": "settings"})
            explanation = "opening Settings for you."
            return {"actions": actions, "explanation": explanation}

        # Camera Launch
        camera_phrases = ["open camera", "launch camera", "start camera", "open webcam", "launch webcam",
                          "take a photo", "take photo", "take a selfie", "selfie", "open my camera"]
        if any(clause_clean.startswith(phrase) for phrase in camera_phrases):
            actions.append({"type": "open_camera", "details": ""})
            explanation = "opening the Camera for you."
            return {"actions": actions, "explanation": explanation}

        # 1. Clear/Delete Text Rule (Selects all via ctrl+a, and deletes via backspace)
        clear_phrases = [
            "clear all text", "clear text", "delete all text", "delete text", 
            "delete everything", "clear everything", "clear all the text", 
            "clear all text written before", "delete all text written before",
            "delete any text that is written before", "delete any text",
            "clear the text", "clear the text written before", 
            "delete text that is written before", "clear text that is written before",
            "delete anything that is written in there before", "delete anything written in there before",
            "delete anything written before", "clear anything written before"
        ]
        if any(clause_clean.startswith(phrase) for phrase in clear_phrases):
            actions.append({"type": "press_key", "details": "ctrl+a"})
            actions.append({"type": "press_key", "details": "backspace"})
            explanation = "clear all text"
            return {"actions": actions, "explanation": explanation}

        # 2. File Writing Pattern
        write_match1 = re.search(r"^(?:write file|write to file|create file)\s+(\S+)\s+(?:with\s+)?content\s+(.+)\b", raw_clause, re.IGNORECASE)
        write_match2 = re.search(r"^(?:write|create)\s+(.+)\s+to\s+file\s+(\S+)\b", raw_clause, re.IGNORECASE)
        
        if write_match1:
            filepath = write_match1.group(1).strip()
            content = write_match1.group(2).strip()
            if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                content = content[1:-1]
            actions.append({"type": "write_file", "details": filepath, "content": content})
            explanation = f"write content to '{filepath}'"
            return {"actions": actions, "explanation": explanation}
            
        elif write_match2:
            content = write_match2.group(1).strip()
            filepath = write_match2.group(2).strip()
            if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                content = content[1:-1]
            actions.append({"type": "write_file", "details": filepath, "content": content})
            explanation = f"write content to '{filepath}'"
            return {"actions": actions, "explanation": explanation}

        # 3. File Reading Pattern
        elif re.search(r"^(?:read file|read|view file)\s+(\S+)\b", clause_clean):
            read_match = re.search(r"^(?:read file|read|view file)\s+(\S+)\b", raw_clause, re.IGNORECASE)
            filepath = read_match.group(1).strip()
            if filepath.lower() not in ["notepad", "calculator", "chrome", "cmd", "explorer", "paint", "taskmgr", "folder", "directory"]:
                actions.append({"type": "read_file", "details": filepath})
                explanation = f"read file '{filepath}'"
                return {"actions": actions, "explanation": explanation}

        # 4. Open Folder Pattern
        folder_match = re.search(r"^(?:open|show)\s+(?:folder|directory|path)\s+(.+)\b", raw_clause, re.IGNORECASE)
        if folder_match:
            folder_path = folder_match.group(1).strip()
            actions.append({"type": "open_folder", "details": folder_path})
            explanation = f"open folder '{folder_path}'"
            return {"actions": actions, "explanation": explanation}

        # 5. Open URL / Web Search Pattern
        url_match = re.search(r"^(?:open|go to|browse)\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}\S*)\b", clause_clean)
        search_match = re.search(r"^(?:search|search for|google)\s+(.+)\b", clause_clean)
        if url_match:
            url = url_match.group(1)
            actions.append({"type": "open_url", "details": url})
            explanation = f"open URL '{url}'"
            return {"actions": actions, "explanation": explanation}
        elif search_match:
            search_query = search_match.group(1).strip()
            search_query = re.sub(r"\bon (google|chrome|browser)\b", "", search_query).strip()
            search_url = f"google.com/search?q={urllib.parse.quote_plus(search_query)}"
            actions.append({"type": "open_url", "details": search_url})
            explanation = f"search Google for '{search_query}'"
            return {"actions": actions, "explanation": explanation}

        # 6. Execute Command Pattern
        cmd_match = re.search(r"^(?:run command|execute command|run in cmd|run in terminal|terminal|execute|cmd|shell)\s+(.+)\b", raw_clause, re.IGNORECASE)
        if cmd_match:
            cmd = cmd_match.group(1).strip()
            is_common_app = any(app in cmd.lower() for app in ["notepad", "calculator", "chrome", "paint", "taskmgr"])
            if not is_common_app or len(cmd.split()) > 1:
                actions.append({"type": "run_command", "details": cmd})
                explanation = f"run command '{cmd}'"
                return {"actions": actions, "explanation": explanation}

        # 7. Close App Pattern (supports multi-word app names)
        close_match = re.search(r"^(?:close|kill|terminate|stop|exit)\s+(?:the\s+)?(.+?)\s*$", clause_clean)
        if close_match:
            app_name = close_match.group(1).strip()
            if app_name not in ["folder", "directory", "path", "file", "url", "website", "command", "cmd", "shell"]:
                raw_close_match = re.search(r"^(?:close|kill|terminate|stop|exit)\s+(?:the\s+)?(.+?)\s*$", raw_clause, re.IGNORECASE)
                raw_app_name = raw_close_match.group(1).strip() if raw_close_match else app_name
                raw_app_names = re.split(r",|\band\b", raw_app_name, flags=re.IGNORECASE)
                added_apps = []
                for name in raw_app_names:
                    name = name.strip()
                    if name:
                        actions.append({"type": "close_app", "details": name})
                        added_apps.append(name)
                explanation = f"close application(s) '{', '.join(added_apps)}'"
                return {"actions": actions, "explanation": explanation}

        # 8. Open Generic App Pattern (supports multi-word app names like 'gta 5', 'visual studio code')
        app_match = re.search(r"^(?:open|launch|start|run)\s+(?:the\s+)?(.+?)\s*$", clause_clean)
        if app_match:
            app_name = app_match.group(1).strip()
            if app_name not in ["folder", "directory", "path", "file", "url", "website", "command", "cmd", "shell"]:
                raw_app_match = re.search(r"^(?:open|launch|start|run)\s+(?:the\s+)?(.+?)\s*$", raw_clause, re.IGNORECASE)
                raw_app_name = raw_app_match.group(1).strip() if raw_app_match else app_name
                raw_app_names = re.split(r",|\band\b", raw_app_name, flags=re.IGNORECASE)
                added_apps = []
                for name in raw_app_names:
                    name = name.strip()
                    if name:
                        actions.append({"type": "open_app", "details": name})
                        added_apps.append(name)
                explanation = f"open application(s) '{', '.join(added_apps)}'"
                return {"actions": actions, "explanation": explanation}

        # 9. Type Text Pattern
        type_match = re.search(r"^(?:type|type out|write down)\s+(.+)\b", raw_clause, re.IGNORECASE)
        if type_match:
            to_type = type_match.group(1).strip()
            if (to_type.startswith('"') and to_type.endswith('"')) or (to_type.startswith("'") and to_type.endswith("'")):
                to_type = to_type[1:-1]
            
            # Smart conversational substitutions
            to_type_lower = to_type.lower()
            if any(phrase in to_type_lower for phrase in ["para about you", "para about yourself", "paragraph about you", "paragraph about yourself"]):
                to_type = (
                    "Hello! I am Ron, your autonomous local AI system assistant. "
                    "I reside directly on your computer to assist with opening applications, writing files, "
                    "reading code, running shell scripts, and automating mouse/keyboard controls. "
                    "I run completely locally and offline to keep your system safe and your data private."
                )
            elif any(phrase in to_type_lower for phrase in ["who are you", "introduce yourself", "about yourself", "about you"]):
                to_type = "I am Ron, your autonomous local AI assistant. I run offline to perform system automation."
            elif any(phrase in to_type_lower for phrase in ["alphabets", "alphabet", "the alphabets", "the whole alphabet"]):
                # Determine capitalization
                if "block" in to_type_lower or "uppercase" in to_type_lower or "capital" in to_type_lower:
                    to_type = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                else:
                    to_type = "abcdefghijklmnopqrstuvwxyz"
            else:
                # Strip trailing prepositional references: "in it", "into the notepad", etc.
                to_type_clean = re.sub(r"\b(?:in|into|in\s+the|into\s+the)\s+(?:it|notepad|calculator|chrome|editor|app|application)\b$", "", to_type, flags=re.IGNORECASE).strip()
                if (to_type_clean.startswith('"') and to_type_clean.endswith('"')) or (to_type_clean.startswith("'") and to_type_clean.endswith("'")):
                    to_type_clean = to_type_clean[1:-1]
                to_type = to_type_clean
                
            actions.append({"type": "type_text", "details": to_type})
            explanation = f"type '{to_type[:30]}'"
            return {"actions": actions, "explanation": explanation}

        # 10. Volume Change Pattern
        if any(clause_clean.startswith(v) for v in ["volume up", "increase volume", "increase the volume", "raise volume", "raise the volume", "volume increase"]):
            actions.append({"type": "change_volume", "details": "up"})
            explanation = "increase volume"
            return {"actions": actions, "explanation": explanation}
        elif any(clause_clean.startswith(v) for v in ["volume down", "decrease volume", "decrease the volume", "lower volume", "lower the volume", "volume decrease"]):
            actions.append({"type": "change_volume", "details": "down"})
            explanation = "decrease volume"
            return {"actions": actions, "explanation": explanation}
        elif any(clause_clean.startswith(v) for v in ["mute", "unmute"]):
            actions.append({"type": "change_volume", "details": "mute"})
            explanation = "toggle volume mute"
            return {"actions": actions, "explanation": explanation}

        # 11. Screenshot Pattern
        if clause_clean.startswith("screenshot") or clause_clean.startswith("take a screenshot") or clause_clean.startswith("capture screen"):
            actions.append({"type": "take_screenshot", "details": ""})
            explanation = "capture screenshot"
            return {"actions": actions, "explanation": explanation}

        # 12. Press Key Pattern
        key_match = re.search(r"^press\s+(enter|tab|backspace|space|esc|escape|ctrl\+[a-z]|alt\+[a-z]|win\+[a-z])\b", clause_clean)
        if key_match:
            key_name = key_match.group(1)
            actions.append({"type": "press_key", "details": key_name})
            explanation = f"press key '{key_name}'"
            return {"actions": actions, "explanation": explanation}

        return {"actions": [], "explanation": ""}
