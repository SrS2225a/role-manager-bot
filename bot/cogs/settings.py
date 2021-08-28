import datetime
import typing
import re
import discord
from discord.ext import commands
from parsedatetime import Calendar


# administrator commands
def date_convert_seconds(s):
    current, result = Calendar().parse(s)
    t = datetime.datetime(*current[:6])
    futureDate = int((t - datetime.datetime.now()).total_seconds())
    return futureDate + 1, result


class Management(commands.Cog, name='Settings'):
    """[These commands adjust the various settings of the bot](
    https://github.com/SrS2225a/role-manager-bot/wiki/Settings) """

    def __init__(self, bot):
        self.bot = bot

    # I am too lazy to add comments for all of this. The doc strings are pretty self explanatory with what the
    # commands do

    @commands.group(description="""You may also supply position with a channel category to define where the custom channel will be created under if the type is an text channel/voice channel or if as a role to define what role the custom role will be created under. 
    If you want your members to be able to give their custom role/channel to others supply amount with a limit you desire, or 0 to disable the mechanism. 
    If you want the custom role to be deleted from them as soon as they lose the set required role, set removal to true, otherwise set it to false.""",
                    brief="custom role booster placeholder 0 true", invoke_without_command=True, hidden=True)
    @commands.has_permissions(manage_guild=True)
    async def custom(self, ctx):
        """Sets who can create an custom role or channel upon getting the defined role"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @custom.command()
    async def role(self, ctx, role: discord.Role, position: discord.Role, amount: int, remove: bool, *, tag=None):
        """Allows the member to create a custom role"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        role = role.id
        position = position.id
        result = await cursor.fetchval("SELECT role FROM custom WHERE system = $1 and guild = $2", 'role', guild)
        if result is not None:
            await cursor.execute("DELETE FROM custom WHERE system = $1 and guild = $2", 'role', guild)
            await ctx.send("Custom Removed Successfully!")
        else:
            await cursor.execute("INSERT INTO custom(guild, role, position, amount, tag, system, remove) VALUES($1, "
                                 "$2, $3, $4, $5, $6, $7)", guild, role, position, amount, tag, 'role', remove)
            await ctx.send("Custom Set Successfully!")
        await self.bot.db.release(cursor)

    @custom.command()
    async def voice(self, ctx, role: discord.Role, position: discord.CategoryChannel, amount: int, remove: bool, *,
                    tag=None):
        """Allows the member to create a custom voice channel"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        role = role.id
        position = position.id
        result = await cursor.fetchval("SELECT role FROM custom WHERE system = $1 and guild = $2", 'voice', guild)
        if result is not None:
            await cursor.execute("DELETE FROM custom WHERE system = $1 and guild = $2", 'voice', guild)
            await ctx.send("Custom Removed Successfully!")
        else:
            await cursor.execute("INSERT INTO custom(guild, role, position, amount, tag, system, remove) VALUES($1, "
                                 "$2, $3, $4, $5, $6, $7)", guild, role, position, amount, tag, 'voice', remove)
            await ctx.send("Custom Set Successfully!")
        await self.bot.db.release(cursor)

    @custom.command()
    async def text(self, ctx, role: discord.Role, position: discord.CategoryChannel, amount: int, remove: bool, *,
                   tag=None):
        """Allows the member to create a custom text channel"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        role = role.id
        position = position.id
        result = await cursor.fetchval("SELECT role FROM custom WHERE system = $1 and guild = $2", 'text', guild)
        if result is not None:
            await cursor.execute("DELETE FROM custom WHERE system = $1 and guild = $2", 'text', guild)
            await ctx.send("Custom Removed Successfully!")
        else:
            await cursor.execute("INSERT INTO custom(guild, role, position, amount, tag, system, remove) VALUES($1, "
                                 "$2, $3, $4, $5, $6, $7)", guild, role, position, amount, tag, 'text', remove)
            await ctx.send("Custom Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def voicerole(self, ctx, channel: discord.VoiceChannel, role: discord.Role):
        """Sets what role to give and remove depending on the user joining the set voice channel"""
        chan = str(channel.id)
        cursor = await self.bot.db.acquire()
        result = await cursor.fetchval("SELECT role FROM boost WHERE date = $1 and role = $2 and guild = $3 and type "
                                       "= $4", chan, role.id, ctx.guild.id, 'voice')
        if result is not None:
            await cursor.execute("DELETE FROM boost WHERE role = $1 and date = $2 and guild = $3 and type = $4", chan,
                                 role.id, ctx.guild.id, 'voice')
            await ctx.send("Voice Role Deleted Successfully!")
        else:
            await cursor.execute("INSERT INTO boost(guild, role, date, type) VALUES($1, $2, $3, $4)", ctx.guild.id,
                                 role.id, chan, 'voice')
            await ctx.send("Voice Role Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="""Set count to True if you want the bot to edit the channels topic with the new 
    counting number. And role to a role for the role to give upon the user giving a wrong number, passing nothing to 
    the delay arguments disables this behavior""")
    @commands.has_permissions(manage_guild=True)
    async def counter(self, ctx, count: bool, channel: discord.TextChannel, role: discord.Role,
                      delay: int = None):
        """Allows you to set an counting channel"""
        cursor = await self.bot.db.acquire()

        result = await cursor.fetchval("SELECT channel FROM count WHERE guild = $1 and channel = $2 and role = $3",
                                       ctx.guild.id, channel.id, role.id)
        if result is not None:
            await cursor.execute("DELETE FROM count WHERE guild = $1 and channel = $2 and role = $3", ctx.guild.id,
                                 channel.id, role.id)
            await channel.set_permissions(role, overwrite=None)
            await ctx.send("Counting Channel Deleted Successfully!")
        else:
            time = date_convert_seconds(delay) if delay is not None else [0, 1]
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            else:
                await cursor.execute("INSERT INTO count(guild, channel, role, count, delay) VALUES($1, $2, $3, $4, $5)",
                                     ctx.guild.id, channel.id, role.id, count, time[0])
                await channel.set_permissions(role, read_messages=True, send_messages=False)
                await ctx.send("Counting Channel Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.group(invoke_without_command=True, hidden=True,
                    description="To disable applications if they have alreadly preveiously been enabled, remove the "
                                "channel applications been set to",
                    brief="applications question Some Question")
    @commands.has_permissions(manage_guild=True)
    async def application(self, ctx):
        """Lets you set up applications"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @application.command(
        description="You may append `--edit=<number>` at the end to edit a question; number being the question number "
                    "to edit")
    @commands.has_permissions(manage_guild=True)
    async def question(self, ctx, question):
        """Allows you to add a question"""
        cursor = await self.bot.db.acquire()
        result = await cursor.fetch("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id,
                                    'question')
        if re.search("--edit=([0-9])", question):
            value = re.split("--edit=([0-9])", question, 1)
            await cursor.execute("UPDATE questions SET text = $1 WHERE guild = $2 and type = $3 and number = $4",
                                 value[0], ctx.guild.id, 'question', int(value[1]))
            await ctx.send("Question edited successfully!")
        elif question not in [fetch[0] for fetch in result]:
            await cursor.execute("INSERT INTO questions(guild, type, text, number) VALUES($1, $2, $3, $4)",
                                 ctx.guild.id, 'question', question, len(result) + 1)
            await ctx.send("Question set successfully!")
        else:
            await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id,
                                 'question', question)
            await ctx.send("Question removed successfully!")
        await self.bot.db.release(cursor)

    @application.command()
    @commands.has_permissions(manage_guild=True)
    async def give(self, ctx, role: discord.Role):
        """The role to give when a member is accepted for their application"""
        cursor = await self.bot.db.acquire()
        result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'role')
        role = str(role.id)
        if not result == role:
            await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'role',
                                 role)
            await ctx.send("Role set successfully!")
        else:
            await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id,
                                 'role', role)
            await ctx.send("Role removed successfully!")
        await self.bot.db.release(cursor)

    @application.command()
    @commands.has_permissions(manage_guild=True)
    async def require(self, ctx, role: discord.Role):
        """The role needed for a member to create an application"""
        cursor = await self.bot.db.acquire()
        result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'require')
        role = str(role.id)
        if not result == role:
            await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'require',
                                 role)
            await ctx.send("Requirement set successfully!")
        else:
            await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id,
                                 'require', role)
            await ctx.send("Requirement removed successfully!")
        await self.bot.db.release(cursor)

    @application.command()
    @commands.has_permissions(manage_guild=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """The channel to send applicants to"""
        cursor = await self.bot.db.acquire()
        result = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id,
                                       'channel')
        channel = str(channel.id)
        if not result == channel:
            await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'channel',
                                 channel)
            await ctx.send("Channel set successfully!")
        else:
            await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id,
                                 'channel', channel)
            await ctx.send("Channel removed successfully!")
        await self.bot.db.release(cursor)

    @application.command(description='"Congrats! You been accepted."')
    @commands.has_permissions(manage_guild=True)
    async def accept(self, ctx, text):
        """The message to send to the user when their application is accepted"""
        cursor = await self.bot.db.acquire()
        result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'accept')
        if not result == text:
            await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'accept',
                                 text)
            await ctx.send("Acceptance text set successfully!")
        else:
            await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id,
                                 'accept', text)
            await ctx.send("Acceptance text removed successfully!")
        await self.bot.db.release(cursor)

    @application.command(description='Default is "Oh no! You been denied."')
    @commands.has_permissions(manage_guild=True)
    async def deny(self, ctx, text):
        """The message to send to the user when their application is denied"""
        cursor = await self.bot.db.acquire()
        result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'deny')
        if not result == text:
            await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'deny',
                                 text)
            await ctx.send("Acceptance text set successfully!")
        else:
            await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id,
                                 'deny', text)
            await ctx.send("Acceptance text removed successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def suggestion(self, ctx, *, channel: discord.TextChannel):
        """Sets what channel guild suggestions should be sent to"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT suggest FROM settings WHERE suggest = $1 and guild = $2", channel.id,
                                       guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
        if result is not None:
            await cursor.execute("UPDATE settings SET suggest = NULL WHERE guild = $1", guild)
            await ctx.send("Suggestions Channel Successfully Removed!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(guild, suggest) VALUES($1, $2)", guild, channel.id)
            await ctx.send("Suggestions Channel Set Successfully!")
        else:
            await cursor.execute("UPDATE settings SET suggest = $1 WHERE guild = $2", channel.id, guild)
            await ctx.send("Suggestions Channel Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def livestream(self, ctx, *, role: discord.Role):
        """Allows you to set what role to give when someone is streaming or live"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT live FROM settings WHERE live = $1 and guild = $2", role.id, guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
        if result is not None:
            cursor.execute("UPDATE settings SET announce = NULL WHERE guild = $1", guild)
            await ctx.send("Announcement Channel Disabled Successfully!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(guild, live) VALUES($1, $2)", guild, role.id)
            await ctx.send("Announcement Channel Enabled Successfully!")
        else:
            await cursor.execute("UPDATE settings SET live = $1 WHERE guild = $2", role.id, guild)
            await ctx.send("Announcement Channel Enabled Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def booster(self, ctx, day: int, *, role: discord.Role):
        """Allows you to set an booster reward based on how long a booster boosted for"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        rolemaster = role.id
        result = await cursor.fetchval(
            "SELECT role FROM boost WHERE date::int8 = $1 and role = $2 and guild = $3 and type = $4", day, rolemaster,
            guild, 'boost')
        if result is None:
            await cursor.execute(f"INSERT INTO boost(guild, date, role, type) VALUES($1, $2::int8, $3, $4)", guild, day,
                                 rolemaster, 'boost')
            await ctx.send("Booster Reward Set Successfully!")
        else:
            await cursor.execute(f"DELETE FROM boost WHERE role = $1 and date::int8 = $2 and guild = $3 and type = $4",
                                 day, rolemaster, guild, 'boost')
            await ctx.send("Booster Reward Deleted Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def inviter(self, ctx, amount: int, *, role: discord.Role):
        """Allows you to set an invite reward based on how many users were invited by the inviter"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        rolemaster = role.id
        result = await cursor.fetchval(
            "SELECT role FROM boost WHERE date = $1 and role = $2 and guild = $3 and type = $4", str(amount),
            rolemaster, guild, 'invite')
        if result is None:
            await cursor.execute("INSERT INTO boost(guild, date, role, type) VALUES($1, $2, $3, $4)", guild,
                                 str(amount), rolemaster, 'invite')
            await ctx.send("Inviter Reward Set Successfully!")
        else:
            await cursor.execute("DELETE FROM boost WHERE role = $1 and date = $2 and guild = $3 and type = $4",
                                 rolemaster, str(amount), guild, 'invite')
            await ctx.send("Inviter Reward Deleted Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def overwrite(self, ctx, channel: discord.TextChannel, role: discord.Role):
        """Sets if defined channel overwrites be given back if the member rejoins by a set role for selected channel"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        result = await cursor.fetchval(
            "SELECT role FROM roles WHERE role = $1 and member = $2 and guild = $3 and type = $4", role.id, channel.id,
            guild.id, 'recover')
        if result is not None:
            await cursor.execute("DELETE FROM roles WHERE guild = $1 and member = $2 and role = $3 and type = $4",
                                 guild.id, channel.id, role.id, 'recover')
            await ctx.send("Overwrites Recovery Set Successfully!")
        else:
            await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guild.id,
                                 channel.id, role.id, 'recover')
            await ctx.send("Overwrites Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def lookback(self, ctx, days):
        """Allows you to set how many days to lookback for the graph command (default is 30)"""
        cursor = await self.bot.db.acquire()

        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", ctx.guild.id)
        time = date_convert_seconds(days)
        if time[0] > 120:
            await ctx.send("The lookback cannot be more than 120 days!")
        elif time[0] == 1:
            await ctx.send("The lookback must be at least greater than 1 day!")
        elif time[1] < 1:
            await ctx.send("I do not recognise that time!")
        else:
            if search is None:
                await cursor.execute("INSERT INTO settings(guild, lookback) VALUES($1, $2)", ctx.guild.id, time[0])
                await ctx.send("Lookback Set Successfully!")
            else:
                await cursor.execute("UPDATE settings SET lookback = $1 WHERE guild = $2", time[0], ctx.guild.id)
                await ctx.send("Lookback Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def announce(self, ctx, channel: discord.TextChannel):
        """Sets what channel broadcast messages should be sent to"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT announce FROM settings WHERE announce = $1 and guild = $2", channel.id,
                                       guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
        if result is not None:
            await cursor.execute("UPDATE settings SET announce = NULL WHERE guild = $1", guild)
            await ctx.send("Announcement Channel Disabled Successfully!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(guild, announce) VALUES($1, $2)", guild, channel.id)
            await ctx.send("Announcement Channel Enabled Successfully!")
        else:
            await cursor.execute("UPDATE settings SET announce = $1 WHERE guild = $2", channel.id, guild)
            await ctx.send("Announcement Channel Enabled Successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="""The following flags are supported:
`staff` - If the user is a Discord Employee
`partner` - If the user is a Discord Partner
`hypesquad` - If the user is a HypeSquad Events Member
`bug_hunter` - If the user is a Bug Hunter
`hypesquad_bravery` - If the user is a HypeSquad Bravery member
`hypesquad_brillince` - If the user is a HypeSquad Brillince member
`hypesquad_balance` - If the user is a HypeSquad Balance member
`early_supporter` - If the user is a Early Suporter
`system` - If the user is a system user (i.e. represents Discord officially)
`bug_hunter_level_2` - If the user is a Bug Hunter Level 2
`verified_bot` - If the user is a verified bot
`verified_bot_developer` - If the user is a Early Verified Bot Developer """, brief="flags staff Discord Employee")
    @commands.has_permissions(manage_guild=True)
    async def flag(self, ctx, flag, *, role: discord.Role):
        """Allows you to set what role to give automatically depending on what flags the user has"""
        cursor = await self.bot.db.acquire()
        if flag in (
        'staff', 'partner', 'hypesquad', 'bug_hunter', 'hypesquad_bravery', 'hypesquad_brilliance', 'hypesquad_balance',
        'early_supporter', 'team_user', 'system', 'bug_hunter_level_2', 'verified_bot', 'verified_bot_developer'):
            guild = ctx.guild.id
            result = await cursor.fetchval(
                "SELECT role FROM boost WHERE role = $1 and date = $2 and guild = $3 and type = $4", role.id, flag,
                guild, 'flag')
            if result is None:
                await cursor.execute("INSERT INTO boost(guild, role, date, type) VALUES($1, $2, $3, $4)", guild,
                                     role.id, flag, 'flag')
                await ctx.send("Flags Role Set Successfully!")
            else:
                await cursor.execute("DELETE FROM boost WHERE role = $1 and guild = $2 and date = $3 and type = $4",
                                     role.id, guild, flag, 'flag')
                await ctx.send("Flags Role Deleted Successfully!")
        else:
            await ctx.send(
                "The flag must be defined as 'staff', 'partner', 'hypesquad', 'bug_hunter', 'hypesquad_bravery', "
                "'hypesquad_brilliance', 'hypesquad_balance', 'early_supporter', 'team_user', 'system', "
                "'bug_hunter_level_2', 'verified_bot', or 'verified_bot_developer'")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def partnership(self, ctx, channel: discord.TextChannel, role: discord.Role, reward: discord.Role = None,
                          amount: int = None):
        """Allows you to set an partnership reward based on how many partnerships were completed"""
        cursor = await self.bot.db.acquire()
        role = role.id
        channel = channel.id
        check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and type = $3",
                                      ctx.guild.id, 'partners', channel)
        reward = 0 if reward is None else reward.id
        amount = 0 if amount is None else amount
        if check is not None:
            await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id,
                                 'partners', channel)
            await ctx.send("Partner Requirement Deleted Successfully!")
        else:
            await cursor.execute(
                f"INSERT INTO leveling(guild, system, level, difficulty, type, role) VALUES($1, $2, $3, $4, $5, $6)",
                ctx.guild.id, 'partners', amount, reward, channel, role)
            await ctx.send("Partner Requirement Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.group(invoke_without_command=True, hidden=True, brief="leveling ranking 5 Level 5")
    @commands.has_permissions(manage_guild=True)
    async def leveling(self, ctx):
        """Allows you to set up server leveling"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @leveling.command()
    @commands.has_permissions(manage_guild=True)
    async def blacklist(self, ctx, main: typing.Union[discord.TextChannel, discord.Role, discord.VoiceChannel]):
        """Adds what channel or role cannot level up from"""
        cursor = await self.bot.db.acquire()
        if isinstance(main, discord.TextChannel) or isinstance(main, discord.VoiceChannel) or isinstance(main,
                                                                                                         discord.Role):
            check = await cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3",
                                          ctx.guild.id, 'blacklist', main.id)
            if check is not None:
                await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3",
                                     ctx.guild.id, 'blacklist', main.id)
                await ctx.send(f"Blacklist Deleted Successfully!")
            else:
                await cursor.execute("INSERT INTO leveling(guild, system, role) VALUES($1, $2, $3)", ctx.guild.id,
                                     'blacklist', main.id)
                await ctx.send(f"Blacklist Set Successfully!")
        await self.bot.db.release(cursor)

    @leveling.command()
    @commands.has_permissions(manage_guild=True)
    async def multiplier(self, ctx, main: typing.Union[discord.TextChannel, discord.Role, discord.VoiceChannel, str],
                         value: int):
        """Sets what channel or role should gain extra XP"""
        cursor = await self.bot.db.acquire()
        if isinstance(main, discord.TextChannel) or isinstance(main, discord.VoiceChannel) or isinstance(main,
                                                                                                         discord.Role):
            check = await cursor.fetchval(
                "SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4",
                ctx.guild.id, 'multiplier', main.id, value)
            if check is not None:
                await cursor.execute(
                    "DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4",
                    ctx.guild.id, 'multiplier', main.id, value)
                await ctx.send(f"Multiplier Deleted Successfully!")
            else:
                await cursor.execute("INSERT INTO leveling(guild, system, role, difficulty) VALUES($1, $2, $3, $4)",
                                     ctx.guild.id, 'multiplier', main.id, value)
                await ctx.send(f"Multiplier Set Successfully!")
        await self.bot.db.release(cursor)

    @leveling.command(
        description="You can optionally set main as `difficulty` to set how hard it is to level up, and `message` for "
                    "the message weight or `voice` for the voice weight")
    @commands.has_permissions(manage_guild=True)
    async def weight(self, ctx, main, value: int):
        """Sets how much XP should be weighted"""
        cursor = await self.bot.db.acquire()
        if main in ('message', 'voice', 'difficulty'):
            check = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2",
                                          ctx.guild.id, main)
            if check is not None:
                await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, main)
                await ctx.send(f"{main} Weight Deleted Successfully!")
            else:
                await cursor.execute("INSERT INTO leveling(guild, system, difficulty) VALUES($1, $2, $3)", ctx.guild.id,
                                     main, value)
                await ctx.send(f"{main} Weight Set Successfully!")
        else:
            await ctx.send("'main' must be defined as message, voice, or difficulty")
        await self.bot.db.release(cursor)

    @leveling.command(
        description="You can set main to `keep` for level roles behavior or `clear` for user levels behavior")
    @commands.has_permissions(manage_guild=True)
    async def behavior(self, ctx, main, value: bool):
        """Sets if level roles should "stack" on each other and/or delete the users levels upon leaving the guild."""
        cursor = await self.bot.db.acquire()
        if main in ("keep", "clear") and isinstance(value, bool):
            check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and type = $3",
                                          ctx.guild.id, main, value)
            if check is not None:
                await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and type = $3",
                                     ctx.guild.id, main, value)
                await ctx.send(f"{main} Deleted Successfully!")
            else:
                await cursor.execute("INSERT INTO leveling(guild, system, type) VALUES($1, $2, $3)", ctx.guild.id, main,
                                     value)
                await ctx.send(f"{main} Set Successfully!")
        else:
            ctx.send("'main' must be defined as keep or clear")
        await self.bot.db.release(cursor)

    @leveling.command()
    @commands.has_permissions(manage_guild=True)
    async def ranking(self, ctx, main: discord.Role, value: int):
        """Sets a level role"""
        cursor = await self.bot.db.acquire()
        if isinstance(main, discord.Role):
            check = await cursor.fetchval(
                "SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4", ctx.guild.id,
                'levels', main.id, value)
            if check is not None:
                await cursor.execute(
                    "DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4", ctx.guild.id,
                    'levels', main.id, value)
                await ctx.send("Levels Deleted Successfully!")
            else:
                await cursor.execute("INSERT INTO leveling(guild, system, role, level) VALUES($1, $2, $3, $4)",
                                     ctx.guild.id, 'levels', main.id, value)
                await ctx.send("Levels Set Successfully!")
        await self.bot.db.release(cursor)

    @leveling.command()
    @commands.has_permissions(manage_guild=True)
    async def top(self, ctx, main, value: discord.Role):
        """Allows you to add support for member of the day, week, or month"""
        cursor = await self.bot.db.acquire()
        if main in ('day', 'week', 'year'):
            check = cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and system = $2 and type = $3",
                                    ctx.guild.id, 'top', main)
            if check is not None:
                await cursor.execute(
                    "DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and type = $4", ctx.guild.id,
                    'top', value, main)
                await ctx.send(f"{main} Deleted Successfully!")
            else:
                await cursor.execute("INSERT INTO leveling(guild, system, role, type) VALUES($1, $2, $3, $4)",
                                     ctx.guild.id, 'top', value, main)
                await ctx.send(f"{main} Set Successfully!")
        else:
            await ctx.send("'main' must be defied as day, week, or year")

        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Management(bot))
