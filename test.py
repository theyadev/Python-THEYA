from ossapi import *
from os import getenv
from dotenv import load_dotenv
from pymongo import *
from main import *

load_dotenv()

MONGODB_URI = getenv("TEST_DB")
CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")
REDIRECT_URI = getenv("REDIRECT_URI")
OSU_API_TOKEN = getenv("OSU_API_TOKEN")

api = OssapiV2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

client = MongoClient(MONGODB_URI)
db = client.theya


def getMaps():
    return list(db.maps.find({}))

def main():
    maps = getMaps()[::-1]

    max_ = len(maps)
    for i, beatmap in enumerate(maps):
        print(f"{i}/{max_}")
        try:
            print(f"{beatmap['artist']} - {beatmap['title']}")
            addBeatmap(f"https://osu.ppy.sh/beatmapsets/{beatmap['beatmapsetId']}", beatmap['genre'], True)
            print(f"{TextColors.GREEN}Good !{TextColors.RESET}")
        except:
            continue

# def main():
#     maps = readMapsMongo()
#     for beatmap in maps:
#         print(f"{beatmap['artist']} - {beatmap['title']}")
#         if beatmap['mode'] != "STD":
#             print(f"{TextColors.RED}Pas GOOD!{TextColors.RESET}")
#             input()
#         elif not valid_status.__contains__(beatmap['status']):
#             print(f"{TextColors.RED}Pas GOOD!{TextColors.RESET}")
#             input()
#         else:
#             print(f"{TextColors.GREEN}Good !{TextColors.RESET}")

main()