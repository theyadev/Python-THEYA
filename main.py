from ossapi import *
from os import getenv
from dotenv import load_dotenv
from pymongo import *
from random import sample
from math import floor

load_dotenv()


"""

TODO: Error handling

"""

"""

* Osu! API Connection

"""

CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")
REDIRECT_URI = getenv("REDIRECT_URI")
OSU_API_TOKEN = getenv("OSU_API_TOKEN")

api = OssapiV2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


"""
* MongoDB Connection
"""

MONGODB_URI = getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)
db = client.python_database

"""

* Global Variables and Classes

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

* FUNCTIONS: Import/Export from MongoDB 

"""


def getGenres(genre_list: list) -> list[Genre]:
    genres = []

    for genre in genre_list:
        genres.append(
            Genre(genre["genre"], genre["aliases"]
                  if "aliases" in genre else [])
        )

    return genres


def getGenre(genre: str) -> Genre | None:
    genres = getGenres(genre_list)
    for genre_class in genres:
        if (
            genre_class.NAME.lower() == genre.lower()
            or genre_class.ALIASES.__contains__(genre.lower())
        ):
            return genre_class

    return None


def linkParser(link: str) -> tuple((int | None, int | None)):
    """
    Supported links:\n
    1 - https://osu.ppy.sh/beatmapsets/123456\n
    2 - https://osu.ppy.sh/beatmapsets/123456#osu/123456\n
    3 - https://osu.ppy.sh/b/123456\n
    4 - https://osu.ppy.sh/beatmaps/123456\n
    """

    website_url = "https://osu.ppy.sh"

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
            return int(link[0]), int(link[1])
        else:
            return None, None

    elif link.startswith(f"{website_url}/b/"):
        link = link.replace(f"{website_url}/b/", "")
        if link.isnumeric():
            return None, int(link)
        else:
            return None, None
    elif link.startswith(f"{website_url}/beatmaps/"):
        link = link.replace(f"{website_url}/beatmaps/", "")
        if link.isnumeric():
            return None, int(link)
        else:
            return None, None

    return None, None


def getCreator(user_id):
    creator = api.user(user_id)
    return creator.username


def generateBeatmapJSON(beatmap: Beatmap, genre: Genre, beatmapset: Beatmapset = None) -> dict:
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
        "creator": getCreator(beatmap.user_id),
        "ar": beatmap.ar,
        "cs": beatmap.cs,
        "accuracy": beatmap.accuracy,
        "hp": beatmap.drain,
        "genre": genre.NAME,
    }


def readMapsMongo() -> list[dict]:
    try:
        return list(db.maps.find({}))
    except:
        return []


def writeMapsMongo(beatmap: dict) -> bool:
    try:
        db.maps.insert_one(beatmap)
        return True
    except:
        return False


def saveBeatmapJSON(beatmap: Beatmap, genre: Genre, beatmapset: Beatmapset = None) -> bool:
    genre = getGenre(genre)

    if beatmap.mode.name != "STD":
        # Check if game mode is STD
        return False

    if not valid_status.__contains__(beatmap.status.name):
        # Check if map is not ranked, loved or qualified
        return False

    beatmap_json = generateBeatmapJSON(beatmap, genre, beatmapset=beatmapset)

    maps = readMapsMongo()

    if any(d["id"] == beatmap.id for d in maps):
        # Check if beatmap already exist in maps
        return False

    writeMapsMongo(beatmap_json)

    print(
        f"{beatmap_json['artist']} - {beatmap_json['title']} [{beatmap_json['version']}] has been added !"
    )


