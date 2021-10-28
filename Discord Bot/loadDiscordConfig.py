import json

def loadConfigJSON():
    config = {}

    with open(r"C:\Users\stagiaire.PORT-20B-11.000\Documents\Python-THEYA\Discord Bot\discord_config.json", "r", encoding="utf-8") as config_file:
        config_json = json.load(config_file)
        config.update(config_json)

    return config