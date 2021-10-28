
from Classes.Connexions import Connexions

from ossapi import Beatmapset, Beatmap

API = Connexions()

def getBeatmapInfo(beatmapset_id: int = None, beatmap_id: int = None) -> tuple[Beatmapset, Beatmap]:
    beatmapset = None
    beatmap = None

    if beatmap_id:
        beatmapset = API.osu._get(
            Beatmapset, "/beatmapsets/lookup", {"beatmap_id": beatmap_id})
        beatmap = API.osu.beatmap(beatmap_id)
    elif beatmapset_id:
        beatmapset = API.osu._get(
            Beatmapset, "/beatmapsets/" + str(beatmapset_id))

    return beatmapset, beatmap