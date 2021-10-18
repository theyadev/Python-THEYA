import json
from ossapi import *
from os import getenv
from dotenv import load_dotenv
from pymongo import *

load_dotenv()


"""

TODO: Error handling

"""

"""

Osu! API Connection

"""

CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")
REDIRECT_URI = getenv("REDIRECT_URI")

api = OssapiV2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


"""
MongoDB Connection
"""

MONGODB_URI = getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)
db = client.python_database

"""

Global Variables and Classes

"""


class Genre:
    def __init__(self, genre: str = "", aliases: list = []):
        self.NAME = genre
        self.ALIASES = aliases


genre_list = [
    {"genre": "Classic"},
    {"genre": "Tech"},
    {"genre": "Alternate", "aliases": ["alt"]},
    {"genre": "Speed"},
    {"genre": "Stream"},
]

valid_status = ["GRAVEYARD", "PENDING", "WIP"]

"""

Functions

"""


def getGenres(genre_list: list):
    genres = []

    for genre in genre_list:
        genres.append(
            Genre(genre["genre"], genre["aliases"]
                  if "aliases" in genre else [])
        )

    return genres


def getGenre(genre: str):
    genres = getGenres(genre_list)
    for genre_class in genres:
        if (
            genre_class.NAME.lower() == genre.lower()
            or genre_class.ALIASES.__contains__(genre.lower())
        ):
            return genre_class

    return None


def linkParser(link: str):
    website_url = "https://osu.ppy.sh"

    """
    Supported links:
    1 - https://osu.ppy.sh/beatmapsets/123456
    2 - https://osu.ppy.sh/beatmapsets/123456#osu/123456
    3 - https://osu.ppy.sh/b/123456
    """

    if not link.startswith(website_url):
        return None, None

    if link.startswith(f"{website_url}/beatmapsets/"):
        link = link.replace(f"{website_url}/beatmapsets/", "")

        if link.isnumeric():
            # In this case it's the first type of link
            return int(link), None

        if not link.__contains__("#osu"):
            # If it doesn't contain #osu, it's not a STD beatmap
            return None, None

        link = link.split("#osu/")

        if len(link) != 2:
            # Idk how this can happen but just in case
            return None, None

        if link[0].isnumeric() and link[1].isnumeric():
            return link[0], link[1]
        else:
            return None, None

    elif link.startswith(f"{website_url}/b/"):
        link = link.replace(f"{website_url}/b/", "")
        if link.isnumeric():
            return None, int(link)
        else:
            return None, None


def generateBeatmapJSON(beatmap: Beatmap, genre: Genre):
    return {
        "id": beatmap.id,
        "artist": beatmap.beatmapset.artist,
        "title": beatmap.beatmapset.title,
        "beatmapset_id": beatmap.beatmapset_id,
        "mode": beatmap.mode.name,
        "status": beatmap.status.name,
        "total_length": beatmap.total_length,
        "version": beatmap.version,
        "rating": beatmap.difficulty_rating,
        "creator": beatmap.user_id,
        "ar": beatmap.ar,
        "cs": beatmap.cs,
        "accuracy": beatmap.accuracy,
        "hp": beatmap.drain,
        "genre": genre.NAME,
    }


def readMapsMongo():
    try:
        cursor = db.maps.find({})

        maps = []

        for beatmap in cursor:
            maps.append(beatmap)

        return maps
    except:
        return []


def writeMapsMongo(beatmap: dict):
    try:
        db.maps.insert_one(beatmap)
        return True
    except:
        return False


def saveBeatmapJSON(beatmap: Beatmap, genre: Genre):
    genre = getGenre(genre)

    if beatmap.mode.name != "STD":
        # Check if game mode is STD
        return False

    if not valid_status.__contains__(beatmap.status.name):
        # Check if map is not ranked, loved or qualified
        return False

    beatmap_json = generateBeatmapJSON(beatmap, genre)

    maps = readMapsMongo()

    if any(d['id'] == beatmap.id for d in maps):
        # Check if beatmap already exist in maps
        return False

    writeMapsMongo(beatmap_json)

    print(
        f"{beatmap_json['artist']} - {beatmap_json['title']} has been added !")


def getBeatmapsFromBeatmapset(beatmapset_id: int = None, beatmap_id: int = None):
    beatmapset_discussion = None

    if beatmapset_id:
        beatmapset_discussion = api.beatmapset_discussions(
            beatmapset_id=beatmapset_id).beatmaps
    else:
        beatmapset_discussion = api.beatmapset_discussions(
            beatmap_id=beatmap_id).beatmaps

    beatmaps = []
    for beatmap_discussion in beatmapset_discussion:
        try:
            beatmaps.append(api.beatmap(beatmap_discussion.id))
        except:
            pass

    return beatmaps


def addBeatmap(url: str, genre: str, import_beatmapset: bool):
    beatmapset_id, beatmap_id = linkParser(url)

    maps = readMapsMongo()

    if any(d['id'] == beatmap_id for d in maps):
        # Check if beatmap_id already exist in maps
        return False

    if import_beatmapset == False and beatmap_id == None:
        # We need beatmap_id when importing only 1 difficulty
        return False

    if import_beatmapset == True and beatmapset_id:
        beatmapset = getBeatmapsFromBeatmapset(beatmapset_id)
        for beatmap in beatmapset:
            saveBeatmapJSON(beatmap, genre)
        return True
    else:
        if import_beatmapset == True:
            beatmapset = getBeatmapsFromBeatmapset(beatmap_id=beatmap_id)
            for beatmap in beatmapset:
                saveBeatmapJSON(beatmap, genre)
            return True

        beatmap = api.beatmap(beatmap_id)
        saveBeatmapJSON(beatmap, genre)


if __name__ == "__main__":
    addBeatmap("https://osu.ppy.sh/beatmapsets/1583851#osu/3235078",
               "Classic", False)
    addBeatmap("https://osu.ppy.sh/beatmapsets/955965",
               "Classic", True)
    addBeatmap("https://osu.ppy.sh/b/1996988",
               "Classic", False)
    addBeatmap("https://osu.ppy.sh/b/1996988",
               "Classic", True)
    addBeatmap("https://osu.ppy.sh/beatmapsets/880539#osu/1929422", "Tech", True)
