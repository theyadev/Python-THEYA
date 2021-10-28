from logs import writeLogs
from ossapi import Beatmapset, Beatmap
from utilities import getGenre, getCreatorName
from linkParser import linkParser
from loadConfig import loadConfigJSON

from Classes.Connexions import Connexions

API = Connexions()

config = loadConfigJSON()

"""
    Adding to main database
"""


def generateBeatmapJSON(beatmap: Beatmap, genre: dict, beatmapset: Beatmapset = None) -> dict:
    return {
        "id": beatmap.id,
        "artist": beatmapset.artist if beatmapset else beatmap.beatmapset.artist,
        "title": beatmapset.title if beatmapset else beatmap.beatmapset.title,
        "beatmapset_id": beatmap.beatmapset_id,
        "mode": beatmap.mode.name,
        "status": beatmap.status.name,
        "total_length": beatmap.total_length,
        "version": beatmap.version,
        "rating": beatmap.difficulty_rating,
        "creator": getCreatorName(API, beatmap.user_id),
        "ar": beatmap.ar,
        "cs": beatmap.cs,
        "accuracy": beatmap.accuracy,
        "hp": beatmap.drain,
        "genre": genre['name'],
    }


def addBeatmapToDatabase(beatmap: Beatmap, genre: str, beatmapset: Beatmapset = None) -> bool:
    """
        Add a beatmap to the mongo "maps" database.
    """

    genre = getGenre(genre)

    if genre is None:
        # Check if genre is a valid genre
        return False

    if beatmap.mode.name != "STD":
        # Check if game mode is STD
        return False

    if not beatmap.status.name in config["valid_status"]:
        # Check if map is not ranked, loved or qualified
        return False

    beatmap_json = generateBeatmapJSON(beatmap, genre, beatmapset=beatmapset)

    maps = API.readDatabse("maps")

    if any(d["id"] == beatmap.id for d in maps):
        # Check if beatmap already exist in maps
        return False

    API.writeDatabase("maps", beatmap_json)

    writeLogs(beatmap_json['id'], beatmap_json['artist'],
              beatmap_json['title'], "ADDED")

    return True


def addBeatmap(url: str, genre: str, import_beatmapset: bool) -> bool:
    """
        Function to add a beatmap to the mongo "maps" database using a link
    """

    beatmapset_id, beatmap_id = linkParser(url)

    if beatmapset_id == None and beatmap_id == None:
        return False

    if import_beatmapset == False and beatmap_id == None:
        # We need beatmap_id when importing only 1 difficulty
        return False

    if import_beatmapset:
        beatmapset = None

        if beatmapset_id:
            beatmapset = API.osu._get(
                Beatmapset, "/beatmapsets/" + str(beatmapset_id))
        elif beatmap_id:
            beatmapset = API.osu._get(
                Beatmapset, "/beatmapsets/lookup", {"beatmap_id": beatmap_id})

        responses = []

        for beatmap in beatmapset.beatmaps:
            responses.append(addBeatmapToDatabase(beatmap, genre, beatmapset=beatmapset))

        responses = [not response for response in responses]

        if all(responses):
            return False
    else:
        beatmap = API.osu.beatmap(beatmap_id)
        return addBeatmapToDatabase(beatmap, genre)

    return True


"""
    Adding to requests database
"""


def generateRequestBeatmapsetJSON(beatmapset: Beatmapset) -> dict:
    return {
        "artist": beatmapset.artist,
        "title": beatmapset.title,
        "beatmapset_id": beatmapset.id,
        "status": beatmapset.status.name,
        "creator": getCreatorName(API, beatmapset.user_id),
        "done": False
    }


def requestMap(url: str):
    beatmapset_id, beatmap_id = linkParser(url)

    if beatmapset_id == None and beatmap_id == None:
        return False

    maps = API.readDatabse("maps")
    requested_maps = API.readDatabse("requested_maps")

    if any(d["beatmapset_id"] == beatmapset_id for d in requested_maps) or any(d["id"] == beatmap_id for d in maps):
        # Check if beatmap_id already exist in maps
        return False

    beatmapset = None

    try:
        if beatmapset_id:
            beatmapset = API.osu._get(
                Beatmapset, "/beatmapsets/" + str(beatmapset_id))
        elif beatmap_id:
            beatmapset = API.osu._get(
                Beatmapset, "/beatmapsets/lookup", {"beatmap_id": beatmap_id})
    except:
        return False

    beatmapset_json = generateRequestBeatmapsetJSON(beatmapset)
    API.writeDatabase("requested_maps", beatmapset_json)

    writeLogs(beatmapset.id, beatmapset.artist, beatmapset.title, "REQUESTED")
    return True
