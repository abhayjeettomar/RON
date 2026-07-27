import os
import subprocess
import webbrowser
import time
import pyautogui

# Set PyAutoGUI fail-safe: move mouse to any corner of the screen to abort automation
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15 # Pause between actions to allow OS to render


# ── Expanded App Map ──────────────────────────────────────────────
# Maps common names / aliases to executable names or URI protocols
APP_MAP = {
    # System utilities
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "paint": "mspaint.exe",
    "ms paint": "mspaint.exe",
    "taskmgr": "taskmgr.exe",
    "task manager": "taskmgr.exe",
    "settings": "ms-settings:",
    "about": "ms-settings:about",
    "systeminfo": "msinfo32.exe",
    "system info": "msinfo32.exe",
    "system information": "msinfo32.exe",
    "snipping tool": "snippingtool.exe",
    "snip": "snippingtool.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "powershell": "powershell.exe",
    "control panel": "control.exe",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "registry editor": "regedit.exe",
    "regedit": "regedit.exe",
    "wordpad": "wordpad.exe",
    "character map": "charmap.exe",
    "magnifier": "magnify.exe",
    "narrator": "narrator.exe",
    "on screen keyboard": "osk.exe",
    "remote desktop": "mstsc.exe",
    "resource monitor": "resmon.exe",
    "event viewer": "eventvwr.msc",
    "services": "services.msc",
    "msconfig": "msconfig.exe",
    "defragment": "dfrgui.exe",
    "disk cleanup": "cleanmgr.exe",

    # Camera
    "camera": "microsoft.windows.camera:",
    "webcam": "microsoft.windows.camera:",

    # Browsers
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "mozilla firefox": "firefox.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "brave": "brave.exe",
    "opera": "opera.exe",
    "vivaldi": "vivaldi.exe",

    # Communication
    "discord": "discord.exe",
    "telegram": "telegram.exe",
    "whatsapp": "whatsapp.exe",
    "slack": "slack.exe",
    "zoom": "zoom.exe",
    "teams": "ms-teams.exe",
    "microsoft teams": "ms-teams.exe",
    "skype": "skype.exe",

    # Media
    "spotify": "spotify.exe",
    "vlc": "vlc.exe",
    "vlc media player": "vlc.exe",
    "itunes": "itunes.exe",
    "foobar": "foobar2000.exe",
    "windows media player": "wmplayer.exe",
    "media player": "wmplayer.exe",
    "photos": "ms-photos:",

    # Productivity / Office
    "word": "winword.exe",
    "microsoft word": "winword.exe",
    "excel": "excel.exe",
    "microsoft excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "microsoft powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "microsoft outlook": "outlook.exe",
    "onenote": "onenote.exe",
    "access": "msaccess.exe",

    # Dev tools
    "vscode": "code.exe",
    "vs code": "code.exe",
    "visual studio code": "code.exe",
    "visual studio": "devenv.exe",
    "pycharm": "pycharm64.exe",
    "intellij": "idea64.exe",
    "android studio": "studio64.exe",
    "sublime text": "sublime_text.exe",
    "sublime": "sublime_text.exe",
    "atom": "atom.exe",
    "notepad++": "notepad++.exe",
    "git bash": "git-bash.exe",
    "postman": "postman.exe",

    # Gaming
    "steam": "steam.exe",
    "epic games": "epicgameslauncher.exe",
    "epic": "epicgameslauncher.exe",
    "origin": "origin.exe",
    "battle.net": "battle.net.exe",
    "battlenet": "battle.net.exe",
    "ubisoft connect": "upc.exe",
    "uplay": "upc.exe",
    "gog galaxy": "goggalaxy.exe",
    "riot client": "riotclientservices.exe",
    "valorant": "riotclientservices.exe",

    # Utilities
    "obs": "obs64.exe",
    "obs studio": "obs64.exe",
    "7zip": "7zfm.exe",
    "winrar": "winrar.exe",
    "everything": "everything.exe",
    "ccleaner": "ccleaner.exe",
    "malwarebytes": "mbam.exe",
    "bluestacks": "bluestacks.exe",
    "handbrake": "handbrake.exe",
    "audacity": "audacity.exe",
    "gimp": "gimp.exe",
    "obs": "obs64.exe",
    "qbittorrent": "qbittorrent.exe",
    "utorrent": "utorrent.exe",

    # Design
    "photoshop": "photoshop.exe",
    "illustrator": "illustrator.exe",
    "premiere": "premiere pro.exe",
    "after effects": "afterfx.exe",
    "figma": "figma.exe",
    "canva": "canva.exe",
    "blender": "blender.exe",
}

