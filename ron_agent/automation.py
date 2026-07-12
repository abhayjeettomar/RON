import os
import subprocess
import webbrowser
import time
import pyautogui

# Set PyAutoGUI fail-safe: move mouse to any corner of the screen to abort automation
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15 # Pause between actions to allow OS to render

def find_and_open_app_shortcut(app_name: str) -> bool:
    """Searches Windows Start Menu paths for a matching .lnk shortcut and runs it."""
    program_data = os.environ.get("ProgramData", "C:\\ProgramData")
    app_data = os.environ.get("AppData", os.path.expandvars("%USERPROFILE%\\AppData\\Roaming"))
    
    start_menu_paths = [
        os.path.join(program_data, "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(app_data, "Microsoft\\Windows\\Start Menu\\Programs")
    ]
    
    target = app_name.lower().strip()
    
    for folder in start_menu_paths:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(".lnk"):
                    shortcut_name = file[:-4].lower()
                    if target == shortcut_name or target in shortcut_name:
                        filepath = os.path.join(root, file)
                        try:
                            os.startfile(filepath)
                            return True
                        except Exception:
                            pass
    return False

def open_app(app_name: str) -> str:
    """Launches a common application or searches Start Menu shortcuts to open it."""
    name_clean = app_name.strip()
    name_clean_lower = name_clean.lower()
    
    # 1. Hardcoded mapping first (handles system settings and msinfo32)
    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "chrome": "chrome.exe",
        "cmd": "cmd.exe",
        "explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "taskmgr": "taskmgr.exe",
        "settings": "ms-settings:",
        "about": "ms-settings:about",
        "systeminfo": "msinfo32.exe",
        "system info": "msinfo32.exe",
        "system information": "msinfo32.exe"
    }
    
    if name_clean_lower in app_map:
        exec_name = app_map[name_clean_lower]
        try:
            os.startfile(exec_name)
            time.sleep(1.2)
            return f"Successfully launched application: {exec_name}"
        except Exception as e:
            try:
                subprocess.Popen(exec_name, shell=True)
                time.sleep(1.2)
                return f"Successfully opened: {exec_name}"
            except Exception as ex:
                return f"Failed to open '{app_name}'. Error: {str(ex)}"
                
    # 2. Try Windows Start Menu Shortcuts (handles Spotify, Steam, Discord, Chrome, etc.)
    try:
        if find_and_open_app_shortcut(name_clean):
            time.sleep(1.2)
            return f"Successfully launched '{name_clean}' from Start Menu shortcuts."
    except Exception:
        pass
        
    # 3. Last fallback: try startfile with raw input name
    try:
        os.startfile(name_clean)
        time.sleep(1.2)
        return f"Successfully launched application: {name_clean}"
    except Exception as e:
        try:
            subprocess.Popen(name_clean, shell=False)
            time.sleep(1.2)
            return f"Successfully opened: {name_clean}"
        except Exception as ex:
            return f"Failed to open '{app_name}'. Error: {str(ex)}"

def close_app(app_name: str) -> str:
    """Closes an application by killing its system processes."""
    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "chrome": "chrome.exe",
        "cmd": "cmd.exe",
        "explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "taskmgr": "taskmgr.exe",
        "spotify": "spotify.exe",
        "discord": "discord.exe"
    }
    name_clean = app_name.lower().strip()
    exec_name = app_map.get(name_clean, name_clean)
    
    if not exec_name.endswith(".exe"):
        exec_name += ".exe"
        
    try:
        # Run taskkill forcefully
        res = subprocess.run(
            f"taskkill /f /im {exec_name}",
            shell=True,
            capture_output=True,
            text=True
        )
        if res.returncode == 0:
            return f"Successfully closed application: {exec_name}"
        else:
            # Check if it was already closed or not found
            if "not found" in res.stderr.lower():
                return f"Application '{app_name}' ({exec_name}) is not currently running."
            return f"Failed to close '{app_name}'. Error: {res.stderr.strip()}"
    except Exception as e:
        return f"Failed to close '{app_name}'. Error: {str(e)}"

