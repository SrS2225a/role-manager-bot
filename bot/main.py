
import asyncio

import asyncpg
import discord

from discord.ext import commands
import logging
import json
import os


# represents a connection to Discord
async def __init__(self, bot):
    self.bot = bot

# sets bots command prefix and bot variables
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.invites = False
intents.webhooks = False
intents.integrations = False
intents.emojis = False
intents.bans = False
bot = commands.Bot(command_prefix=commands.when_mentioned_or('*'), intents=intents)
bot.owner_ids = [508455796783317002, 381694604187009025, 270848136006729728, 222492698236420099, 372923892865433600, 468854398806654976]
bot.active = []
bot.emoji = []
bot.version = '5.20.1'


# loads token and emojis from file
with open("bot/token.json", "r") as set:
    bot.settings = json.load(set)

with open("bot/emojis.json", "r") as unicode:
    emojis = json.load(unicode)
    for key, value in emojis.items():
        bot.emoji.append(value['emoji'])


async def connect():
    bot.db = await asyncpg.create_pool('postgresql://localhost:5432/postgres', user=bot.settings['user'], password=bot.settings['password'], database='database', command_timeout=12)

asyncio.get_event_loop().run_until_complete(connect())


# log all actions happening with bot
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(handler)


# checks if an command has been run in a dm
@bot.check
async def predicate(ctx):
    if ctx.guild is None:
        raise commands.NoPrivateMessage
    return commands.check(predicate)


# loads cogs
bot.load_extension("jishaku")
for cogs in os.listdir('bot/./cogs'):
    if cogs.endswith('.py'):
        bot.load_extension(f'cogs.{cogs[:-3]}')

bot.token = bot.settings['token']

bot.run(bot.token)  # runs bot