# ── Fuzzy Alias Map ───────────────────────────────────────────────
# Maps common misspellings, abbreviations, and variations to canonical names
FUZZY_ALIASES = {
    "gta v": "grand theft auto v",
    "gta 5": "grand theft auto v",
    "gta5": "grand theft auto v",
    "gtav": "grand theft auto v",
    "grand theft auto 5": "grand theft auto v",
    "pubg": "pubg",
    "fortnite": "fortnite",
    "minecraft": "minecraft",
    "roblox": "roblox",
    "apex legends": "apex legends",
    "apex": "apex legends",
    "cod": "call of duty",
    "call of duty": "call of duty",
    "warzone": "call of duty warzone",
    "league of legends": "league of legends",
    "lol": "league of legends",
    "csgo": "counter-strike",
    "cs2": "counter-strike 2",
    "counter strike": "counter-strike",
    "dota": "dota 2",
    "dota2": "dota 2",
    "overwatch": "overwatch",
    "ow2": "overwatch 2",
    "rocket league": "rocket league",
    "rl": "rocket league",
    "elden ring": "elden ring",
    "cyberpunk": "cyberpunk 2077",
    "rdr2": "red dead redemption 2",
    "red dead": "red dead redemption 2",
    "witcher": "the witcher 3",
    "witcher 3": "the witcher 3",
    "hogwarts legacy": "hogwarts legacy",
    "starfield": "starfield",
    "baldurs gate": "baldur's gate 3",
    "baldur's gate": "baldur's gate 3",
    "bg3": "baldur's gate 3",
    "wpp": "whatsapp",
    "wp": "whatsapp",
    "insta": "instagram",
    "tg": "telegram",
    "yt": "youtube",
    "vsc": "visual studio code",
    "notepad plus": "notepad++",
    "notepad plus plus": "notepad++",
    "npp": "notepad++",
    "ff": "firefox",
    "gc": "google chrome",
}


def _simple_similarity(s1: str, s2: str) -> float:
    """Simple character-level similarity ratio (no external deps). Returns 0.0 to 1.0."""
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    if s1 in s2 or s2 in s1:
        return len(min(s1, s2, key=len)) / len(max(s1, s2, key=len))
    # Simple bigram overlap ratio
    def bigrams(s):
        return set(s[i:i+2] for i in range(len(s)-1))
    b1, b2 = bigrams(s1), bigrams(s2)
    if not b1 or not b2:
        return 0.0
    return 2.0 * len(b1 & b2) / (len(b1) + len(b2))


