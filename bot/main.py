import asyncio

import asyncpg
import discord

from discord.ext import commands
import logging
import json
import os

print("Initalizing and connecting to discord!")


# represents a connection to Discord
async def __init__(self, bot):
    self.bot = bot


# loads token/database credentials and emojis from file
with open("token.json", "r") as set:
    settings = json.load(set)

# connects to database
db = asyncio.get_event_loop().run_until_complete(
    asyncpg.create_pool('postgresql://localhost:5432/postgres', user=settings['user'], password=settings['password'],
                        max_size=800, max_queries=100, max_cacheable_statement_size=0))


# gets custom command prefix or default one
async def get_prefix(bot, message):
    async with db.acquire() as cursor:
        prefix = '*'
        if message.guild:
            pre = await cursor.prepare("SELECT auth FROM settings WHERE guild = $1 LIMIT 1")
            prefix = await pre.fetchval(message.guild.id) or prefix
        return commands.when_mentioned_or(prefix)(bot, message)

# sets discord gateway intents
intents = discord.Intents.default()
intents.members = True
intents.presences = False
intents.messages = True
intents.webhooks = False
intents.integrations = False
intents.bans = False
intents.typing = False

# initializes bot vars to be used elsewhere
bot = commands.Bot(command_prefix=get_prefix, intents=intents, case_insensitive=True)
bot.owner_ids = [508455796783317002, 270848136006729728, 222492698236420099, 372923892865433600]
bot.active = []
bot.emoji = []
bot.db = db

# loads emojis from file
with open("emojis.json", "r") as unicode:
    emojis = json.load(unicode)
    for key, value in emojis.items():
        bot.emoji.append(value['emoji'])


# checks if an command has been run in a dm
@bot.check
async def predicate(ctx):
    if ctx.guild is None:
        raise commands.NoPrivateMessage
    return commands.check(predicate)


# checks if a guild has enabled or disabled a command
@bot.check
async def bot_check(ctx):
    async with db.acquire() as cursor:
        name = await cursor.prepare("SELECT date FROM boost WHERE guild = $1 and date = $2 and type = $3 LIMIT 1")
        name = await name.fetchval(ctx.guild.id, ctx.command.name, 'command')
        if name is None or ctx.command.parent:
            return True
        else:
            # raise if the command is disabled
            raise commands.DisabledCommand(f"{ctx.command.name} command is disabled.")


_cd = commands.CooldownMapping.from_cooldown(1.0, 5.0, commands.BucketType.member) # from ?tag cooldown mapping

# Then apply a bot check that will run before every command
# Very similar to ?tag cooldown mapping but in Bot scope instead of Cog scope
@bot.check
async def cooldown_check(ctx):
    bucket = _cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after)
    return True

# loads cogs
bot.load_extension("jishaku")
for cogs in os.listdir('./cogs'):
    if cogs.endswith('.py'):
        bot.load_extension(f'cogs.{cogs[:-3]}')

# log all actions happening with bot
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(handler)

bot.run(settings['token'])  # runs bot
