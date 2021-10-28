from utilities import getGenre

def filterMaps(
    maps: list[dict],
    search: str = None,
    artist: str = None,
    title: str = None,
    rating: int = None,
    genre: str = None,
) -> list[dict]:

    if search is not None:
        maps = list(
            filter(lambda beatmap: search.lower() in beatmap["artist"].lower(
            ) or search.lower() in beatmap["title"].lower(), maps)
        )
    else:
        if artist is not None:
            maps = list(
                filter(lambda beatmap: artist.lower()
                       in beatmap["artist"].lower(), maps)
            )

        if title is not None:
            maps = list(
                filter(lambda beatmap: title.lower()
                       in beatmap["title"].lower(), maps)
            )

    if rating is not None and rating > 0:
        maps = list(
            filter(lambda beatmap: round(rating) ==
                   round(beatmap["rating"]), maps)
        )

    if genre is not None:
        maps = list(filter(lambda beatmap: genre.lower()
                    == beatmap["genre"].lower(), maps))

    return maps


def filterMapsFromArgs(maps, args: list) -> tuple[list[dict], str | None, int | None, str | None]:
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
                genre = is_genre['name']
            else:
                search = arg

    maps = filterMaps(maps, search=search, rating=rating, genre=genre)
    return maps, genre, rating, search