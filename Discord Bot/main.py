import json
import sys

from discord import Embed, Color
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.ext.commands.context import Context
from discord.message import Message

from os import getenv
from dotenv import load_dotenv

from pymongo import *

from loadDiscordConfig import loadConfigJSON as loadDiscordConfigJSON

sys.path.append("../")

from utilities import *
from getRandomMap import *
from filters import filterMapsFromArgs
from linkParser import linkParser
from getBeatmapInfo import getBeatmapInfo
from add import addBeatmap, requestMap

from checkIfAuthorIsMe import checkIfAuthorIsMe


from Classes.Connexions import Connexions

from commands.recommend import Recommend
from commands.setChannel import setChannel
from commands.seeChannels import seeChannels
from commands.maps import Maps

API = Connexions()

load_dotenv()

DISCORD_TOKEN = getenv("DISCORD_TOKEN")

admin_request_channel = getenv("REQUEST_CHANNEL_ID")
admin_request_message = getenv("REQUEST_MESSAGE_ID")

config = loadDiscordConfigJSON()

config["servers"] = []


config["servers"] = list(API.readDatabse('servers'))

for i in range(len(config['servers'])):
    del config['servers'][i]['_id']


bot = commands.Bot(command_prefix=config["prefix"])

positive_responses = ["oui", "o", "yes", "y"]
negative_responses = ["non", "n", "no"]

valid_responses = positive_responses + negative_responses


@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))

@bot.command()
async def sendEmptyMessage(ctx: Context):
    if ctx.author.id != 382302674164514818:
        return

    message = await ctx.send(" H")
    print(ctx.channel.id, message.id)

async def handleAdd(message, beatmap, beatmapset):
    def checkPositiveOrNegative(msg: Message):
        return (
            valid_responses.__contains__(msg.content.lower())
            and msg.author == message.author
        )

    def check(msg: Message):
        return msg.author == message.author

    timeout = 30

    embed_timeout = Embed(
        title="Error !",
        description=f"You took too long, bot timeout ! ({timeout}s)",
        color=Color.red(),
    )

    import_all = False if beatmap is not None else True

    if len(beatmapset.beatmaps) > 1 and not import_all:
        await message.channel.send(embed=Embed(
            title="Do you want to add every difficulty of the beatmapset in the database ?",
            description="(yes/no)",
            color=Color.blue(),
        ))

        try:
            msg_import: Message = await bot.wait_for(
                "message", check=checkPositiveOrNegative, timeout=timeout
            )
        except:
            await message.channel.send(embed=embed_timeout)
            return

        if msg_import.content.lower() in positive_responses:
            import_all = True

    await message.channel.send(embed=Embed(
        title=f"Wich genre for the beatmap{'set' if import_all else ''} ?",
        description="(Classic/Tech/Alternate/Speed/Stream)",
        color=Color.blue(),
    ))

    genre = None

    try:
        msg_genre: Message = await bot.wait_for("message", check=check, timeout=timeout)
        genre = getGenre(msg_genre.content)
    except:
        await message.channel.send(embed=embed_timeout)
        return

    if genre is None:
        await message.channel.send(embed=Embed(
            title="Error !",
            description="Invalid genre ! Please try again !",
            color=Color.red(),
        ))
        return

    genre = genre['name']

    embed = Embed(
        title=f"Are you sure you want to import{' every difficulty of' if import_all else ''}:",
        description=f"**{beatmapset.artist}**\n**Title:** {beatmapset.title}\n**by:** {getCreatorName(API, beatmapset.creator)}\n{f'**Difficulty:** [{beatmap.version}]' if not import_all else ''}\n**With the genre:** {genre}",
        color=Color.greyple(),
        image=""
    )
    embed.set_image(url=beatmapset.covers.card_2x)
    await message.channel.send(embed=embed)

    try:
        msg_recap: Message = await bot.wait_for(
            "message", check=checkPositiveOrNegative, timeout=timeout
        )
    except:
        await message.channel.send(embed=embed_timeout)
        return

    if msg_recap.content.lower() in positive_responses:
        await message.channel.send(embed=Embed(
            title=f"Adding beatmap{'set' if import_all else ''} to database...",
            description="Please wait...",
            color=Color.orange(),
        ))

        added = addBeatmap(message.content, genre, import_all)

        embed = None

        await message.channel.send(embed=Embed(
            title=f"The beatmap{'set' if import_all else ''} has {'not' if not added else ''} been added !!",
            description="You can add another one by sending another link !",
            color=Color.green() if added else Color.red(),
        ))
    else:
        await message.channel.send(embed=Embed(
            title="Aborted.", description="Aborted by user.", color=Color.red()
        ))


