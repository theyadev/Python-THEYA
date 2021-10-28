from random import sample

def getRandomMap(maps: list[dict], number: int = 1) -> list[dict] | None:
    if number <= len(maps):
        random_beatmaps = sample(maps, k=number)
        # ! Problem: random_beatmaps can contain multiple difficulty of the same beatmapset !
        return random_beatmaps

    return None