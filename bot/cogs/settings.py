import datetime
import argparse
import typing
import re
import discord
from discord.ext import commands
from parsedatetime import Calendar


# administrator commands
class Management(commands.Cog, name='Settings'):
    """[These commands adjust the various settings of the bot](https://github.com/SrS2225a/role-manager-bot/wiki/Settings)"""
    def __init__(self, bot):
        self.bot = bot
        
    # I am too lazy to add comments for all of this. The doc strings are pretty self explanitory with what the commmands do

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def custom(self, ctx, type, role: discord.Role, position: typing.Union[discord.Role, discord.CategoryChannel], amount: int, removal: bool, *, tag=None):
        """Sets who can create an custom role or channel upon getting the defined role"""
        cursor = await self.bot.db.acquire()
        if type == 'role' and isinstance(position, discord.Role) or type == 'voice' and isinstance(position, discord.CategoryChannel) or type == 'text' and isinstance(position, discord.CategoryChannel):
            guild = ctx.guild.id
            role = role.id
            position = position.id
            result = await cursor.fetchval("SELECT role FROM custom WHERE system = $1 and guild = $2", type, guild)
            if result is not None:
                await cursor.execute("DELETE FROM custom WHERE system = $1 and guild = $2", type, guild)
                await ctx.send("Custom Removed Successfully!")
            else:
                await cursor.execute("INSERT INTO custom(guild, role, position, amount, tag, system, remove) VALUES($1, $2, $3, $4, $5, $6, $7)", guild, role, position, amount, tag, type, removal)
                await ctx.send("Custom Set Successfully!")
        else:
            await ctx.send("The 'type' must be defined as role, text, or voice")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def voice(self, ctx, channel: discord.VoiceChannel, role: discord.Role):
        """Sets what role to give and remove depending on the user joining the set voice channel"""
        chan = str(channel.id)
        cursor = await self.bot.db.acquire()
        result = await cursor.fetchval("SELECT role FROM boost WHERE date = $1 and role = $2 and guild = $3 and type = $4", chan, role.id, ctx.guild.id, 'voice')
        if result is not None:
            await cursor.execute("DELETE FROM boost WHERE role = $1 and date = $2 and guild = $3 and type = $4", chan, role.id, ctx.guild.id, 'voice')
            await ctx.send("Voice Role Deleted Successfully!")
        else:
            await cursor.execute("INSERT INTO boost(guild, role, date, type) VALUES($1, $2, $3, $4)", ctx.guild.id, role.id, chan, 'voice')
            await ctx.send("Voice Role Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def counter(self, ctx, count: bool, channel: discord.TextChannel, role: discord.Role, delay: int=None):
        """Allows you to set an counting channel"""
        cursor = await self.bot.db.acquire()
        def date_convert_seconds(s):
            current, result = Calendar().parse(s)
            t = datetime.datetime(*current[:6])
            futureDate = int((t-datetime.datetime.now()).total_seconds())
            return futureDate+1, result

        result = await cursor.fetchval("SELECT channel FROM count WHERE guild = $1 and channel = $2 and role = $3", ctx.guild.id, channel.id, role.id)
        if result is not None:
            await cursor.execute("DELETE FROM count WHERE guild = $1 and channel = $2 and role = $3", ctx.guild.id, channel.id, role.id)
            await channel.set_permissions(role, overwrite=None)
            await ctx.send("Counting Channel Deleted Successfully!")
        else:
            time = date_convert_seconds(delay)
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            else:
                await cursor.execute("INSERT INTO count(guild, channel, role, count, delay) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, channel.id, role.id, count, time[0])
                await channel.set_permissions(role, read_messages=True, send_messages=False)
                await ctx.send("Counting Channel Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="To disable applications, remove the channel applications will be set to")
    @commands.has_permissions(manage_guild=True)
    async def application(self, ctx, type, *, main: typing.Union[discord.Role, discord.TextChannel, str]):
        """Lets you set up applications"""
        cursor = await self.bot.db.acquire()
        # feature to close and open applications
        if type == "question":
            result = await cursor.fetch("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'question')
            print(result)
            print(main)
            if re.search("--edit=([0-9])", main):
                value = re.split("--edit=([0-9])", main, 1)
                await cursor.execute("UPDATE questions SET text = $1 WHERE guild = $2 and type = $3 and number = $4", value[0], ctx.guild.id, 'question', int(value[1]))
                await ctx.send("Question edited successfully!")
            elif main not in [fetch[0] for fetch in result]:
                await cursor.execute("INSERT INTO questions(guild, type, text, number) VALUES($1, $2, $3, $4)", ctx.guild.id, 'question', main, len(result)+1)
                await ctx.send("Question set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'question', main)
                await ctx.send("Question removed successfully!")
        elif type == "role":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'role')
            main = str(main.id)
            if not result == main:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'role', main)
                await ctx.send("Role set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'role', main)
                await ctx.send("Role removed successfully!")
        elif type == "require":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'require')
            main = str(main.id)
            if not result == main:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'require', main)
                await ctx.send("Requirement set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'require', main)
                await ctx.send("Requirement removed successfully!")
        elif type == "channel":
            result = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'channel')
            main = str(main.id)
            if not result == main:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'channel', main)
                await ctx.send("Channel set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'channel', main)
                await ctx.send("Channel removed successfully!")
        elif type == "accept":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'accept')
            if not result == main:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'accept', main)
                await ctx.send("Acceptance text set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'accept', main)
                await ctx.send("Acceptance text removed successfully!")
        elif type == "deny":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'deny')
            if not result == main:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'deny', main)
                await ctx.send("Denied text set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'deny', main)
                await ctx.send("Denied text removed successfully!")
        else:
            await ctx.send("The 'type' must be defined as question, role, require, channel, accept or deny")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def suggestion(self, ctx, *, channel: discord.TextChannel):
        """Sets what channel guild suggestions should be sent to"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT suggest FROM settings WHERE suggest = $1 and guild = $2", channel.id, guild)
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
            cursor.execute("UPDATE settings SET announce = NULL and guild = $1", guild)
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
        result = await cursor.fetchval("SELECT role FROM boost WHERE date::int8 = $1 and role = $2 and guild = $3 and type = $4", day, rolemaster, guild, 'boost')
        if result is None:
            await cursor.execute(f"INSERT INTO boost(guild, date, role, type) VALUES($1, $2::int8, $3, $4)", guild, day, rolemaster, 'boost')
            await ctx.send("Booster Reward Set Successfully!")
        else:
            await cursor.execute(f"DELETE FROM boost WHERE role = $1 and date::int8 = $2 and guild = $3 and type = $4", day, rolemaster, guild, 'boost')
            await ctx.send("Booster Reward Deleted Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def invite(self, ctx, amount: int, *, role: discord.Role):
        """Allows you to set an invite reward based on how many users were invited by the inviter"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        rolemaster = role.id
        result = await cursor.fetchval("SELECT role FROM boost WHERE date = $1 and role = $2 and guild = $3 and type = $4", str(amount), rolemaster, guild, 'invite')
        if result is None:
            await cursor.execute("INSERT INTO boost(guild, date, role, type) VALUES($1, $2, $3, $4)", guild, str(amount), rolemaster, 'invite')
            await ctx.send("Inviter Reward Set Successfully!")
        else:
            await cursor.execute("DELETE FROM boost WHERE role = $1 and date = $2 and guild = $3 and type = $4", rolemaster, str(amount), guild, 'invite')
            await ctx.send("Inviter Reward Deleted Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def overwrites(self, ctx, channel: discord.TextChannel, role: discord.Role):
        """Sets if defined channel overwrites be given back if the member rejoins by a set role for selected channel"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        result = await cursor.fetchval("SELECT role FROM roles WHERE role = $1 and member = $2 and guild = $3 and type = $4", role.id, channel.id, guild.id, 'recover')
        if result is not None:
            await cursor.execute("DELETE FROM roles WHERE guild = $1 and member = $2 and role = $3 and type = $4", guild.id, channel.id, role.id, 'recover')
            await ctx.send("Overwrites Recovery Set Successfully!")
        else:
            await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guild.id, channel.id, role.id, 'recover')
            await ctx.send("Overwrites Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def announce(self, ctx, channel: discord.TextChannel):
        """Sets what channel broadcast messages should be sent to"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT announce FROM settings WHERE announce = $1 and guild = $2", channel.id, guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
        if result is not None:
            await cursor.execute("UPDATE settings SET announce = NULL and guild = $1", guild)
            await ctx.send("Announcement Channel Disabled Successfully!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(guild, announce) VALUES($1, $2)", guild, channel.id)
            await ctx.send("Announcement Channel Enabled Successfully!")
        else:
            await cursor.execute("UPDATE settings SET announce = $1 WHERE guild = $2", channel.id, guild)
            await ctx.send("Announcement Channel Enabled Successfully!")
        await self.bot.db.release(cursor)


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def flag(self, ctx, flag, *, role: discord.Role):
        """Allows you to set what role to give automatically depending on what flags the user has"""
        cursor = await self.bot.db.acquire()
        if flag in ('staff', 'partner', 'hypesquad', 'bug_hunter', 'hypesquad_bravery', 'hypesquad_brilliance', 'hypesquad_balance', 'early_supporter', 'team_user', 'system', 'bug_hunter_level_2', 'verified_bot', 'verified_bot_developer'):
            guild = ctx.guild.id
            result = await cursor.fetchval("SELECT role FROM boost WHERE role = $1 and date = $2 and guild = $3 and type = $4", role.id, flag, guild, 'flag')
            if result is None:
                await cursor.execute("INSERT INTO boost(guild, role, date, type) VALUES($1, $2, $3, $4)", guild, role.id, flag, 'flag')
                await ctx.send("Flags Role Set Successfully!")
            else:
                await cursor.execute("DELETE FROM boost WHERE role = $1 and guild = $2 and date = $3 and type = $4", role.id, guild, flag, 'flag')
                await ctx.send("Flags Role Deleted Successfully!")
        else:
            await ctx.send("The flag must be defined as 'staff', 'partner', 'hypesquad', 'bug_hunter', 'hypesquad_bravery', 'hypesquad_brilliance', 'hypesquad_balance', 'early_supporter', 'team_user', 'system', 'bug_hunter_level_2', 'verified_bot', or 'verified_bot_developer'")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def partnership(self, ctx, channel: discord.TextChannel, role: discord.Role, reward: discord.Role=None, amount: int=None):
        """Allows you to set an partnership reward based on how many partnerships were completed"""
        cursor = await self.bot.db.acquire()
        role = role.id
        reward = reward.id
        channel = channel.id
        check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, 'partners', channel)
        reward = 0 if reward is None else reward
        amount = 0 if amount is None else amount
        if check is not None:
            await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, 'partners', channel)
            await ctx.send("Partner Requirement Deleted Successfully!")
        else:
            await cursor.execute(f"INSERT INTO leveling(guild, system, level, difficulty, type, role) VALUES($1, $2, $3, $4, $5, $6)", ctx.guild.id, 'partners', amount, reward, channel, role)
            await ctx.send("Partner Requirement Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="Define 'type' as blacklist to set which role/channel cannot level, multiplier for what channel/role gains an xp bounus, or weight for how hard it is level up per voice/message/default or behavoir to change the behavoir, or ranking for what role to give upon the user reaching the level")
    @commands.has_permissions(manage_guild=True)
    async def leveling(self, ctx, type, main: typing.Union[discord.TextChannel, discord.Role, discord.VoiceChannel, str], value: typing.Union[int, bool, str]=None):
        """Allows you to set up server leveling"""
        cursor = self.bot.db.acquire()
        if type == "blacklist":
            if isinstance(main, discord.TextChannel) or isinstance(main, discord.VoiceChannel) or isinstance(main, discord.Role):
                check = await cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3", ctx.guild.id, 'blacklist', main.id)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3",  ctx.guild.id, 'blacklist', main.id)
                    await ctx.send(f"Blacklist Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role) VALUES($1, $2, $3)", ctx.guild.id, 'blacklist', main.id)
                    await ctx.send(f"Blacklist Set Successfully!")
            else:
                await ctx.send("'main' must be defined as an role or channel")
        elif type == "multiplier":
            if isinstance(main, discord.TextChannel) or isinstance(main, discord.VoiceChannel) or isinstance(main, discord.Role):
                check = await cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", ctx.guild.id, 'multiplier', main.id, value)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", ctx.guild.id, 'multiplier', main.id, value)
                    await ctx.send(f"Multiplier Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role, difficulty) VALUES($1, $2, $3, $4)", ctx.guild.id, 'multiplier', main.id, value)
                    await ctx.send(f"Multiplier Set Successfully!")
            else:
                ctx.send("'main' must be defined as an role or channel")
        elif type == "weight":
            if main in ('message', 'voice', 'difficulty'):
                check = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, main)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and difficulty = $3", ctx.guild.id, main, value)
                    await ctx.send(f"{main} Weight Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, difficulty) VALUES($1, $2, $3)", ctx.guild.id, main, value)
                    await ctx.send(f"{main} Weight Set Successfully!")
            else:
                await ctx.send("'main' must be defined as message, voice difficulty")
        elif type == "behavior":
            if main in ("keep", "clear") and isinstance(value, bool):
                check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, main, value)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, main, value)
                    await ctx.send(f"{main} Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, type) VALUES($1, $2, $3)", ctx.guild.id, main, value)
                    await ctx.send(f"{main} Set Successfully!")
            else:
                ctx.send("'main' must be defined as keep or clear")
        elif type == "ranking":
            if isinstance(main, discord.Role):
                check = await cursor.fetchval(
                    "SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4",
                    ctx.guild.id, 'levels', main.id, value)
                if check is not None:
                    await cursor.execute(
                        "DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4",
                        ctx.guild.id, 'levels', main.id, value)
                    await ctx.send("Levels Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role, level) VALUES($1, $2, $3, $4)", ctx.guild.id, 'levels', main.id, value)
                    await ctx.send("Levels Set Successfully!")
        elif type == "top":
            if value in ('day', 'week', 'year'):
                check = cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, 'top', value)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and type = $4", ctx.guild.id, 'top', main, value)
                    await ctx.send(f"{main} Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role, type) VALUES($1, $2, $3, $4)", ctx.guild.id, 'top', main, value)
                    await ctx.send(f"{main} Set Successfully!")
        else:
            await ctx.send("The 'type' must be defined as blacklist, weight, multiplier, behavior, or top")
        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Management(bot))
