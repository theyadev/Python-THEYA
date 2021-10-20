import json
from discord import Embed, Color
from discord.ext import commands
from os import getenv
from discord.ext.commands.context import Context
from discord.message import Message
from dotenv import load_dotenv
from main import (
    getCreator,
    readMapsMongo,
    getRandomMap,
    filterMaps,
    getGenre,
    linkParser,
    getBeatmapInfo,
    addBeatmap,
    valid_status,
)
from pymongo import *

load_dotenv()

MONGODB_URI = getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)
db = client.python_database

config = {}

with open("./discord_config.json", "r", encoding="utf-8") as config_file:
    config_json = json.load(config_file)
    config.update(config_json)

config["authorized_channels"] = []

servers = list(db.servers.find({}))

for server in servers:
    config["authorized_channels"].append(server["id"])

bot = commands.Bot(command_prefix=config["prefix"])

positive_responses = ["oui", "o", "yes", "y"]
negative_responses = ["non", "n", "no"]

valid_responses = positive_responses + negative_responses


def getColor(artist):
    artist = artist.replace("/\s/g", "").lower()
    n = 0
    for i in range(len(artist)):
        u = ord(artist[i]) - 64
        n += u * (i * u)
    return n


@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))


@bot.command()
async def setChannel(ctx: Context, arg: str):
    if ctx.author.id != 382302674164514818:
        embed = Embed(
            title="You are not authorized.",
            description="You can't do this command !",
            color=Color.red(),
        )
        await ctx.send(embed=embed)
        return
    if arg.isnumeric():

        def checkPositiveOrNegative(message: Message):
            return (
                valid_responses.__contains__(message.content.lower())
                and message.author == ctx.author
            )

        channel = bot.get_channel(int(arg))

        if config["authorized_channels"].__contains__(int(arg)):
            await ctx.send(
                f"Channel #{channel} is already a moderation channel, do you want to remove it ?"
            )

            try:
                message: Message = await bot.wait_for(
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

            if positive_responses.__contains__(message.content.lower()):
                config["authorized_channels"].remove(int(arg))

                db.servers.remove({"id": int(arg)})

                embed = Embed(
                    title="Success !",
                    description=f"#{channel} has been removed from moderation channels !",
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
            f"Are you sure you want to add channel #{channel} to the list of moderation channels ?"
        )

        try:
            message: Message = await bot.wait_for(
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

        if positive_responses.__contains__(message.content.lower()):
            config["authorized_channels"].append(int(arg))

            db.servers.insert_one({"id": int(arg)})
            embed = Embed(
                title="Success !",
                description=f"#{channel} is now a moderation channel !",
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


@bot.command(aliases=["r"])
async def recommend(ctx, *args):
    maps = readMapsMongo()

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
                genre = is_genre.NAME
            else:
                search = arg

    maps = filterMaps(maps, search=search, rating=rating, genre=genre)
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
            description=f"**▸ Difficulty:** {beatmap['rating']}★ **▸ Genre:** {beatmap['genre']} **▸ Length:** {beatmap['total_length']}s\n**▸ CS:** {beatmap['cs']} **▸ Accuracy:** {beatmap['accuracy']} **▸ AR:** {beatmap['ar']} **▸ HP:** {beatmap['hp']}\n\n[**Download**](https://osu.ppy.sh/d/{beatmap['beatmapset_id']})",
            color=getColor(beatmap["artist"]),
        )
        embed.set_image(
            url=f"https://assets.ppy.sh/beatmaps/{beatmap['beatmapset_id']}/covers/cover@2x.jpg"
        )
        await ctx.send(embed=embed)


@bot.event
async def on_message(message: Message):
    def checkPositiveOrNegative(msg: Message):
        return (
            valid_responses.__contains__(msg.content.lower())
            and msg.author == message.author
        )

    timeout = 30
    embed_timeout = Embed(
        title="Error !",
        description=f"You took too long, bot timeout ! ({timeout}s)",
        color=Color.red(),
    )

    def check(msg: Message):
        return msg.author == message.author

    if message.author == bot.user:
        return

    if message.content.startswith(config["prefix"]):
        await bot.process_commands(message)
        return

    if not config["authorized_channels"].__contains__(message.channel.id):
        return

    if not message.content.startswith("https://osu.ppy.sh/"):
        return

    maps = readMapsMongo()

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

    if not valid_status.__contains__(beatmapset.status.name):
        embed = Embed(
            title="Erreur !",
            description="The beatmap is RANKED, QUALIED ou LOVED !\nPlease try again with another beatmap !",
            color=Color.red(),
        )
        await message.channel.send(embed=embed)
        return

    import_all = False if beatmap is not None else True

    if (len(beatmapset.beatmaps) > 1) and not import_all:
        embed = Embed(
            title="Do you want to add every difficulty of the beatmapset in the database ?",
            description="(yes/no)",
            color=Color.blue(),
        )
        await message.channel.send(embed=embed)

        try:
            msg_import: Message = await bot.wait_for(
                "message", check=checkPositiveOrNegative, timeout=timeout
            )
        except:
            await message.channel.send(embed=embed_timeout)
            return

        if positive_responses.__contains__(msg_import.content.lower()):
            import_all = True

    embed = Embed(
        title=f"Wich genre for the beatmap{'set' if import_all else ''} ?",
        description="(Classic/Tech/Alternate/Speed/Stream)",
        color=Color.blue(),
    )
    await message.channel.send(embed=embed)

    genre = None

    try:
        msg_genre: Message = await bot.wait_for("message", check=check, timeout=timeout)
        genre = getGenre(msg_genre.content)
    except:
        await message.channel.send(embed=embed_timeout)
        return

    if genre is None:
        embed = Embed(
            title="Error !",
            description="Invalid genre ! Please try again !",
            color=Color.red(),
        )
        await message.channel.send(embed=embed)
        return

    genre = genre.NAME

    embed = Embed(
        title=f"Are you sure you want to import{' every difficulty of' if import_all else ''}:",
        description=f"**{beatmapset.artist}**\n**Title:** {beatmapset.title}\n**by:** {getCreator(beatmapset.creator)}\n{f'**Difficulty:** [{beatmap.version}]' if not import_all else ''}\n**With the genre:** {genre}",
        color=Color.greyple(),
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

    if positive_responses.__contains__(msg_recap.content.lower()):
        embed = Embed(
            title=f"Adding beatmap{'set' if import_all else ''} to database...",
            description="Please wait...",
            color=Color.orange(),
        )
        await message.channel.send(embed=embed)

        addBeatmap(message.content, genre, import_all)

        embed = Embed(
            title=f"The beatmap{'set' if import_all else ''} has been added !!",
            description="You can add another one by sending another link !",
            color=Color.green(),
        )
        await message.channel.send(embed=embed)
    else:
        embed = Embed(
            title="Aborted.", description="Aborted by user.", color=Color.red()
        )
        await message.channel.send(embed=embed)


bot.run(getenv("DISCORD_TOKEN"))