def find_and_open_app_shortcut(app_name: str, fuzzy: bool = True) -> bool:
    """Searches Windows Start Menu paths for a matching .lnk shortcut and runs it.
    If fuzzy=True, uses substring and similarity matching for more flexible results.
    """
    program_data = os.environ.get("ProgramData", "C:\\ProgramData")
    app_data = os.environ.get("AppData", os.path.expandvars("%USERPROFILE%\\AppData\\Roaming"))
    
    start_menu_paths = [
        os.path.join(program_data, "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(app_data, "Microsoft\\Windows\\Start Menu\\Programs")
    ]
    
    target = app_name.lower().strip()
    
    # First pass: exact and substring match (original behavior)
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
    
    # Second pass (fuzzy): similarity-based matching
    if fuzzy:
        best_match = None
        best_score = 0.0
        
        for folder in start_menu_paths:
            if not os.path.exists(folder):
                continue
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        shortcut_name = file[:-4].lower()
                        score = _simple_similarity(target, shortcut_name)
                        if score > best_score and score >= 0.55:
                            best_score = score
                            best_match = os.path.join(root, file)
        
        if best_match:
            try:
                os.startfile(best_match)
                return True
            except Exception:
                pass
    
    return False


def _find_app_in_registry(app_name: str) -> str:
    """Searches Windows Registry for an app executable path.
    Checks App Paths and Uninstall entries.
    Returns the executable path if found, else empty string.
    """
    try:
        import winreg
    except ImportError:
        return ""
    
    target = app_name.lower().strip()
    
    # 1. Check App Paths (HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths)
    try:
        app_paths_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
        )
        try:
            i = 0
            while True:
                subkey_name = winreg.EnumKey(app_paths_key, i)
                exe_name = subkey_name.lower().replace(".exe", "")
                if target == exe_name or target in exe_name or _simple_similarity(target, exe_name) >= 0.65:
                    try:
                        subkey = winreg.OpenKey(app_paths_key, subkey_name)
                        exe_path, _ = winreg.QueryValueEx(subkey, "")
                        winreg.CloseKey(subkey)
                        if exe_path and os.path.exists(exe_path.strip('"')):
                            winreg.CloseKey(app_paths_key)
                            return exe_path.strip('"')
                    except Exception:
                        pass
                i += 1
        except OSError:
            pass
        winreg.CloseKey(app_paths_key)
    except Exception:
        pass
    
    # 2. Check Uninstall entries for DisplayName matches
    uninstall_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    
    for uninstall_path in uninstall_paths:
        try:
            uninstall_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_path)
            try:
                i = 0
                while True:
                    subkey_name = winreg.EnumKey(uninstall_key, i)
                    try:
                        subkey = winreg.OpenKey(uninstall_key, subkey_name)
                        try:
                            display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                            display_name_lower = display_name.lower()
                            if target in display_name_lower or _simple_similarity(target, display_name_lower) >= 0.6:
                                # Try to get InstallLocation or DisplayIcon for exe path
                                try:
                                    install_loc, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                                    if install_loc and os.path.isdir(install_loc):
                                        # Search for .exe files in the install directory
                                        for f in os.listdir(install_loc):
                                            if f.lower().endswith(".exe"):
                                                exe_path = os.path.join(install_loc, f)
                                                if os.path.exists(exe_path):
                                                    winreg.CloseKey(subkey)
                                                    winreg.CloseKey(uninstall_key)
                                                    return exe_path
                                except Exception:
                                    pass
                                try:
                                    display_icon, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
                                    icon_path = display_icon.split(",")[0].strip('"')
                                    if icon_path.lower().endswith(".exe") and os.path.exists(icon_path):
                                        winreg.CloseKey(subkey)
                                        winreg.CloseKey(uninstall_key)
                                        return icon_path
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        winreg.CloseKey(subkey)
                    except Exception:
                        pass
                    i += 1
            except OSError:
                pass
            winreg.CloseKey(uninstall_key)
        except Exception:
            pass
    
    # 3. Also check current user uninstall
    try:
        user_uninstall = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        )
        try:
            i = 0
            while True:
                subkey_name = winreg.EnumKey(user_uninstall, i)
                try:
                    subkey = winreg.OpenKey(user_uninstall, subkey_name)
                    try:
                        display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        if target in display_name.lower() or _simple_similarity(target, display_name.lower()) >= 0.6:
                            try:
                                install_loc, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                                if install_loc and os.path.isdir(install_loc):
                                    for f in os.listdir(install_loc):
                                        if f.lower().endswith(".exe"):
                                            exe_path = os.path.join(install_loc, f)
                                            if os.path.exists(exe_path):
                                                winreg.CloseKey(subkey)
                                                winreg.CloseKey(user_uninstall)
                                                return exe_path
                            except Exception:
                                pass
                            try:
                                display_icon, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
                                icon_path = display_icon.split(",")[0].strip('"')
                                if icon_path.lower().endswith(".exe") and os.path.exists(icon_path):
                                    winreg.CloseKey(subkey)
                                    winreg.CloseKey(user_uninstall)
                                    return icon_path
                            except Exception:
                                pass
                    except Exception:
                        pass
                    winreg.CloseKey(subkey)
                except Exception:
                    pass
                i += 1
        except OSError:
            pass
        winreg.CloseKey(user_uninstall)
    except Exception:
        pass
    
    return ""


def _find_exe_in_path(app_name: str) -> str:
    """Searches PATH directories for a matching .exe file."""
    target = app_name.lower().strip()
    if not target.endswith(".exe"):
        target_exe = target + ".exe"
    else:
        target_exe = target
    
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for d in path_dirs:
        if not os.path.isdir(d):
            continue
        try:
            for f in os.listdir(d):
                if f.lower() == target_exe:
                    return os.path.join(d, f)
                # Fuzzy match on exe name
                fname = f.lower().replace(".exe", "")
                if _simple_similarity(target.replace(".exe", ""), fname) >= 0.7:
                    if f.lower().endswith(".exe"):
                        return os.path.join(d, f)
        except PermissionError:
            continue
    return ""


