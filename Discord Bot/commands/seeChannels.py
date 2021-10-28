from discord.ext import commands

from discord.ext import commands

from discord import Embed, Color

from checkIfAuthorIsMe import checkIfAuthorIsMe

from Classes.Connexions import Connexions

API = Connexions()


class seeChannels(commands.Cog):
    def __init__(self, bot, servers):
        self.bot = bot
        self.servers = servers

    @commands.command()
    async def seeChannels(self, ctx):
        if not await checkIfAuthorIsMe(ctx):
            return
        print(f"{ctx.author.name} - seeChannels")

        channels = [
            "#" +
            str(self.bot.get_channel(server['id'])) + f" {server['type']}"
            for server in self.servers
            if self.bot.get_channel(server['id']) is not None
        ]
        description = "\n".join(channels)
        embed = Embed(
            title="Moderation channels list:", description=description, color=Color.blue()
        )
        await ctx.send(embed=embed)
