from ossapi import OssapiV2
from os import getenv
from dotenv import load_dotenv
from pymongo import *

load_dotenv()

CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")
REDIRECT_URI = getenv("REDIRECT_URI")
OSU_API_TOKEN = getenv("OSU_API_TOKEN")

MONGODB_URI = getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)

class Connexions:
    def __init__(self):
        self.osu = OssapiV2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
        self.mongo = client.python_database

    def readDatabse(self, name: str) -> list:
        try:
            return list(self.mongo[name].find({}))
        except:
            return []

    def writeDatabase(self, name: str, item: dict) -> bool:
        try:
            self.mongo[name].insert_one(item)
            return True
        except:
            return False

    def removeFromDatabase(self, name: str, item: dict) -> bool:
        try:
            self.mongo[name].remove_one(item)
        except:
            return False

        return True

if __name__ == "__main__": 
    con = Connexions()

    print(con.osu.beatmap(1996988))
    print(list(con.mongo.maps.find({}))[0])