def _scan_desktop_shortcuts(app_name: str) -> bool:
    """Searches Desktop for .lnk shortcuts matching the app name."""
    target = app_name.lower().strip()
    desktop_paths = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop")
    ]
    for desktop in desktop_paths:
        if not os.path.isdir(desktop):
            continue
        try:
            for f in os.listdir(desktop):
                if f.lower().endswith(".lnk"):
                    name = f[:-4].lower()
                    if target in name or name in target or _simple_similarity(target, name) >= 0.55:
                        try:
                            os.startfile(os.path.join(desktop, f))
                            return True
                        except Exception:
                            pass
        except Exception:
            pass
    return False


def _find_exe_deep_scan(app_name: str, max_depth: int = 4, time_limit: float = 8.0) -> str:
    """Deep filesystem scan for an executable matching the app name.
    Searches all drives: Program Files, Games folders, user directories.
    Uses depth-limited os.walk and a time limit to avoid hanging.
    Returns the path to the best matching .exe, or empty string.
    """
    import string
    target = app_name.lower().strip()
    start_time = time.time()
    
    # Build list of directories to scan, prioritized
    scan_dirs = []
    
    # 1. Program Files on all drives
    # 2. Common game directories on all drives
    # 3. User home directories
    
    # Get all available drive letters
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    
    for drive in drives:
        # Program Files (highest priority)
        for pf in ["Program Files", "Program Files (x86)"]:
            pf_path = os.path.join(drive, pf)
            if os.path.isdir(pf_path):
                scan_dirs.append(pf_path)
        # Common game directories
        for gdir in ["Games", "Game", "SteamLibrary", "Epic Games", "GOG Games",
                     "Riot Games", "Origin Games", "Ubisoft Game Launcher"]:
            gpath = os.path.join(drive, gdir)
            if os.path.isdir(gpath):
                scan_dirs.append(gpath)
    
    # User home
    home = os.path.expanduser("~")
    for subdir in ["Desktop", "Downloads", "AppData\\Local", "AppData\\Roaming"]:
        spath = os.path.join(home, subdir)
        if os.path.isdir(spath):
            scan_dirs.append(spath)
    
    # Also scan drive roots (shallow, depth 2 only)
    for drive in drives:
        scan_dirs.append(drive)
    
    best_match = ""
    best_score = 0.0
    
    for scan_dir in scan_dirs:
        if time.time() - start_time > time_limit:
            break
        try:
            for root, dirs, files in os.walk(scan_dir):
                # Depth limiting
                depth = root.replace(scan_dir, "").count(os.sep)
                if depth >= max_depth:
                    dirs.clear()  # Don't descend further
                    continue
                
                if time.time() - start_time > time_limit:
                    break
                
                # Skip system/hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in 
                          ['windows', '$recycle.bin', 'system volume information', 
                           'recovery', 'perflogs', 'msocache', '__pycache__',
                           'node_modules', '.git', 'appdata']]
                
                for f in files:
                    if not f.lower().endswith(".exe"):
                        continue
                    fname = f[:-4].lower()  # Remove .exe
                    
                    # Exact match is best
                    if target == fname:
                        return os.path.join(root, f)
                    
                    # Check directory name too (e.g., "Grand Theft Auto V" folder)
                    dir_name = os.path.basename(root).lower()
                    
                    # Strong match: target found in dirname AND exe is a launcher-like file
                    if target in dir_name or _simple_similarity(target, dir_name) >= 0.65:
                        # Prefer common launcher names
                        launcher_names = ["launcher", "play", "game", fname]
                        if any(ln in fname for ln in launcher_names) or fname == dir_name.replace(" ", ""):
                            score = _simple_similarity(target, dir_name) + 0.2
                            if score > best_score:
                                best_score = score
                                best_match = os.path.join(root, f)
                    
                    # Direct name similarity
                    score = _simple_similarity(target, fname)
                    if score > best_score and score >= 0.6:
                        best_score = score
                        best_match = os.path.join(root, f)
        except (PermissionError, OSError):
            continue
    
    return best_match


