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

FUNCTIONS: Import/Export from MongoDB 

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
    4 - https://osu.ppy.sh/beatmaps/123456
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
    elif link.startswith(f"{website_url}/beatmaps/"):
        link = link.replace(f"{website_url}/beatmaps/", "")
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
        f"{beatmap_json['artist']} - {beatmap_json['title']} [{beatmap_json['version']}] has been added !")


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

    if beatmapset_id == None and beatmap_id == None:
        return False

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


"""

FUNCTIONS: Fetching betmaps from list of beatmaps

"""


def getMaps(maps: list[dict], artist: str = "", title: str = "", difficulty: float = 0, genre: str = ""):
    filters = ["artist", "title", "difficulty", "genre"]
    filtered_maps = []

    for beatmap in maps:
        for the_filter in filters:
            if artist != "" and artist.lower() in beatmap['artist'].lower():
                print('A') 


"""
TESTS
"""


def truncateMaps():
    db.maps.remove({})


class TextColors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[39m'


def runImportsTests():
    truncateMaps()

    # Test 1: Import beatmapset from supported link 1
    print(f"{TextColors.YELLOW}Should import: Every Difficulty of AliA - Kakurenbo{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmapsets/955965",
               "Classic", True)

    # Test 2: Import 1 Difficulty from supported link 2
    print(
        f"{TextColors.YELLOW}Should import: Shadow is the Light [blob]{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmapsets/1583851#osu/3235078",
               "Classic", False)

    # Test 3: Import beatmapset from supported link 2
    print(
        F"{TextColors.YELLOW}Should import: Kuyenda [Underwater]{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmapsets/880539#osu/1929422", "Tech", True)

    # Test 4: Import 1 Difficulty from supported link 3
    print(
        F"{TextColors.YELLOW}Should import: Feelsleft0ut [Nokris' Extreme]{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/b/1722775",
               "Classic", False)

    # Test 5: Import beatmapset from supported link 3
    print(F"{TextColors.YELLOW}Should not import: AliA - Kakurenbo{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/b/1996988",
               "Classic", True)

    # Test 6: Import 1 Difficulty from supported link 4
    print(
        F"{TextColors.YELLOW}Should import: Kirameki Inokori Daisensou [F4UZ4N's Expert!]{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmaps/2319298", "Classic", False)

    # Test 7: Import beatmapset from supported link 4
    print(F"{TextColors.YELLOW}Should import every difficulty from *Feels Seasickness...*{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmaps/1929269", "Tech", True)

    # Test 8: Passing wrong link
    print(F"{TextColors.YELLOW}Should do nothing{TextColors.RESET}")
    addBeatmap("https://youtube.com", "Tech", True)

    # Test 9: Passing wrong genre
    print(F"{TextColors.YELLOW}Should do nothing{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmaps/1929269", "TechAndAlternate", True)

    # Test 10: Passing wrong import_beatmapset
    print(F"{TextColors.YELLOW}Should do nothing{TextColors.RESET}")
    addBeatmap("https://osu.ppy.sh/beatmaps/1929269", "Tech", 58)


"""
MAIN
"""

if __name__ == "__main__":
    # runImportsTests()
    maps = readMapsMongo()
    getMaps(maps, artist="Alia")
