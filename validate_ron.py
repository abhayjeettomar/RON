import sys
import os

from ron_agent.intent_parser import IntentParser
from ron_agent.safety_manager import SafetyManager

def run_tests():
    print("==========================================")
    # 1. Test Safety Manager
    print("Testing Safety Manager...")
    safety = SafetyManager("test_config.json")
    
    if os.path.exists("test_config.json"):
        os.remove("test_config.json")
        
    safety.load_settings()
    assert safety.safe_mode == True
    assert safety.requires_approval("close_app") == True
    
    print("Safety Manager: PASS")
    print("------------------------------------------")

    # 2. Test Intent Parser (History Context & Chaining)
    print("Testing Intent Parser...")
    parser = IntentParser()
    
    # Verify signature handles history context without breaking rule fallback
    res = parser.parse_with_rules("open notepad and close it")
    actions = res["actions"]
    assert len(actions) == 2
    assert actions[0]["type"] == "open_app" and actions[0]["details"] == "notepad"
    assert actions[1]["type"] == "close_app" and actions[1]["details"] == "notepad"

    # Test clearing rules
    res = parser.parse_with_rules("open notepad clear all text write hehehe then close it")
    actions = res["actions"]
    assert len(actions) == 5
    assert actions[1]["details"] == "ctrl+a"
    assert actions[2]["details"] == "backspace"
    assert actions[3]["details"] == "hehehe"
    assert actions[4]["details"] == "notepad"

    # Test system info mapping
    res = parser.parse_with_rules("find my system info")
    actions = res["actions"]
    assert len(actions) == 1
    assert actions[0]["type"] == "open_app" and actions[0]["details"] == "systeminfo"

    # Test delay wait mapping and clear phrases
    res = parser.parse_with_rules("open notepad delete any text that is written before and type the alphabets and then close the notepad after 10 seconds of doing this")
    actions = res["actions"]
    assert len(actions) == 6
    assert actions[0]["type"] == "open_app" and actions[0]["details"] == "notepad"
    assert actions[1]["type"] == "press_key" and actions[1]["details"] == "ctrl+a"
    assert actions[2]["type"] == "press_key" and actions[2]["details"] == "backspace"
    assert actions[3]["type"] == "type_text" and actions[3]["details"] == "abcdefghijklmnopqrstuvwxyz"
    assert actions[4]["type"] == "wait" and actions[4]["details"] == "10"
    assert actions[5]["type"] == "close_app" and actions[5]["details"] == "notepad"

    # Test uppercase block letters alphabet delay wait chain
    res = parser.parse_with_rules("pls open notepad delete anything that is written in there before after that write down the whole alphabet in block letters and then close it after 10 sec")
    actions = res["actions"]
    assert len(actions) == 6
    assert actions[0]["type"] == "open_app" and actions[0]["details"] == "notepad"
    assert actions[1]["type"] == "press_key" and actions[1]["details"] == "ctrl+a"
    assert actions[2]["type"] == "press_key" and actions[2]["details"] == "backspace"
    assert actions[3]["type"] == "type_text" and actions[3]["details"] == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert actions[4]["type"] == "wait" and actions[4]["details"] == "10"
    assert actions[5]["type"] == "close_app" and actions[5]["details"] == "notepad"

    print("Intent Parser: PASS")
    print("------------------------------------------")

    # Clean up
    if os.path.exists("test_config.json"):
        os.remove("test_config.json")
        
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
