import json
import os

class SafetyManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            ron_dir = os.path.join(appdata, "RON")
            if not os.path.exists(ron_dir):
                os.makedirs(ron_dir)
            self.config_path = os.path.join(ron_dir, "ron_config.json")
        else:
            self.config_path = config_path
            
        self.safe_mode = True
        self.load_settings()

    def load_settings(self):
        """Loads settings from a local config file, creating it if it doesn't exist."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.safe_mode = data.get("safe_mode", True)
            except Exception:
                self.safe_mode = True
        else:
            self.save_settings()

    def save_settings(self):
        """Saves current settings to the config file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump({"safe_mode": self.safe_mode}, f, indent=4)
        except Exception as e:
            print(f"Failed to save safety settings: {e}")

    def toggle_safe_mode(self) -> bool:
        """Toggles safe mode state and saves it."""
        self.safe_mode = not self.safe_mode
        self.save_settings()
        return self.safe_mode

    def requires_approval(self, action_type: str) -> bool:
        """Checks if a given action type requires user approval based on current settings."""
        if not self.safe_mode:
            return False
        
        # Critical actions that represent potential security risks (terminal execution / file modifications / process kills)
        critical_actions = {
            "run_command",
            "write_file",
            "read_file",
            "close_app"
        }
        return action_type in critical_actions

    def get_action_warning(self, action_type: str, details: str) -> str:
        """Returns a user-friendly description of the action to be performed."""
        warnings = {
            "run_command": f"Execute the system command: '{details}'",
            "write_file": f"Write/Overwrite file at: '{details}'",
            "read_file": f"Read content from file: '{details}'",
            "close_app": f"Force close application process: '{details}'",
            "open_app": f"Launch the application: '{details}'",
            "open_camera": "Open the Camera app on this device.",
            "open_folder": f"Open the folder path: '{details}'",
            "open_url": f"Open the website: '{details}'",
            "type_text": f"Type the text: '{details}'",
            "press_key": f"Press the key or key combination: '{details}'",
            "change_volume": f"Change the system volume state: '{details}'",
            "take_screenshot": "Capture a screenshot of your screen."
        }
        return warnings.get(action_type, f"Perform action '{action_type}' with details '{details}'")
