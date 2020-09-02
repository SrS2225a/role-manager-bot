# \/ ----------------Priority's----------------- \/
# TODO: NSFW Commands (Maybe)
# TODO: Automatic topic changer (Maybe)
# TODO: Staff Applications Feature (Maybe)
# TODO: Ticket system (Maybe)
# TODO: Custom Embed Creator
# TODO: Task: Content Creator Reward System Based on how many subs/videos/viwers/etc someone has (Need OAuth For This Sadly :/)
# TODO: Task: Use Pal Pal's/Stripe's API to create an donate reward system (may not be possible due to identifying)
# TODO: Improve reminder system by using an database and loop through in case the bot goes down use https://discordpy.readthedocs.io/en/latest/ext/tasks/#discord.ext.tasks.Loop for some ways to manage loop
# TODO: Task system where bot performs a automated action every set day/week/month I.E. purge users from the last 7 days every Monday
# \/ ----------------Supper Less Important Stuff----------------- \/

import asyncio

import asyncpg

from discord.ext import commands
import logging
import json
import os


# represents a connection to Discord
async def __init__(self, bot):
    self.bot = bot

# sets bots command prefix and bot variables
bot = commands.Bot(command_prefix=commands.when_mentioned_or('*'))
bot.active = []
bot.emoji = []
bot.version = '5.17.7'
bot.remove_command('help')


# loads token and emojis from file
with open("token.json", "r") as set:
    settings = json.load(set)

with open("emojis.json", "r") as unicode:
    emojis = json.load(unicode)
    for key, value in emojis.items():
        bot.emoji.append(value['emoji'])


# connects to database
async def connect():
    bot.db = await asyncpg.create_pool('postgresql://localhost:5432/postgres', user=settings['user'], password=settings['password'], database='database')

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
for cogs in os.listdir('./cogs'):
    if cogs.endswith('.py'):
        bot.load_extension(f'cogs.{cogs[:-3]}')

bot.token = settings['token']

bot.run(bot.token)  # runs bot
