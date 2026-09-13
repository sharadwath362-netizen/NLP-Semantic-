import json
data = json.load(open("data/word_bank.json"))
# try to find a synset entry directly
print(data.get("02604760-v"))
# or if nested:
print(data.get("synsets", {}).get("02604760-v"))