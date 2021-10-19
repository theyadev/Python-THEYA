import json
from discord import Embed, Color
from discord.ext import commands
from os import getenv
from discord.ext.commands.context import Context
from discord.message import Message
from dotenv import load_dotenv
from main import readMapsMongo, getRandomMap, filterMaps, getGenre, linkParser, getBeatmapInfo, addBeatmap
load_dotenv()

prefix = "$"

config = {}

with open("./discord_config.json", "r", encoding="utf-8") as config_file:
    config_json = json.load(config_file)
    config.update(config_json)

bot = commands.Bot(command_prefix=prefix)

positive_responses = ['oui', "o", "yes", "y"]
negative_responses = ['non', "n", "no"]

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
    print('We have logged in as {0.user}'.format(bot))


@bot.command()
async def setChannel(ctx: Context, arg: str):
    if arg.isnumeric():
        def checkPositiveOrNegative(message: Message):
            return valid_responses.__contains__(message.content.lower()) and message.author == ctx.author

        channel = bot.get_channel(int(arg))

        if config["authorized_channels"].__contains__(int(arg)):
            await ctx.send("Le channel est deja dans la liste, voulez vous le retirer ?")

            try:
                message: Message = await bot.wait_for("message", check=checkPositiveOrNegative, timeout=15)
            except:
                await ctx.send('Vous avez mis trop de temps, tache annulé !')
                return

            if positive_responses.__contains__(message.content.lower()):
                config['authorized_channels'].remove(int(arg))

                with open("./discord_config.json", "w", encoding="utf-8") as config_file:
                    json.dump(config, config_file,
                              ensure_ascii=False, indent=4)

                await ctx.send(f"Le channel #{channel} à bien été retiré !")
            else:
                await ctx.send(f"D'accord, je ne fais rien !")

            return

        await ctx.send(f"Voulez-vous vraiment ajouter le channel #{channel} à la liste des channels de modération ?")

        try:
            message: Message = await bot.wait_for("message", check=checkPositiveOrNegative, timeout=15)
        except:
            await ctx.send('Vous avez mis trop de temps, tache annulé !')
            return

        if positive_responses.__contains__(message.content.lower()):
            config['authorized_channels'].append(int(arg))

            with open("./discord_config.json", "w", encoding="utf-8") as config_file:
                json.dump(config, config_file, ensure_ascii=False, indent=4)

            await ctx.send(f"Le channel #{channel} à bien été ajouté !")
        else:
            await ctx.send(f"Tache annulé !")


@bot.command(aliases=['r'])
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
        embed = Embed(title=f"{beatmap['artist']} - {beatmap['title']} by {beatmap['creator']} [{beatmap['version']}]", url=f"https://osu.ppy.sh/b/{beatmap['id']}",
                      description=f"**▸ Difficulty:** {beatmap['rating']}★ **▸ Genre:** {beatmap['genre']} **▸ Length:** {beatmap['total_length']}s\n**▸ CS:** {beatmap['cs']} **▸ Accuracy:** {beatmap['accuracy']} **▸ AR:** {beatmap['ar']} **▸ HP:** {beatmap['hp']}\n\n[**Download**](https://osu.ppy.sh/d/{beatmap['beatmapset_id']})", color=getColor(beatmap['artist']))
        embed.set_image(
            url=f"https://assets.ppy.sh/beatmaps/{beatmap['beatmapset_id']}/covers/cover.jpg")
        await ctx.send(embed=embed)


@bot.event
async def on_message(message: Message):
    def checkPositiveOrNegative(msg: Message):
        return valid_responses.__contains__(msg.content.lower()) and msg.author == message.author

    timeout = 30

    def check(msg: Message):
        return msg.author == message.author

    if message.author == bot.user:
        return

    if message.content.startswith(prefix):
        await bot.process_commands(message)
        return

    if not config["authorized_channels"].__contains__(message.channel.id):
        return

    if not message.content.startswith('https://osu.ppy.sh/'):
        return

    maps = readMapsMongo()

    beatmapset_id, beatmap_id = linkParser(message.content)

    if beatmapset_id is None and beatmap_id is None:
        await message.channel.send("Lien invalide !")
        return

    if any(beatmap["id"] == beatmap_id for beatmap in maps):
        # Check if beatmap_id already exist in maps
        await message.channel.send("La beatmap existe déja dans le bot !")
        return

    beatmapset, beatmap = getBeatmapInfo(beatmapset_id, beatmap_id)

    if beatmap:
        if beatmap.mode.name != "STD":
            await message.channel.send("Ce n'est pas une map Standard !")
            return

    await message.channel.send("Quel genre ?")

    genre = None

    try:
        msg_genre: Message = await bot.wait_for("message", check=check, timeout=timeout)
        genre = getGenre(msg_genre.content)
    except:
        await message.channel.send('Vous avez mis trop de temps, tache annulé !')
        return

    if genre is None:
        await message.channel.send("Le genre est invalide ! Veuillez recommencer l'importation !")
        return

    genre = genre.NAME

    import_all = False if beatmap is not None else True

    if (len(beatmapset.beatmaps) > 1):
        await message.channel.send(f"Est-ce que tu veux importer toute les difficultées ?")

        try:
            msg_import: Message = await bot.wait_for("message", check=checkPositiveOrNegative, timeout=timeout)
        except:
            await message.channel.send('Vous avez mis trop de temps, tache annulé !')
            return

        if positive_responses.__contains__(msg_import.content.lower()):
            import_all = True

    await message.channel.send(f"Est-tu sur de vouloir importer {beatmapset.artist} - {beatmapset.title} {f'[{beatmap.version}]' if not import_all else ''} avec le genre {genre} ?")

    try:
        msg_recap: Message = await bot.wait_for("message", check=checkPositiveOrNegative, timeout=timeout)
    except:
        await message.channel.send('Vous avez mis trop de temps, tache annulé !')
        return

    if positive_responses.__contains__(msg_recap.content.lower()):
        addBeatmap(message.content, genre, import_all)
        await message.channel.send("La map à correctement été ajouté !")
    else:
        await message.channel.send("D'accord ! Annulation...")


bot.run(getenv("DISCORD_TOKEN"))
