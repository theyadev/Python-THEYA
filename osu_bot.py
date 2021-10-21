from osu_irc import *
from os import getenv
from dotenv import load_dotenv
import shlex
from main import (
    getRandomMap,
    filterMapsFromArgs
)
import math
from threading import Timer
from time import sleep

load_dotenv()

USERNAME = getenv('OSU_IRC_USERNAME')
PASSWORD = getenv('OSU_IRC_PASSWORD')

PREFIX = "!"

COOLDOWN_SECONDS = 10

cooldown = []
cooldown_general = []


def mapLength(nombre):
    heures = math.floor(nombre / 60 / 60)
    minutes = math.floor(nombre / 60) - (heures * 60)
    secondes = nombre % 60
    duree = str(minutes).zfill(2) + ':' + str(secondes).zfill(2)
    return duree


def mapRating(nombre):
    starRating = nombre * 100
    starRating = round(starRating)
    starRating = starRating / 100
    return starRating


def removeCooldown(*author):
    author = "".join(author)
    cooldown.remove(author)
    try:
        cooldown_general.remove(author)
    except ValueError:
        pass
    return


class MyBot(Client):

    async def recommendMaps(self, message, args, nb=1):
        maps, genre, rating, search = filterMapsFromArgs(args)

        maps = getRandomMap(maps, nb)

        if maps is None:
            message.reply("There is not maps with theses criterias !")
            return

        for beatmap in maps:
            await message.reply(cls=self, reply=f"[https://osu.ppy.sh/b/{beatmap['id']} {beatmap['artist']} - {beatmap['title']} [{beatmap['version']}]] | {beatmap['genre']} | {mapRating(beatmap['rating'])} ★ | {mapLength(beatmap['total_length'])} ♪")

        return

    async def messageCooldown(self, message, cooldown_time):
        if cooldown.__contains__(message.Author.name):
            if cooldown_general.__contains__(message.Author.name):
                return
            cooldown_general.append(message.Author.name)
            await message.reply(cls=self, reply=f'Vous devez attendre {cooldown_time} secondes avant de pouvoir refaire une commande.')
            return

    async def onReady(self):
        print('Le bot est lancé !')
        # do something

    async def onMessage(self, message: Message):
        if not message.content.startswith(PREFIX):
            return

        msg = message.content[1:]
        args = shlex.split(msg)
        command = args.pop(0).lower()

        if command == "r" or command == "recommend":
            command_cooldown = 10

            await self.messageCooldown(message, command_cooldown)

            print(f"{message.Author.name} - recommend: {args}")

            await self.recommendMaps(message, args)

            cooldown.append(message.Author.name)

            Timer(float(command_cooldown), removeCooldown,
                  (message.Author.name)).start()

            return

        if command == "bomb":
            command_cooldown = 15

            await self.messageCooldown(message, command_cooldown)

            print(f"{message.Author.name} - bomb: {args}")

            await self.recommendMaps(message, args, 3)

            cooldown.append(message.Author.name)

            Timer(float(command_cooldown), removeCooldown,
                  (message.Author.name)).start()

            return

        if command == "help":
            command_cooldown = 20

            await self.messageCooldown(message, command_cooldown)

            print(f"{message.Author.name} - help: {args}")

            await message.reply(cls=self, reply='Filters: "artist/title" genre rating')
            sleep(0.5)
            await message.reply(cls=self, reply='!recommend (!r) [filters] = recommend an osu! beatmap.')
            sleep(0.5)
            await message.reply(cls=self, reply='!bomb [filters] = recommend 5 maps.')
            sleep(0.5)
            await message.reply(cls=self, reply='Command example: !r "Camellia feat. Nanahira" Tech')

            cooldown.append(message.Author.name)

            Timer(float(command_cooldown), removeCooldown,
                  (message.Author.name)).start()

            return

        # do more with your code


MyBot(token=PASSWORD, nickname=USERNAME).run()
