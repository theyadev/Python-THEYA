from loadConfig import loadConfigJSON

from math import floor

from random import randint, seed

config = loadConfigJSON()


def getGenre(string: str) -> dict | None:
    """
        Check if string is a valid Genre\n
        If yes return Genre class else return None.
    """

    for genre in config['genres']:
        if (
            genre['name'].lower() == string.lower()
            or ("aliases" in genre and string.lower() in genre['aliases'])
        ):
            return genre

    return None

def formatMapLength(nombre) -> str:
    hours = floor(nombre / 60 / 60)
    minutes = floor(nombre / 60) - (hours * 60)
    seconds = nombre % 60
    length = str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
    return length

def getCreatorName(API, user_id) -> str:
    """
        Return username from user_id
    """

    creator = API.osu.user(user_id)
    return creator.username

def getColor(artist):
    artist = artist.replace("/\s/g", "").lower()
    seed(artist)
    color = randint(1, 16744576)
    seed()
    return color