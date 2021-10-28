def linkParser(link: str) -> tuple[int | None, int | None]:
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
