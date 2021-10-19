import json
from discord.ext import commands
from os import getenv
from discord.ext.commands.context import Context
from discord.message import Message
from dotenv import load_dotenv
from main import readMapsMongo, getRandomMap, filterMaps, getGenre
load_dotenv()

prefix = "$"

config = {}

with open("./discord_config.json", "r", encoding="utf-8") as config_file:
    config_json = json.load(config_file)
    config.update(config_json)

bot = commands.Bot(command_prefix=prefix)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.command()
async def setChannel(ctx: Context, arg:str):
    if arg.isnumeric():
        channel = bot.get_channel(int(arg))
        
        await ctx.send(f"Voulez-vous vraiment ajouter le channel #{channel} à la liste des channels de modération ?")
    
        positive_responses = ['oui', "o", "yes", "y"]
        negative_responses = ['non', "n", "no"]

        valid_responses = positive_responses + negative_responses

        def check(message:Message):
            return valid_responses.__contains__(message.content.lower()) and message.author == ctx.author

        message: Message = await bot.wait_for("message", check=check)

        if positive_responses.__contains__(message.content.lower()):
            config['authorized_channels'].append(int(arg))
            with open("./discord_config.json", "w", encoding="utf-8") as config_file:
                json.dump(config, config_file, ensure_ascii=False, indent=4)
                
            await ctx.send(f"Le channel #{channel} à bien été ajouté !")


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
async def on_message(message: Message):
    if not message.content.startswith(prefix):
        print(message.channel.id)

    await bot.process_commands(message)

bot.run(getenv("DISCORD_TOKEN"))
