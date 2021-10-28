import json

def loadConfigJSON() -> dict:
    with open(r"C:\Users\stagiaire.PORT-20B-11.000\Documents\Python-THEYA\config.json", 'r', encoding="utf-8") as file:
        return json.load(file)