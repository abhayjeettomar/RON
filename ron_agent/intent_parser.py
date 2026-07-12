import re
import json
import urllib.request
import urllib.parse
import urllib.error

class IntentParser:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.system_prompt = (
            "You are Ron, an offline desktop AI assistant with direct system integration.\n"
            "Chat naturally for greetings and questions. For system tasks, output ONE JSON block.\n\n"
            "CRITICAL RULES:\n"
            "1. Output EXACTLY ONE JSON block at the END of your response. Never multiple.\n"
            "2. Keep your text explanation SHORT — one sentence max.\n"
            "3. NEVER show intermediate steps, progress updates, or partial action lists.\n"
            "4. NEVER make up system specs, file paths, or hardware info.\n"
            "5. To type text INTO an app (like notepad), use type_text, NOT write_file.\n"
            "6. To clear existing text in an app, use press_key with ctrl+a then backspace.\n\n"
            "Available actions:\n"
            "- {\"type\": \"open_app\", \"details\": \"notepad\"}\n"
            "- {\"type\": \"close_app\", \"details\": \"notepad\"}\n"
            "- {\"type\": \"type_text\", \"details\": \"text to type into focused app\"}\n"
            "- {\"type\": \"press_key\", \"details\": \"ctrl+a\"} (or enter, backspace, ctrl+c, etc.)\n"
            "- {\"type\": \"open_url\", \"details\": \"google.com\"}\n"
            "- {\"type\": \"open_folder\", \"details\": \"C:\\\\Users\"}\n"
            "- {\"type\": \"change_volume\", \"details\": \"up\"}\n"
            "- {\"type\": \"take_screenshot\", \"details\": \"\"}\n"
            "- {\"type\": \"run_command\", \"details\": \"ipconfig\"}\n"
            "- {\"type\": \"write_file\", \"details\": \"C:\\\\path\\\\file.txt\", \"content\": \"text\"}\n"
            "- {\"type\": \"read_file\", \"details\": \"C:\\\\path\\\\file.txt\"}\n"
            "- {\"type\": \"wait\", \"details\": \"10\"}\n\n"
            "Example — user says 'open notepad and type hello':\n"
            "Opening Notepad and typing for you.\n"
            "```json\n"
            "{\"actions\": [{\"type\": \"open_app\", \"details\": \"notepad\"}, "
            "{\"type\": \"type_text\", \"details\": \"hello\"}], "
            "\"explanation\": \"Opening Notepad and typing hello.\"}\n"
            "```\n\n"
            "For general chat (hi, how are you, etc.), respond naturally without any JSON."
        )

    def parse_instruction(self, text: str, chat_history: list = None) -> dict:
        """Parses user instruction. Tries Ollama first, then falls back to rule-based parser."""
        ollama_active = self.check_ollama_status()
        
        if ollama_active:
            try:
                return self.parse_with_ollama(text, chat_history)
            except Exception as e:
                print(f"Ollama parsing failed: {e}. Falling back to rule-based parser.")
        
        return self.parse_with_rules(text)

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

    def parse_with_ollama(self, text: str, chat_history: list = None) -> dict:
        """Sends prompt to Ollama and extracts the LAST valid JSON action block."""
        model_name = self.get_best_model_name()
        url = f"{self.ollama_url}/api/chat"
        
        messages = [{"role": "system", "content": self.system_prompt}]
        if chat_history:
            messages.extend(chat_history[-10:])
        else:
            messages.append({"role": "user", "content": text})
            
        payload = {"model": model_name, "messages": messages, "stream": False}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, 
                                     headers={"Content-Type": "application/json"}, method="POST")
        
        with urllib.request.urlopen(req, timeout=30.0) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            message_content = res_json.get("message", {}).get("content", "").strip()
            
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
                for action in res["actions"]:
                    # Anaphora resolution for "it" pronoun in close commands (e.g. "open notepad and close it")
                    if action["type"] == "close_app" and action["details"].lower() == "it":
                        # Search previous actions inside the same chain for an open_app details
                        for prev_act in reversed(actions):
                            if prev_act["type"] == "open_app":
                                action["details"] = prev_act["details"]
                                # Update description label in explanation
                                if "'it'" in res["explanation"]:
                                    res["explanation"] = res["explanation"].replace("'it'", f"'{prev_act['details']}'")
                                break
                actions.extend(res["actions"])
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
        # 1. Scan for delay suffixes
        delay_match = re.search(r"\b(?:after|in|for)\s+(\d+)\s*(?:seconds|sec|s)?\b", clause_clean)
        delay_seconds = 0
        if delay_match:
            try:
                delay_seconds = int(delay_match.group(1))
                # Strip the suffix from rule clean strings
                clause_clean = clause_clean.replace(delay_match.group(0), "").strip()
                raw_clause = re.sub(r"\b(?:after|in|for)\s+\d+\s*(?:seconds|sec|s)?\b", "", raw_clause, flags=re.IGNORECASE).strip()
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
                "1. Apps: 'open notepad', 'close notepad', 'launch spotify'\n"
                "2. Web: 'search python variables', 'open google.com'\n"
                "3. Automation: 'type [text]', 'press enter', 'screenshot'\n"
                "4. System: 'volume up', 'volume down', 'mute', 'time', 'date'\n"
                "5. Terminal: 'run command ipconfig'\n"
                "6. Files: 'read file C:\\test.txt', 'write hello to file C:\\test.txt'\n\n"
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
        if any(phrase in clause_clean for phrase in clear_phrases):
            actions.append({"type": "press_key", "details": "ctrl+a"})
            actions.append({"type": "press_key", "details": "backspace"})
            explanation = "clear all text"
            return {"actions": actions, "explanation": explanation}

        # 2. File Writing Pattern
        write_match1 = re.search(r"\b(?:write file|write to file|create file)\s+(\S+)\s+(?:with\s+)?content\s+(.+)\b", raw_clause, re.IGNORECASE)
        write_match2 = re.search(r"\b(?:write|create)\s+(.+)\s+to\s+file\s+(\S+)\b", raw_clause, re.IGNORECASE)
        
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
        elif re.search(r"\b(?:read file|read|view file)\s+(\S+)\b", clause_clean):
            read_match = re.search(r"\b(?:read file|read|view file)\s+(\S+)\b", raw_clause, re.IGNORECASE)
            filepath = read_match.group(1).strip()
            if filepath.lower() not in ["notepad", "calculator", "chrome", "cmd", "explorer", "paint", "taskmgr", "folder", "directory"]:
                actions.append({"type": "read_file", "details": filepath})
                explanation = f"read file '{filepath}'"
                return {"actions": actions, "explanation": explanation}

        # 4. Open Folder Pattern
        folder_match = re.search(r"\b(?:open|show)\s+(?:folder|directory|path)\s+(.+)\b", raw_clause, re.IGNORECASE)
        if folder_match:
            folder_path = folder_match.group(1).strip()
            actions.append({"type": "open_folder", "details": folder_path})
            explanation = f"open folder '{folder_path}'"
            return {"actions": actions, "explanation": explanation}

        # 5. Open URL / Web Search Pattern
        url_match = re.search(r"\b(?:open|go to|browse)\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}\S*)\b", clause_clean)
        search_match = re.search(r"\b(?:search|search for|google)\s+(.+)\b", clause_clean)
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
        cmd_match = re.search(r"\b(?:run command|execute command|run in cmd|run in terminal|terminal|execute|cmd|shell)\s+(.+)\b", raw_clause, re.IGNORECASE)
        if cmd_match:
            cmd = cmd_match.group(1).strip()
            is_common_app = any(app in cmd.lower() for app in ["notepad", "calculator", "chrome", "paint", "taskmgr"])
            if not is_common_app or len(cmd.split()) > 1:
                actions.append({"type": "run_command", "details": cmd})
                explanation = f"run command '{cmd}'"
                return {"actions": actions, "explanation": explanation}

        # 7. Close App Pattern
        close_match = re.search(r"\b(?:close|kill|terminate|stop|exit)\s+(?:the\s+)?([a-zA-Z0-9_-]+)\b", clause_clean)
        if close_match:
            app_name = close_match.group(1)
            if app_name not in ["folder", "directory", "path", "file", "url", "website", "command", "cmd", "shell"]:
                raw_app_match = re.search(r"\b(?:close|kill|terminate|stop|exit)\s+(?:the\s+)?([a-zA-Z0-9_-]+)\b", raw_clause, re.IGNORECASE)
                raw_app_name = raw_app_match.group(1) if raw_app_match else app_name
                actions.append({"type": "close_app", "details": raw_app_name})
                explanation = f"close application '{raw_app_name}'"
                return {"actions": actions, "explanation": explanation}

        # 8. Open Generic App Pattern
        app_match = re.search(r"\b(?:open|launch|start|run)\s+(?:the\s+)?([a-zA-Z0-9_-]+)\b", clause_clean)
        if app_match:
            app_name = app_match.group(1)
            if app_name not in ["folder", "directory", "path", "file", "url", "website", "command", "cmd", "shell"]:
                raw_app_match = re.search(r"\b(?:open|launch|start|run)\s+(?:the\s+)?([a-zA-Z0-9_-]+)\b", raw_clause, re.IGNORECASE)
                raw_app_name = raw_app_match.group(1) if raw_app_match else app_name
                actions.append({"type": "open_app", "details": raw_app_name})
                explanation = f"open application '{raw_app_name}'"
                return {"actions": actions, "explanation": explanation}

        # 9. Type Text Pattern
        type_match = re.search(r"\b(?:type|type out|write|write down)\s+(.+)\b", raw_clause, re.IGNORECASE)
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
        if any(v in clause_clean for v in ["volume up", "increase volume", "increase the volume", "raise volume", "raise the volume", "volume increase"]):
            actions.append({"type": "change_volume", "details": "up"})
            explanation = "increase volume"
            return {"actions": actions, "explanation": explanation}
        elif any(v in clause_clean for v in ["volume down", "decrease volume", "decrease the volume", "lower volume", "lower the volume", "volume decrease"]):
            actions.append({"type": "change_volume", "details": "down"})
            explanation = "decrease volume"
            return {"actions": actions, "explanation": explanation}
        elif any(v in clause_clean for v in ["mute", "unmute"]):
            actions.append({"type": "change_volume", "details": "mute"})
            explanation = "toggle volume mute"
            return {"actions": actions, "explanation": explanation}

        # 11. Screenshot Pattern
        if "screenshot" in clause_clean or "capture screen" in clause_clean:
            actions.append({"type": "take_screenshot", "details": ""})
            explanation = "capture screenshot"
            return {"actions": actions, "explanation": explanation}

        # 12. Press Key Pattern
        key_match = re.search(r"\bpress\s+(enter|tab|backspace|space|esc|escape|ctrl\+[a-z]|alt\+[a-z]|win\+[a-z])\b", clause_clean)
        if key_match:
            key_name = key_match.group(1)
            actions.append({"type": "press_key", "details": key_name})
            explanation = f"press key '{key_name}'"
            return {"actions": actions, "explanation": explanation}

        return {"actions": [], "explanation": ""}