def open_camera() -> str:
    """Opens the Windows Camera app."""
    try:
        os.startfile("microsoft.windows.camera:")
        time.sleep(1.5)
        return "Successfully opened the Camera app."
    except Exception:
        # Fallback: try Start Menu shortcut
        try:
            if find_and_open_app_shortcut("camera"):
                time.sleep(1.5)
                return "Successfully opened the Camera app."
        except Exception:
            pass
        return "Failed to open the Camera app. It may not be installed on this PC."


def open_app(app_name: str) -> str:
    """Launches an application using a multi-tier search strategy:
    1. Expanded app map (hardcoded common apps)
    2. Fuzzy alias resolution
    3. Start Menu shortcut search (exact + fuzzy)
    4. Windows Registry App Paths
    5. Windows Registry Uninstall entries
    6. PATH environment search
    7. Direct os.startfile / subprocess fallback
    If ALL fail, returns an "app not found" message.
    """
    name_clean = app_name.strip()
    name_clean_lower = name_clean.lower()
    
    # ── 1. Hardcoded app map (expanded) ──
    if name_clean_lower in APP_MAP:
        exec_name = APP_MAP[name_clean_lower]
        try:
            os.startfile(exec_name)
            time.sleep(1.2)
            return f"Successfully launched: {name_clean}"
        except Exception:
            # Fall back to finding shortcut if startfile fails (e.g. not in PATH)
            try:
                if find_and_open_app_shortcut(name_clean):
                    time.sleep(1.2)
                    return f"Successfully launched: {name_clean}"
            except Exception:
                pass
            
            # If all else fails, try explicit Popen without shell (to catch true errors)
            try:
                subprocess.Popen(exec_name)
                time.sleep(1.2)
                return f"Successfully opened: {name_clean}"
            except Exception:
                pass
    
    # ── 2. Fuzzy alias resolution ──
    if name_clean_lower in FUZZY_ALIASES:
        resolved = FUZZY_ALIASES[name_clean_lower]
        # Check if resolved name is in app map
        if resolved in APP_MAP:
            try:
                os.startfile(APP_MAP[resolved])
                time.sleep(1.2)
                return f"Successfully launched: {name_clean}"
            except Exception:
                pass
        # Try Start Menu with resolved name
        try:
            if find_and_open_app_shortcut(resolved, fuzzy=True):
                time.sleep(1.2)
                return f"Successfully launched '{name_clean}' (found as '{resolved}')."
        except Exception:
            pass
    
    # ── 3. Start Menu shortcut search (exact + fuzzy) ──
    try:
        if find_and_open_app_shortcut(name_clean, fuzzy=True):
            time.sleep(1.2)
            return f"Successfully launched '{name_clean}' from Start Menu."
    except Exception:
        pass
    
    # ── 4. Windows Registry App Paths + Uninstall entries ──
    reg_path = _find_app_in_registry(name_clean)
    if reg_path:
        try:
            os.startfile(reg_path)
            time.sleep(1.2)
            return f"Successfully launched '{name_clean}' from registry path."
        except Exception:
            try:
                subprocess.Popen([reg_path], shell=False)
                time.sleep(1.2)
                return f"Successfully opened '{name_clean}' from registry."
            except Exception:
                pass
    
    # ── 5. PATH environment search ──
    path_exe = _find_exe_in_path(name_clean)
    if path_exe:
        try:
            subprocess.Popen([path_exe], shell=False)
            time.sleep(1.2)
            return f"Successfully launched '{name_clean}' from system PATH."
        except Exception:
            pass
    
    # ── 6. Desktop shortcut scan ──
    try:
        if _scan_desktop_shortcuts(name_clean):
            time.sleep(1.2)
            return f"Successfully launched '{name_clean}' from Desktop shortcut."
    except Exception:
        pass
    
    # ── 7. Deep filesystem scan (scans all drives for the executable) ──
    deep_path = _find_exe_deep_scan(name_clean)
    if deep_path:
        try:
            os.startfile(deep_path)
            time.sleep(1.5)
            return f"Successfully launched '{name_clean}' (found at: {deep_path})."
        except Exception:
            try:
                subprocess.Popen([deep_path], shell=False)
                time.sleep(1.5)
                return f"Successfully opened '{name_clean}' (found at: {deep_path})."
            except Exception:
                pass
    
    # ── 8. Direct os.startfile / subprocess fallback ──
    try:
        os.startfile(name_clean)
        time.sleep(1.2)
        return f"Successfully launched: {name_clean}"
    except Exception:
        try:
            subprocess.Popen(name_clean, shell=False)
            time.sleep(1.2)
            return f"Successfully opened: {name_clean}"
        except Exception:
            pass
    
    # ── 9. ALL methods failed — app not found ──
    return f"Sorry, I couldn't find the app '{app_name}' on your PC. Please make sure it's installed, or try being more specific with the name."

