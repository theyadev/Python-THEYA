from dotenv import load_dotenv

load_dotenv()

from os import getenv
from ossapi import *
import json


"""

TODO: Use MongoDB or SQL Database instead of JSONs

"""

"""

Osu! API Connection

"""

client_id = getenv("CLIENT_ID")
client_secret = getenv("CLIENT_SECRET")
redirect_uri = getenv("REDIRECT_URI")

api = OssapiV2(client_id, client_secret, redirect_uri)

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

"""

Functions

"""


def getGenres(genre_list: list):
    genres = []

    for genre in genre_list:
        genres.append(
            Genre(genre["genre"], genre["aliases"] if "aliases" in genre else [])
        )

    return genres


def linkParser(link: str):
    website_url = "https://osu.ppy.sh"

    if not link.startswith(website_url):
        return None, None

    if link.startswith(f"{website_url}/beatmapsets/"):
        link = link.replace(f"{website_url}/beatmapsets/", "")

        if link.isnumeric():
            return int(link), None

        if not link.__contains__("#osu"):
            return None, None

        link = link.split("#osu/")

        if len(link) != 2:
            return None, None

        if link[0].isnumeric() and link[1].isnumeric():
            return link[0], link[1]
        else:
            return None, None

    elif link.startswith(f"{website_url}/b/"):
        link = link.replace(f"{website_url}/b/", "")
        if link.isnumeric():
            return int(link), None
        else:
            return None, None


def getGenre(genre: str):
    genres = getGenres(genre_list)
    for genre_class in genres:
        if (
            genre_class.NAME.lower() == genre.lower()
            or genre_class.ALIASES.__contains__(genre.lower())
        ):
            return genre_class

    return None


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


def readMapsJSON():
    try:
        with open("./maps.json", "r", encoding="utf-8") as maps_data:
            maps = json.load(maps_data)
            return maps
    except:
        return []


def writeMapsJSON(beatmap: dict):
    maps = readMapsJSON()
    maps.append(beatmap)
    with open("./maps.json", "w") as maps_data:
        json.dump(maps, maps_data, ensure_ascii=False, indent=4)


def addBeatmap(url: str, genre: str, import_beatmapset: bool):
    beatmapset_id, beatmap_id = linkParser(url)

    if import_beatmapset == False and beatmap_id == None:
        return False

    genre = getGenre(genre)

    if import_beatmapset == True and beatmap_id == None:
        beatmapset = api.search_beatmapsets(beatmapset_id).beatmapsets[0].beatmaps

        for beatmap in beatmapset:
            """
            TODO: Use the function saveBeatmapJSON
            """
            pass
    else:
        if import_beatmapset == True:
            beatmapset = api.beatmap(beatmap_id).beatmapset.beatmaps
            for beatmap in beatmapset:
                """
                TODO: Use the function saveBeatmapJSON
                """
                pass

        """
        TODO: Put code below in a function called saveBeatmapJSON
        """

        beatmap = api.beatmap(beatmap_id)

        valid_status = ["GRAVEYARD", "PENDING", "WIP"]

        if not valid_status.__contains__(beatmap.status.name):
            return False

        beatmap_json = generateBeatmapJSON(beatmap, genre)

        maps = readMapsJSON()

        if maps.__contains__(beatmap_json):
            return False

        writeMapsJSON(beatmap_json)

        print(f"{beatmap_json['artist']} - {beatmap_json['title']} has been added !")


if __name__ == "__main__":
    addBeatmap("https://osu.ppy.sh/beatmapsets/1583851#osu/3235078", "Classic", False)
