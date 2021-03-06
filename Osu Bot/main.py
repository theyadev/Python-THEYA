import shlex
import sys

from osu_irc import *

from os import getenv
from dotenv import load_dotenv

from threading import Timer

from time import sleep

sys.path.append("../")

from Classes.Connexions import Connexions

from filters import *
from utilities import formatMapLength
from getRandomMap import getRandomMap

load_dotenv()

USERNAME = getenv('OSU_IRC_USERNAME')
PASSWORD = getenv('OSU_IRC_PASSWORD')

PREFIX = "!"

COOLDOWN_SECONDS = 10

API = Connexions()

cooldown = []
cooldown_general = []


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
        maps = API.readDatabse("maps")

        maps = filterMapsFromArgs(maps, args)[0]

        maps = getRandomMap(maps, nb)

        if maps is None:
            message.reply("There is not maps with theses criterias !")
            return

        for beatmap in maps:
            await message.reply(cls=self, reply=f"[https://osu.ppy.sh/b/{beatmap['id']} {beatmap['artist']} - {beatmap['title']} [{beatmap['version']}]] | {beatmap['genre']} | {mapRating(beatmap['rating'])} ★ | {formatMapLength(beatmap['total_length'])} ♪")

        return

    async def messageCooldown(self, message, cooldown_time):
        if cooldown.__contains__(message.Author.name):
            if cooldown_general.__contains__(message.Author.name):
                return True
            cooldown_general.append(message.Author.name)
            await message.reply(cls=self, reply=f'You must wait {cooldown_time} seconds before doing another command.')
            return True

        return False

    async def onReady(self):
        print('Le bot est lancé !')

    async def onMessage(self, message: Message):
        if not message.content.startswith(PREFIX):
            return

        msg = message.content[1:]
        args = shlex.split(msg)
        command = args.pop(0).lower()

        if command == "r" or command == "recommend":
            command_cooldown = 10

            if await self.messageCooldown(message, command_cooldown):
                return

            print(f"{message.Author.name} - recommend: {args}")

            await self.recommendMaps(message, args)

            cooldown.append(message.Author.name)

            Timer(float(command_cooldown), removeCooldown,
                  (message.Author.name)).start()

            return

        if command == "bomb":
            command_cooldown = 15

            if await self.messageCooldown(message, command_cooldown):
                return

            print(f"{message.Author.name} - bomb: {args}")

            await self.recommendMaps(message, args, 3)

            cooldown.append(message.Author.name)

            Timer(float(command_cooldown), removeCooldown,
                  (message.Author.name)).start()

            return

        if command == "help":
            command_cooldown = 20

            if await self.messageCooldown(message, command_cooldown):
                return

            print(f"{message.Author.name} - help")

            await message.reply(cls=self, reply='Filters: "artist/title" genre rating')
            sleep(0.5)
            await message.reply(cls=self, reply='!discord: Show Discord link')
            sleep(0.5)
            await message.reply(cls=self, reply='!recommend (!r) [filters] = Recommend an osu! beatmap.')
            sleep(0.5)
            await message.reply(cls=self, reply='!bomb [filters] = Recommend 3 beatmaps.')
            sleep(0.5)
            await message.reply(cls=self, reply='Command example: !r "Camellia feat. Nanahira" Tech')

            cooldown.append(message.Author.name)

            Timer(float(command_cooldown), removeCooldown,
                  (message.Author.name)).start()

            return

        if command == "discord":
            command_cooldown = 10

            if await self.messageCooldown(message, command_cooldown):
                return

            print(f"{message.Author.name} - discord")

            await message.reply(cls=self, reply='[https://discord.gg/bUsRruH Click here to join the Discord !]')

            cooldown.append(message.Author.name)

            Timer(float(command_cooldown), removeCooldown,
                  (message.Author.name)).start()

            return

        if command == "maps":
            command_cooldown = 10

            if await self.messageCooldown(message, command_cooldown):
                return

            print(f"{message.Author.name} - maps: {args}")

            maps, genre, rating, search = filterMapsFromArgs(args)

            await message.reply(cls=self, reply=f"There are {len(maps)} maps{' with:' if search or genre or rating else ' !'}{' ' + search if search else ''}{' ' + str(rating) + '★' if rating else ''}{' ' + genre if genre else ''}")

            cooldown.append(message.Author.name)

            Timer(float(command_cooldown), removeCooldown,
                  (message.Author.name)).start()

            return

        # do more with your code


MyBot(token=PASSWORD, nickname=USERNAME).run()
