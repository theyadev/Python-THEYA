from discord.ext import commands

from discord.ext import commands

from filters import filterMapsFromArgs

from Classes.Connexions import Connexions

API = Connexions()


class Maps(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def maps(self, ctx, *args):
        print(f"{ctx.author.name} - maps: {args}")
        maps = API.readDatabse("maps")
        maps, genre, rating, search = filterMapsFromArgs(maps, args)
        await ctx.send(
            f"There are {len(maps)} maps{' with:' if search or genre or rating else ' !'}{' ' + search if search else ''}{' ' + str(rating) + '★' if rating else ''}{' ' + genre if genre else ''}"
        )
