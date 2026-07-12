import threading
import time
import queue
from typing import Callable, List, Dict, Any

from .intent_parser import IntentParser
from .safety_manager import SafetyManager
from . import automation

class RonEngine:
    def __init__(self, ui_log_callback: Callable[[str], None] = None, 
                 ui_status_callback: Callable[[str], None] = None,
                 ui_message_callback: Callable[[str, str], None] = None,
                 ui_approval_callback: Callable[[str, str, Callable[[bool], None]], None] = None):
        self.intent_parser = IntentParser()
        self.safety_manager = SafetyManager()
        
        # GUI callbacks for communication
        self.ui_log_callback = ui_log_callback
        self.ui_status_callback = ui_status_callback
        self.ui_message_callback = ui_message_callback
        self.ui_approval_callback = ui_approval_callback
        
        # Thread safety utilities
        self.approval_event = threading.Event()
        self.approval_result = False
        self.current_thread = None
        self.is_cancelled = False

    def log(self, text: str):
        if self.ui_log_callback:
            self.ui_log_callback(text)
        print(f"[Ron LOG] {text}")

    def update_status(self, status: str):
        if self.ui_status_callback:
            self.ui_status_callback(status)

    def send_chat_message(self, sender: str, text: str):
        if self.ui_message_callback:
            self.ui_message_callback(sender, text)

    def process_instruction_async(self, text: str, chat_history: List[Dict[str, str]] = None):
        """Launches instruction processing in a background thread with conversational memory context."""
        if self.current_thread and self.current_thread.is_alive():
            self.log("Wait until current execution completes.")
            self.send_chat_message("Ron", "I am currently processing a task. Please wait a moment.")
            return

        self.is_cancelled = False
        self.current_thread = threading.Thread(target=self._process_instruction_thread, args=(text, chat_history), daemon=True)
        self.current_thread.start()

    def set_approval(self, approved: bool):
        """Called by the UI thread to resume the blocked engine thread with approval result."""
        self.approval_result = approved
        self.approval_event.set()

    def cancel_execution(self):
        """Sets task cancellation flag and triggers UI safety releases to stop execution threads."""
        self.is_cancelled = True
        self.set_approval(False)

    def _process_instruction_thread(self, text: str, chat_history: List[Dict[str, str]] = None):
        self.update_status("Thinking...")
        self.log(f"Received instruction: '{text}'")
        
        # Step 1: Parse intent with conversational context
        parsed = self.intent_parser.parse_instruction(text, chat_history)
        actions = parsed.get("actions", [])
        explanation = parsed.get("explanation", "").strip()
        mode = parsed.get("mode", "Local Rules")

        self.log(f"Parser Mode: {mode}")
        self.log(f"Explanation: {explanation}")
        self.log(f"Actions to execute: {actions}")

        if self.is_cancelled:
            self.update_status("Idle")
            self.send_chat_message("Ron", "Execution stopped.")
            return

        # If no automation actions are needed, send direct reply and exit
        if not actions:
            if explanation:
                self.send_chat_message("Ron", explanation)
            else:
                self.send_chat_message("Ron", "I processed your input, but no automation actions were generated.")
            self.update_status("Idle")
            return

        # If there are actions, send Ron's direct description text immediately (no plan logs or system headers!)
        if explanation:
            self.send_chat_message("Ron", explanation)
            time.sleep(0.2)

        success_count = 0
        cancelled = False

        # Step 2: Execute actions sequentially
        for i, action in enumerate(actions):
            if self.is_cancelled:
                cancelled = True
                break
                
            action_type = action.get("type")
            details = action.get("details")

            self.log(f"Step {i+1}/{len(actions)}: {action_type} ({details})")
            
            # Check safety approval
            if self.safety_manager.requires_approval(action_type):
                self.update_status("Awaiting Safety Approval...")
                self.log(f"Action requires approval: {action_type}")
                
                # Reset approval event
                self.approval_event.clear()
                self.approval_result = False
                
                # Ask UI to show verification prompt
                if self.ui_approval_callback:
                    self.ui_approval_callback(action_type, details, self.set_approval)
                    self.approval_event.wait()
                else:
                    self.log("Safety approval callback not found. Denying by default.")
                    self.approval_result = False

                if self.is_cancelled:
                    cancelled = True
                    break

                if not self.approval_result:
                    self.log("Action rejected by user.")
                    self.send_chat_message("Ron", f"Cancelled execution at step {i+1} because permission was denied.")
                    cancelled = True
                    break
                else:
                    self.log("Action approved by user.")

            if self.is_cancelled:
                cancelled = True
                break

            # Execute
            self.update_status(f"Executing: {action_type}...")
            result_msg = self._execute_action(action)
            self.log(result_msg)
            
            # Print output directly into the chat for command execution and file reading
            if action_type in ["run_command", "read_file"]:
                self.send_chat_message("Ron Console", result_msg)
                
            success_count += 1
            
            # Action specific focus sleeps
            if action_type == "open_app":
                time.sleep(1.0)
            elif action_type == "close_app":
                time.sleep(0.8)
            elif action_type == "wait":
                pass # Already slept during execution
            else:
                time.sleep(0.4)

        # Step 3: Complete
        self.update_status("Idle")
        if self.is_cancelled or cancelled:
            self.send_chat_message("Ron", "Execution stopped.")
            return
            
        # If rules mode (no pre-existing LLM explanation text was printed), print a brief completion notice
        if not explanation and success_count > 0:
            self.send_chat_message("Ron", "I have successfully executed the instructions.")

    def _execute_action(self, action: Dict[str, Any]) -> str:
        """Invokes the corresponding action from the automation module."""
        action_type = action.get("type")
        details = action.get("details")
        content = action.get("content", "")
        
        try:
            if action_type == "open_app":
                return automation.open_app(details)
            elif action_type == "close_app":
                return automation.close_app(details)
            elif action_type == "open_url":
                return automation.open_url(details)
            elif action_type == "open_folder":
                return automation.open_folder(details)
            elif action_type == "type_text":
                return automation.type_text(details)
            elif action_type == "press_key":
                return automation.press_key(details)
            elif action_type == "change_volume":
                return automation.change_volume(details)
            elif action_type == "take_screenshot":
                return automation.take_screenshot(output_dir="screenshots")
            elif action_type == "run_command":
                return automation.run_command(details)
            elif action_type == "write_file":
                return automation.write_file(details, content)
            elif action_type == "read_file":
                return automation.read_file(details)
            elif action_type == "wait":
                try:
                    secs = float(details)
                    time.sleep(secs)
                    return f"Successfully waited for {secs} seconds."
                except Exception as e:
                    return f"Error: Invalid wait duration '{details}': {e}"
            elif action_type in ["delete_text", "clear_text"]:
                try:
                    automation.press_key("ctrl+a")
                    time.sleep(0.2)
                    automation.press_key("backspace")
                    return "Successfully cleared existing text."
                except Exception as e:
                    return f"Error executing clear text: {str(e)}"
            else:
                return f"Error: Unknown action type '{action_type}'"
        except Exception as e:
            return f"Execution error on action '{action_type}': {str(e)}"
