# \/ ----------------Priority's----------------- \/
# TODO: Task: Content Creator Reward System Based on how many subs/videos/viwers/etc someone has (Need OAuth For This Sadly :/)
# TODO: Task: Use Pal Pal's/Stripe's API to create an donate reward system (may not be possible due to identifying)
# TODO: Create a web site for oauth with listed tasks and dashboard for configuring, plus documentation, the website will be called dionysus.nyx.io
# TODO: Update system on different problems the bot is currently experiencing
# TODO: Server voting reward system
# TODO: Add roles based on someons creation or server join date
# TODO: Task system where bot performs a automated action every set day/week/month I.E. purge users from the last 7 days every Monday (Support for conditions?)
# \/ ----------------Supper Less Important Stuff----------------- \/
# TODO: Improve reminder system by using an database and loop through in case the bot goes down use https://discordpy.readthedocs.io/en/latest/ext/tasks/#discord.ext.tasks.Loop for some ways to manage loop
# TODO: Add a command to quickly update to an new counting number

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
bot = commands.Bot(command_prefix=commands.when_mentioned_or('&'), intents=intents)
bot.owner_ids = [508455796783317002, 381694604187009025, 270848136006729728, 222492698236420099, 372923892865433600, 468854398806654976]
bot.active = []
bot.emoji = []
bot.version = '5.21.3'


# loads token and emojis from file
with open("bot/token.json", "r") as set:
    bot.settings = json.load(set)

with open("bot/emojis.json", "r") as unicode:
    emojis = json.load(unicode)
    for key, value in emojis.items():
        bot.emoji.append(value['emoji'])


async def connect():
    bot.db = await asyncpg.create_pool('postgresql://localhost:5432/postgres', user=bot.settings['user'], password=bot.settings['password'], database='database', max_size=100, max_queries=5000, max_inactive_connection_lifetime=200)

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