def addBeatmap(url: str, genre: str, import_beatmapset: bool) -> bool:
    beatmapset_id, beatmap_id = linkParser(url)

    if beatmapset_id == None and beatmap_id == None:
        return False

    maps = readMapsMongo()

    if any(d["id"] == beatmap_id for d in maps):
        # Check if beatmap_id already exist in maps
        return False

    if import_beatmapset == False and beatmap_id == None:
        # We need beatmap_id when importing only 1 difficulty
        return False

    if import_beatmapset == True and beatmapset_id:
        # beatmapset = api.search_beatmapsets(query=f"{beatmapset_id}&s=any").beatmapsets[0].beatmaps
        beatmapset = api._get(Beatmapset, "/beatmapsets/" + str(beatmapset_id))
        for beatmap in beatmapset.beatmaps:
            saveBeatmapJSON(beatmap, genre, beatmapset=beatmapset)
        return True
    else:
        if import_beatmapset == True:
            beatmapset = api._get(
                Beatmapset, "/beatmapsets/lookup", {"beatmap_id": beatmap_id})
            for beatmap in beatmapset.beatmaps:
                saveBeatmapJSON(beatmap, genre, beatmapset=beatmapset)
            return True

        beatmap = api.beatmap(beatmap_id)
        saveBeatmapJSON(beatmap, genre)


"""

* FUNCTIONS: Fetching betmaps from list of beatmaps

"""


def filterMaps(
    maps: list[dict],
    search: str = "",
    artist: str = "",
    title: str = "",
    rating: int = 0,
    genre: str = "",
) -> list[dict]:

    if search != "" and search is not None:
        maps = list(
            filter(lambda beatmap: search.lower() in beatmap["artist"].lower(
            ) or search.lower() in beatmap["title"].lower(), maps)
        )
    else:
        if artist != "" and artist is not None:
            maps = list(
                filter(lambda beatmap: artist.lower()
                       in beatmap["artist"].lower(), maps)
            )

        if title != "" and title is not None:
            maps = list(
                filter(lambda beatmap: title.lower()
                       in beatmap["title"].lower(), maps)
            )

    if rating is not None and rating > 0:
        maps = list(
            filter(lambda beatmap: round(rating) ==
                   round(beatmap["rating"]), maps)
        )

    if genre != "" and genre is not None:
        maps = list(filter(lambda beatmap: genre.lower()
                    == beatmap["genre"].lower(), maps))

    return maps


def getRandomMap(maps: list[dict], number: int = 1) -> list[dict] | None:
    if number <= len(maps):
        random_beatmaps = sample(maps, k=number)
        # ! Problem: random_beatmaps can contain multiple difficulty of the same beatmapset !
        return random_beatmaps

    return None


def filterMapsFromArgs(args):
    maps = readMapsMongo()

    genre = None
    rating = None
    search = None

    for arg in args:
        if arg.isnumeric():
            if rating is None:
                rating = int(arg)
        else:
            is_genre = getGenre(arg)

            if is_genre is not None:
                genre = is_genre.NAME
            else:
                search = arg

    maps = filterMaps(maps, search=search, rating=rating, genre=genre)
    return maps, genre, rating, search

"""

* Requests Functions

"""

def readRequestedMaps() -> list[dict]:
    try:
        return list(db.requested_maps.find({}))
    except:
        return []

def writeRequestedMaps(beatmapset: dict) -> bool:
    try:
        db.requested_maps.insert_one(beatmapset)
        return True
    except:
        return False

def generateRequestBeatmapsetJSON(beatmapset: Beatmapset) -> dict:
    return {
        "artist": beatmapset.artist,
        "title": beatmapset.title,
        "beatmapset_id": beatmapset.id,
        "status": beatmapset.status.name,
        "creator": getCreator(beatmapset.user_id),
        "done": False
    }

def requestMap(url: str):
    beatmapset_id, beatmap_id = linkParser(url)

    if beatmapset_id == None and beatmap_id == None:
        return False

    maps = readMapsMongo()
    requested_maps = readRequestedMaps()

    if any(d["beatmapset_id"] == beatmapset_id for d in requested_maps) or any(d["id"] == beatmap_id for d in maps):
        # Check if beatmap_id already exist in maps
        return False
    
    beatmapset = None
    if beatmapset_id:
        beatmapset = api._get(Beatmapset, "/beatmapsets/" + str(beatmapset_id))
    elif beatmap_id:
        beatmapset = api._get(Beatmapset, "/beatmapsets/lookup", {"beatmap_id": beatmap_id})
        
    beatmapset_json = generateRequestBeatmapsetJSON(beatmapset)
    writeRequestedMaps(beatmapset_json)

    print(f"{beatmapset_json['artist']} - {beatmapset_json['title']} has been requested !")
    return True


