from discord.ext import commands

from discord import Embed, Color
from discord.ext import commands


from utilities import *
from getRandomMap import *
from filters import filterMapsFromArgs

from loadDiscordConfig import loadConfigJSON as loadDiscordConfigJSON

from Classes.Connexions import Connexions

API = Connexions()

config = loadDiscordConfigJSON()


class Recommend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["r"])
    async def recommend(self, ctx, *args):
        print(f"{ctx.author.name} - recommend: {args}")

        maps = API.readDatabse("maps")

        maps, genre, rating, search = filterMapsFromArgs(maps, args)

        maps = getRandomMap(maps)

        if maps is None:
            embed = Embed(
                title="Error !",
                description=f"Nothing was found with: {search if search else ''} {str(rating) + '★' if rating else ''} {genre if genre else ''}",
                color=Color.red(),
            )
            await ctx.send(embed=embed)
            return

        for beatmap in maps:
            embed = Embed(
                title=f"{beatmap['artist']} - {beatmap['title']} by {beatmap['creator']} [{beatmap['version']}]",
                url=f"https://osu.ppy.sh/b/{beatmap['id']}",
                description=f"**▸ Difficulty:** {beatmap['rating']}★ **▸ Genre:** {beatmap['genre']} **▸ Length:** {formatMapLength(beatmap['total_length'])} ♪\n**▸ CS:** {beatmap['cs']} **▸ Accuracy:** {beatmap['accuracy']} **▸ AR:** {beatmap['ar']} **▸ HP:** {beatmap['hp']}\n\n[**Download**]({config['beatmap_mirror']}{beatmap['beatmapset_id']})",
                color=getColor(beatmap["artist"]),
            )
            embed.set_image(
                url=f"https://assets.ppy.sh/beatmaps/{beatmap['beatmapset_id']}/covers/cover@2x.jpg"
            )
            await ctx.send(embed=embed)
