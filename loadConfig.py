import json

def loadConfigJSON() -> dict:
    try:
        with open(".\config.json", 'r', encoding="utf-8") as file:
            return json.load(file)
    except:
        with open("..\config.json", 'r', encoding="utf-8") as file:
            return json.load(file)