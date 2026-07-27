from ron_agent.intent_parser import IntentParser
parser = IntentParser()
res = parser.parse_with_rules("open discord,spotify and close both after 10 sec")
print(res)