"""

* Other Functions

"""


def getBeatmapInfo(beatmapset_id: int = None, beatmap_id: int = None, import_all=False):
    beatmapset = None
    beatmap = None

    if beatmap_id:
        beatmapset = api._get(
            Beatmapset, "/beatmapsets/lookup", {"beatmap_id": beatmap_id})
        beatmap = api.beatmap(beatmap_id)
    elif beatmapset_id:
        beatmapset = api._get(Beatmapset, "/beatmapsets/" + str(beatmapset_id))

    return beatmapset, beatmap

def mapLength(nombre):
    heures = floor(nombre / 60 / 60)
    minutes = floor(nombre / 60) - (heures * 60)
    secondes = nombre % 60
    duree = str(minutes).zfill(2) + ':' + str(secondes).zfill(2)
    return duree

"""

* TESTS

"""


class TextColors:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[39m"


def truncateMaps():
    db.maps.remove({})


def runImportsTests():
    truncateMaps()

    # Test 1: Import beatmapset from supported link 1
    print(
        f"{TextColors.YELLOW}Should import: Every Difficulty of AliA - Kakurenbo{TextColors.RESET}"
    )
    addBeatmap("https://osu.ppy.sh/beatmapsets/955965", "Classic", True)

    # Test 2: Import 1 Difficulty from supported link 2
    print(
        f"{TextColors.YELLOW}Should import: Shadow is the Light [blob]{TextColors.RESET}"
    )
    addBeatmap("https://osu.ppy.sh/beatmapsets/1583851#osu/3235078",
               "Classic", False)

    # Test 3: Import beatmapset from supported link 2
    print(
        f"{TextColors.YELLOW}Should import: Kuyenda [Underwater]{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmapsets/880539#osu/1929422", "Tech", True)

    # Test 4: Import 1 Difficulty from supported link 3
    print(
        f"{TextColors.YELLOW}Should import: Feelsleft0ut [Nokris' Extreme]{TextColors.RESET}"
    )
    addBeatmap("https://osu.ppy.sh/b/1722775", "Classic", False)

    # Test 5: Import beatmapset from supported link 3
    print(f"{TextColors.YELLOW}Should not import: AliA - Kakurenbo{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/b/1996988", "Classic", True)

    # Test 5: Import beatmapset from supported link 3
    print(f"{TextColors.YELLOW}Should import CHika CHika Chikatto{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/b/1983407", "Classic", True)

    # Test 6: Import 1 Difficulty from supported link 4
    print(
        f"{TextColors.YELLOW}Should import: Kirameki Inokori Daisensou [F4UZ4N's Expert!]{TextColors.RESET}"
    )
    addBeatmap("https://osu.ppy.sh/beatmaps/2319298", "Classic", False)

    # Test 7: Import beatmapset from supported link 4
    print(
        f"{TextColors.YELLOW}Should import every difficulty from *Feels Seasickness...*{TextColors.RESET}"
    )
    addBeatmap("https://osu.ppy.sh/beatmaps/1929269", "Tech", True)

    # Test 8: Passing wrong link
    print(f"{TextColors.YELLOW}Should do nothing{TextColors.RESET}")
    addBeatmap("https://youtube.com", "Tech", True)

    # Test 9: Passing wrong genre
    print(f"{TextColors.YELLOW}Should do nothing{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmaps/1929269", "TechAndAlternate", True)

    # Test 10: Passing wrong import_beatmapset
    print(f"{TextColors.YELLOW}Should do nothing{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmaps/1929269", "Tech", 58)


"""

* MAIN

"""

if __name__ == "__main__":
    # runImportsTests()
    maps = readMapsMongo()
    maps = filterMaps(maps)

    print("-----RECOMMEND-----")
    # Recommend
    random_map = getRandomMap(maps)

    print(
        f"{random_map[0]['artist']} - {random_map[0]['title']} [{random_map[0]['version']}] {random_map[0]['rating']}*"
    )

    print("-----BOMB-----")
    # Bomb
    random_maps = getRandomMap(maps, 5)

    for random_map in random_maps:
        print(
            f"{random_map['artist']} - {random_map['title']} [{random_map['version']}] {random_map['rating']}*"
        )
