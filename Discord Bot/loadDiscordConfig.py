import json

def loadConfigJSON():
    config = {}

    try:
        with open("./discord_config.json", "r", encoding="utf-8") as config_file:
            config_json = json.load(config_file)
            config.update(config_json)
    except:
        with open("./Discord Bot/discord_config.json", "r", encoding="utf-8") as config_file:
            config_json = json.load(config_file)
            config.update(config_json)        

    return config