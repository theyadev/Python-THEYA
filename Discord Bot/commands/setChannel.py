from discord.ext import commands

from discord.ext.commands.context import Context
from discord.message import Message

from discord import Embed, Color
from discord.ext import commands

from loadDiscordConfig import loadConfigJSON as loadDiscordConfigJSON

from checkIfAuthorIsMe import checkIfAuthorIsMe

from Classes.Connexions import Connexions

API = Connexions()

config = loadDiscordConfigJSON()

positive_responses = ["oui", "o", "yes", "y"]
negative_responses = ["non", "n", "no"]

valid_responses = positive_responses + negative_responses


class setChannel(commands.Cog):
    def __init__(self, bot, servers):
        self.bot = bot
        self.servers = servers

    @commands.command()
    async def setChannel(self, ctx: Context, arg: str, type: str):
        if not await checkIfAuthorIsMe(ctx):
            return

        types = ["authorized_channels", "requests_channels",
                 "approval_channels", "decline_channels"]

        if not type in types:
            return

        print(f"{ctx.author.name} - setChannel: {arg}")

        if arg.isnumeric():

            def checkPositiveOrNegative(message: Message):
                return (
                    message.content.lower() in valid_responses
                    and message.author == ctx.author
                )

            channel = self.bot.get_channel(int(arg))

            if channel is None:
                return await ctx.send(embed=Embed(
                    title="Error !",
                    description=f"Channel ID incorrect ! (15s)",
                    color=Color.red(),
                ))

            servers_type = filter(lambda x: x['type'] == type, self.servers)

            if any(server for server in servers_type if server["id"] == int(arg)):
                await ctx.send(
                    f"Channel #{channel} is already a {type}, do you want to remove it ?"
                )

                try:
                    message: Message = await self.bot.wait_for(
                        "message", check=checkPositiveOrNegative, timeout=15
                    )
                except:
                    embed_timeout = Embed(
                        title="Error !",
                        description=f"You took too long, bot timeout ! (15s)",
                        color=Color.red(),
                    )
                    await ctx.send(embed=embed_timeout)
                    return

                if message.content.lower() in positive_responses:

                    self.servers.remove({"id": int(arg), "type": type})

                    API.removeFromDatabase(
                        "servers", {"id": int(arg), "type": type})

                    embed = Embed(
                        title="Success !",
                        description=f"#{channel} has been removed from {type} !",
                        color=Color.green(),
                    )
                    await ctx.send(embed=embed)
                else:
                    embed = Embed(
                        title="Task aborted !",
                        description="Aborted by user.",
                        color=Color.orange(),
                    )
                    await ctx.send(embed=embed)

                return

            await ctx.send(
                f"Are you sure you want to add channel #{channel} to the list of {type} ?"
            )

            try:
                message: Message = await self.bot.wait_for(
                    "message", check=checkPositiveOrNegative, timeout=15
                )
            except:
                embed_timeout = Embed(
                    title="Error !",
                    description=f"You took too long, bot timeout ! (15s)",
                    color=Color.red(),
                )
                await ctx.send(embed=embed_timeout)
                return

            if message.content.lower() in positive_responses:
                self.servers.append({"id": int(arg), "type": type})

                API.writeDatabase("servers", {"id": int(arg), "type": type})

                embed = Embed(
                    title="Success !",
                    description=f"#{channel} is now a {type} !",
                    color=Color.green(),
                )
                await ctx.send(embed=embed)
            else:
                embed = Embed(
                    title="Task aborted !",
                    description="Aborted by user.",
                    color=Color.orange(),
                )
                await ctx.send(embed=embed)
