from Classes.Connexions import Connexions

from filters import filterMaps
from getRandomMap import getRandomMap
from add import addBeatmap

from logs import clearLogs

API = Connexions()

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
    API.mongo.maps.remove({})


def runImportsTests():
    truncateMaps()
    clearLogs()

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
    runImportsTests()
    maps = API.readDatabse("maps")
    maps = filterMaps(maps)

    print("-----RECOMMEND-----")
    # Recommend
    random_map = getRandomMap(maps)

    print(
        f"{random_map[0]['artist']} - {random_map[0]['title']} [{random_map[0]['version']}] {random_map[0]['rating']}* | {random_map[0]['genre']}"
    )

    print("-----BOMB-----")
    # Bomb
    random_maps = getRandomMap(maps, 5)

    for random_map in random_maps:
        print(
            f"{random_map['artist']} - {random_map['title']} [{random_map['version']}] {random_map['rating']}* | {random_map['genre']}"
        )