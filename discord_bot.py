import discord
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv
from main import readMapsMongo,getRandomMap,filterMaps,getGenre
load_dotenv()

prefix = "$"

bot = commands.Bot(command_prefix=prefix)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.command()
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

    for beatmap in maps:
        await ctx.send(f"{beatmap['artist']} - {beatmap['title']} [{beatmap['version']}] {beatmap['rating']}* | {beatmap['genre']}")
    
@bot.event
async def on_message(message):
    if not message.content.startswith(prefix):
        print(message.content)

    await bot.process_commands(message)

bot.run(getenv("DISCORD_TOKEN"))