def open_url(url: str) -> str:
    """Opens a website in the default browser."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"Opened URL: {url}"
    except Exception as e:
        return f"Failed to open URL '{url}'. Error: {str(e)}"

def open_folder(path: str) -> str:
    """Opens a local file folder in File Explorer."""
    path = os.path.expandvars(path)
    if not os.path.exists(path):
        return f"Folder or path does not exist: {path}"
    try:
        os.startfile(path)
        return f"Opened folder: {path}"
    except Exception as e:
        return f"Failed to open folder '{path}'. Error: {str(e)}"

def _clipboard_set_native(text: str):
    """Sets the Windows clipboard using the native clip.exe command (always works, no Python deps)."""
    process = subprocess.Popen(
        ["clip"],
        stdin=subprocess.PIPE,
        shell=True
    )
    process.communicate(input=text.encode("utf-16-le"))

def _clipboard_get_native() -> str:
    """Gets the Windows clipboard text using PowerShell (always works, no Python deps)."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=3.0
        )
        return result.stdout.rstrip("\r\n")
    except Exception:
        return ""

def type_text(text: str) -> str:
    """Types text by copying to clipboard via Windows clip.exe and pasting with ctrl+v.
    
    This approach:
    - Uses Windows-native clip.exe (always works, no Python clipboard library conflicts)
    - Supports multiline text, special characters, and Unicode
    - Is instant (no character-by-character typing delays)
    - Avoids conflicts with the running CTk/Tk mainloop
    """
    try:
        # 1. Save current clipboard
        old_clipboard = _clipboard_get_native()
        
        # 2. Copy our text to clipboard using native clip.exe
        _clipboard_set_native(text)
        time.sleep(0.15)
        
        # 3. Paste with ctrl+v
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.15)
        
        # 4. Restore old clipboard
        if old_clipboard:
            _clipboard_set_native(old_clipboard)
        
        return f"Typed text successfully: '{text[:40]}...'" if len(text) > 40 else f"Typed text successfully: '{text}'"
    except Exception as e:
        # Fallback: character-by-character typing (slow but reliable for ASCII)
        try:
            time.sleep(0.5)
            pyautogui.write(text, interval=0.02)
            return f"Typed text (fallback): '{text[:40]}...'"
        except Exception as e2:
            return f"Failed to type text. Error: {str(e2)}"

def press_key(key: str) -> str:
    """Simulates pressing a keyboard key or combination (e.g., 'enter', 'tab', 'ctrl', 'c')."""
    try:
        parts = [p.strip().lower() for p in key.split("+")]
        if len(parts) > 1:
            pyautogui.hotkey(*parts)
            return f"Pressed key combination: {'+'.join(parts)}"
        else:
            pyautogui.press(parts[0])
            return f"Pressed key: {parts[0]}"
    except Exception as e:
        return f"Failed to press key '{key}'. Error: {str(e)}"

def take_screenshot(output_dir: str = ".") -> str:
    """Takes a full screenshot and saves it with a timestamped name."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"screenshot_{int(time.time())}.png"
        filepath = os.path.join(output_dir, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return f"Screenshot saved successfully at: {os.path.abspath(filepath)}"
    except Exception as e:
        return f"Failed to capture screenshot. Error: {str(e)}"

def change_volume(action: str) -> str:
    """Controls the system volume. Action can be 'up', 'down', or 'mute'."""
    action = action.lower().strip()
    try:
        if action == "up":
            pyautogui.press("volumeup")
            return "Volume increased"
        elif action == "down":
            pyautogui.press("volumedown")
            return "Volume decreased"
        elif action == "mute":
            pyautogui.press("volumemute")
            return "Volume toggled/muted"
        else:
            return f"Unknown volume action: {action}"
    except Exception as e:
        return f"Failed to change volume. Error: {str(e)}"

def run_command(cmd_string: str) -> str:
    """Executes a command prompt instruction and returns stdout/stderr output."""
    try:
        res = subprocess.run(
            cmd_string,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15.0
        )
        output = ""
        if res.stdout:
            output += res.stdout
        if res.stderr:
            output += f"\nErrors:\n{res.stderr}"
        if not output.strip():
            output = f"Command finished with exit code: {res.returncode} (No output)."
        return output
    except Exception as e:
        return f"Failed to execute command. Error: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Creates a local file and writes the specified content."""
    try:
        filepath = os.path.expandvars(filepath)
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to file: {os.path.abspath(filepath)}"
    except Exception as e:
        return f"Failed to write file. Error: {str(e)}"

def read_file(filepath: str) -> str:
    """Reads a local file's text content (first 5000 characters)."""
    try:
        filepath = os.path.expandvars(filepath)
        if not os.path.exists(filepath):
            return f"Error: File does not exist: {filepath}"
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(5000)
        return f"Content of {filepath}:\n---\n{content}\n---"
    except Exception as e:
        return f"Failed to read file. Error: {str(e)}"
