import datetime
import re
import typing

import discord
from discord.ext import commands
from parsedatetime import Calendar


# administrator commands
class Management(commands.Cog, name='Management Commands'):
    """Commands that adjusts various settings of the bot."""
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
        result = await cursor.fetchval("SELECT channel FROM boost WHERE date = $1 role = $2 and guild = $3 and type = $4", chan, role.id, ctx.guild.id, 'voice')
        if result is not None:
            await cursor.execute("DELETE FROM boost WHERE role = $1 and date =  $2 and guild = $3 and type = $4", chan, role.id, ctx.guild.id, 'voice')
            await ctx.send("Voice Role Deleted Successfully!")
        else:
            await cursor.execute("INSERT INTO boost(guild, role, date, type) VALUES($1, $2, $3, $4)", ctx.guild.id, role.id, chan, 'voice')
            await ctx.send("Voice Role Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def counter(self, ctx, count: bool, channel: discord.TextChannel, role: discord.Role, delay=None):
        """Allows you to set an counting channel"""
        cursor = await self.bot.db.acquire()
        units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}
        def convert_to_seconds(s):
            return int(datetime.timedelta(**{
                units.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
                for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smhdw]?)', s, flags=re.I)
            }).total_seconds())

        result = await cursor.fetchval("SELECT channel FROM count WHERE guild = $1 and channel = $2 and role = $3", ctx.guild.id, channel.id, role.id)
        if result is not None:
            await cursor.execute("DELETE FROM count WHERE guild = $1 and channel = $2 and role = $3", ctx.guild.id, channel.id, role.id)
            await channel.set_permissions(role, overwrite=None)
            await ctx.send("Counting Channel Deleted Successfully!")
        else:
            time = convert_to_seconds(delay) if delay is not None else 0
            await cursor.execute("INSERT INTO count(guild, channel, role, count, delay) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, channel.id, role.id, count, time)
            await channel.set_permissions(role, read_messages=True, send_messages=False)
            await ctx.send("Counting Channel Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="To disable applications, remove the channel applications will be set to")
    @commands.has_permissions(manage_guild=True)
    async def applications(self, ctx, type, *, text: typing.Union[discord.Role, discord.TextChannel, str]):
        """Lets you set up applications"""
        cursor = await self.bot.db.acquire()
        # feature to close and open applications
        if type == "question":
            result = cursor.fetch("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'question')
            if re.search("--edit=", text):
                cursor.execute("UPDATE questions SET text = $1 WHERE guild = $1, type = $2, number = $3", ctx.guild.id, 'question', '')
                await ctx.send("Question edited successfully!")
            elif text not in [fetch['text'] for fetch in result]:
                await cursor.execute("INSERT INTO questions(guild, type, text, number) VALUES($1, $2, $3, $4)", ctx.guild.id, 'question', text, len(result)+1)
                await ctx.send("Question set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'question', text)
                await ctx.send("Question removed successfully!")
        elif type == "role":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'role')
            text = str(text.id)
            if not result == text:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'role', text)
                await ctx.send("Role set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'role', text)
                await ctx.send("Role removed successfully!")
        elif type == "require":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'require')
            text = str(text.id)
            if not result == text:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'require', text)
                await ctx.send("Requirement set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'require', text)
                await ctx.send("Requirement removed successfully!")
        elif type == "channel":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'channel')
            text = str(text.id)
            if not result == text:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'channel', text)
                await ctx.send("Channel set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'channel', text)
                await ctx.send("Channel removed successfully!")
        elif type == "accept":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'accept')
            if not result == text:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'accept', text)
                await ctx.send("Acceptance text set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'accept', text)
                await ctx.send("Acceptance text removed successfully!")
        elif type == "deny":
            result = cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'deny')
            if not result == text:
                await cursor.execute("INSERT INTO questions(guild, type, text) VALUES($1, $2, $3)", ctx.guild.id, 'deny', text)
                await ctx.send("Denied text set successfully!")
            else:
                await cursor.execute("DELETE FROM questions WHERE guild = $1 and type = $2 and text = $3", ctx.guild.id, 'deny', text)
                await ctx.send("Denied text removed successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def suggestions(self, ctx, *, channel: discord.TextChannel):
        """Sets what channel guild suggestions should be sent to"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT suggest FROM settings WHERE suggest = $1 and guild = $2", channel.id, guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE suggest = $1 and guild = $2", channel.id, guild)
        if result is not None:
            await cursor.execute("UPDATE settings SET suggest = NULL WHERE guild = $1", guild)
            await ctx.send("Suggestions Channel Successfully Removed!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(guild, suggest) VALUES($1, $2)", guild, channel.id)
            await ctx.send("Suggestions Channel Set Successfully!")
        else:
            await cursor.execute("UPDATE settings SET suggest = $1 WHERE guild = $2", guild, channel.id)
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
        result = await cursor.fetchrow("SELECT member, channel FROM roles WHERE recovery = $1 and guild = $2 and type = $3", role, guild.id, 'recover')
        if result[0] and result[1] is not None:
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
    async def flags(self, ctx, flag, *, role: discord.Role):
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
    async def partnership(self, ctx, channel: discord.TextChannel, role: discord.Role, reward: discord.Role, amount: int):
        """Allows you to set an partnership reward based on how many partnerships were completed"""
        cursor = await self.bot.db.acquire()
        role = role.id
        reward = reward.id
        channel = channel.id
        check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, 'partners', channel)
        if check is not None:
            await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, 'partners', channel)
            await ctx.send("Partner Requirement Deleted Successfully!")
        else:
            await cursor.execute(f"INSERT INTO leveling(guild, system, level, difficulty, type, role) VALUES($1, $2, $3, $4, $5, $6)", ctx.guild.id, 'partners', amount, reward, channel, role)
            await ctx.send("Partner Requirement Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="Define 'type' as blacklist to set which role/channel cannot level, multiplier for what channel/role gains an xp bounus, or weight for how hard it is level up per voice/message/default or behavoir to change the behavoir, or ranking for what role to give upon the user reaching the level")
    @commands.has_permissions(manage_guild=True)
    async def leveling(self, ctx, type, main: typing.Union[discord.TextChannel, discord.Role, discord.VoiceChannel, str], number: typing.Union[int, bool]=None):
        """Allows you to set ignored channels/roles, multipliers, or behavior"""
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
                check = await cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", ctx.guild.id, 'multiplier', main.id, number)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", ctx.guild.id, 'multiplier', main.id, number)
                    await ctx.send(f"Multiplier Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role, difficulty) VALUES($1, $2, $3, $4)", ctx.guild.id, 'multiplier', main.id, number)
                    await ctx.send(f"Multiplier Set Successfully!")
            else:
                ctx.send("'main' must be defined as an role or channel")
        elif type == "weight":
            if main in ('message', 'voice', 'difficulty'):
                check = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, main)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and difficulty = $3", ctx.guild.id, main, number)
                    await ctx.send(f"{main} Weight Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, difficulty) VALUES($1, $2, $3)", ctx.guild.id, main, number)
                    await ctx.send(f"{main} Weight Set Successfully!")
            else:
                await ctx.send("'main' must be defined as message, voice difficulty")
        elif type == "behavior":
            if main in ("keep", "clear") and isinstance(number, bool):
                check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, main, number)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and type = $3", ctx.guild.id, main, number)
                    await ctx.send(f"{main} Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, type) VALUES($1, $2, $3)", ctx.guild.id, main, number)
                    await ctx.send(f"{main} Set Successfully!")
            else:
                ctx.send("'main' must be defined as keep or clear")
        elif type == "ranking":
            cursor = await self.bot.db.acquire()
            if isinstance(main, discord.Role):
                check = await cursor.fetchval(
                    "SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4",
                    ctx.guild.id, 'levels', main.id, number)
                if check is not None:
                    await cursor.execute(
                        "DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4",
                        ctx.guild.id, 'levels', main.id, number)
                    await ctx.send("Levels Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role, level) VALUES($1, $2, $3, $4)", ctx.guild.id, 'levels', main.id, number)
                    await ctx.send("Levels Set Successfully!")
        else:
            await ctx.send("The 'type' must be defined as blacklist, weight, multiplier, or behavior")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def clubs(self, ctx, channel: discord.TextChannel, category: discord.CategoryChannel, role: discord.Role, give: discord.Role):
        """Sets what members are allowed to create clubs"""
        cursor = await self.bot.db.acquire()
        category = category.id
        level = channel.id
        role = role.id
        give = give.id
        type = await cursor.fetchval("SELECT system FROM leveling WHERE guild = $1 and system= $2", ctx.guild.id, 'points')
        check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4 and type = $5 and difficulty = $6", ctx.guild.id, 'points', category, level, role, give)
        if check is not None:
            await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4 and type = $5 and difficulty = $6", ctx.guild.id, 'points', category, level, role, give)
            await ctx.send("Clubs Requirement Deleted Successfully!")
        elif type is None:
            await cursor.execute("INSERT INTO leveling(guild, system, role, level, type, difficulty) VALUES($1, $2, $3, $4, $5, $6)", ctx.guild.id, 'points', category, level, role, give)
            await ctx.send("Clubs Requirement Set Successfully!")
        else:
            await cursor.execute("UPDATE leveling SET role = $1, level = $2, type = $3 WHERE guild = $4 and system = $5 and difficulty = $6", category, level, role, ctx.guild.id, 'points', give)
            await ctx.send("Clubs Requirement Updated Successfully!")
        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Management(bot))