def close_app(app_name: str) -> str:
    """Closes an application by killing its system processes. Supports fuzzy matching running processes."""
    import psutil
    import difflib
    import pygetwindow as gw
    
    name_clean = app_name.lower().strip()
    
    # ── 0. Handle Pronouns / Active Window ──
    if name_clean in ["it", "that", "this", "app", "application", "window", "program", "current window", "active window"]:
        active = gw.getActiveWindow()
        if active:
            try:
                active.close()
                return f"Successfully closed the active window '{active.title}'."
            except Exception as e:
                return f"Failed to close active window: {e}"
        return "No active window found to close."
    
    # Apps that minimize to tray when closed visually must be forcefully terminated
    FORCE_KILL_APPS = ["spotify", "discord", "steam", "telegram", "slack", "skype", "teams"]
    
    try:
        # ── 1. Graceful Window Closing (Visual Apps) ──
        matched_windows = []
        if not any(fka in name_clean for fka in FORCE_KILL_APPS):
            windows = gw.getAllWindows()
            
            # Exact match first
            for w in windows:
                if not w.title: continue
                if name_clean == w.title.lower():
                    matched_windows.append(w)
                    
            # Substring match if no exact match
            if not matched_windows:
                for w in windows:
                    if not w.title: continue
                    # Match title containing the app name, but ignore typical background/hidden windows
                    if name_clean in w.title.lower() and w.visible and w.width > 0:
                        matched_windows.append(w)
                        
        if matched_windows:
            for w in matched_windows:
                try:
                    w.close()
                except Exception:
                    pass
            return f"Successfully sent close signal to window(s) matching '{app_name}'."
            
        # ── 2. Forceful Process Termination (Background Apps) ──
        exec_name = APP_MAP.get(name_clean, name_clean)
        if not exec_name.endswith(".exe"):
            exec_name += ".exe"

        CREATE_NO_WINDOW = 0x08000000
        res = subprocess.run(
            f"taskkill /f /im {exec_name}",
            shell=True,
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW
        )
        if res.returncode == 0:
            return f"Successfully closed application process: {exec_name}"
        else:
            # Fuzzy match running processes
            process_dict = {}
            for p in psutil.process_iter(['name']):
                try:
                    pname = p.info['name']
                    if pname:
                        clean_p = pname.lower().replace(".exe", "")
                        process_dict[clean_p] = pname
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            matches = difflib.get_close_matches(name_clean, process_dict.keys(), n=1, cutoff=0.85)
            if matches:
                best_match_exe = process_dict[matches[0]]
                if best_match_exe.lower() in ["python.exe", "py.exe", "cmd.exe", "conhost.exe"]:
                    return f"Application '{app_name}' could not be closed because it matched a critical system process ({best_match_exe})."
                subprocess.run(f"taskkill /f /im {best_match_exe}", shell=True, check=True, capture_output=True, creationflags=CREATE_NO_WINDOW)
                return f"Successfully closed {app_name} (matched running process: {best_match_exe})."
                
            return f"Application '{app_name}' is not currently running or could not be found."
            
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
    # Prevent flashing CMD window
    CREATE_NO_WINDOW = 0x08000000
    process = subprocess.Popen(
        ["clip"],
        stdin=subprocess.PIPE,
        shell=True,
        creationflags=CREATE_NO_WINDOW
    )
    process.communicate(input=text.encode("utf-16-le"))

def _clipboard_get_native() -> str:
    """Gets the Windows clipboard text using PowerShell (always works, no Python deps)."""
    try:
        CREATE_NO_WINDOW = 0x08000000
        result = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=3.0,
            creationflags=CREATE_NO_WINDOW
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