async def handleRequest(message, beatmapset):
    requested_maps = API.readDatabse("requested_maps")

    if any(beatmaps["beatmapset_id"] == beatmapset.id for beatmaps in requested_maps):
        # Check if beatmap_id already exist in maps
        await message.channel.send(embed=Embed(
            title="Error !",
            description="Beatmap has already been requested !",
            color=Color.orange(),
        ))
        return

    requested = requestMap(message.content)

    await message.channel.send(embed=Embed(
        title=f"The beatmap has {'not' if not requested else ''} been requested !!",
        description="You can request another one by sending another link !",
        color=Color.green() if requested else Color.red(),
    ))

    if not requested:
        return

    admin_channel = await bot.fetch_channel(admin_request_channel)
    admin_message: Message = await admin_channel.fetch_message(admin_request_message)

    requested_maps = API.readDatabse("requested_maps")

    edit_list = [
        f"{beatmapset['artist']} - {beatmapset['title']}" for beatmapset in requested_maps]

    await admin_message.edit(content="\n".join(edit_list))


@bot.event
async def on_message(message: Message):
    if message.author == bot.user:
        return

    if message.content.startswith(config["prefix"]):
        await bot.process_commands(message)
        return

    if not any(channel for channel in config['servers'] if channel['id'] == message.channel.id):
        return

    if not message.content.startswith("https://osu.ppy.sh/"):
        return

    maps = API.readDatabse("maps")

    beatmapset_id, beatmap_id = linkParser(message.content)

    if beatmapset_id is None and beatmap_id is None:
        await message.channel.send("Lien invalide !")
        return

    if any(beatmap["id"] == beatmap_id for beatmap in maps):
        # Check if beatmap_id already exist in maps
        embed = Embed(
            title="Error !",
            description="Beatmap already in the database !",
            color=Color.orange(),
        )
        await message.channel.send(embed=embed)
        return

    beatmapset, beatmap = getBeatmapInfo(beatmapset_id, beatmap_id)

    if beatmap:
        if beatmap.mode.name != "STD":
            embed = Embed(
                title="Error !",
                description="This is not a STD beatmap !\nPlease try again with another beatmap !",
                color=Color.orange(),
            )
            await message.channel.send(embed=embed)
            return

    if not beatmapset.status.name in ["GRAVEYARD", "PENDING", "WIP"]:
        embed = Embed(
            title="Erreur !",
            description="The beatmap is RANKED, QUALIED ou LOVED !\nPlease try again with another beatmap !",
            color=Color.red(),
        )
        await message.channel.send(embed=embed)
        return

    admins_server = filter(
        lambda x: x['type'] == "authorized_channels", config["servers"])
    requests_server = filter(
        lambda x: x['type'] == "requests_channels", config["servers"])

    if any(channel for channel in admins_server if channel['id'] == message.channel.id):
        await handleAdd(message, beatmap, beatmapset)
    elif any(channel for channel in requests_server if channel['id'] == message.channel.id):
        await handleRequest(message, beatmapset)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error

bot.add_cog(Recommend(bot))
bot.add_cog(Maps(bot))
bot.add_cog(setChannel(bot, config["servers"]))
bot.add_cog(seeChannels(bot, config["servers"]))

bot.run(DISCORD_TOKEN)
