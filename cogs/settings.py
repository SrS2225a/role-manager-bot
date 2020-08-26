import typing

import discord
from discord.ext import commands

client = discord.Client()


# administrator commands
class Settings(commands.Cog, name='Settings Commands'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def custom(self, ctx, type, role: discord.Role, position: discord.Role, amount: int, tag=None):
        """Sets who can create an custom role upon getting the defined role"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        role = role.id
        position = position.id
        result = await cursor.fetchval(
            "SELECT authrole FROM settings WHERE authrole = $1 and position = $2 and amount = $3 and tag = $4 and guild = $5",
            role, position, amount, tag, guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
        if result is not None:
            await cursor.execute(
                "UPDATE settings SET authrole = NULL, position = NULL, amount = NULL, tag = NULL WHERE guild = $1",
                guild)
            await ctx.send("Custom Removed Successfully!")
        elif search is None:
            await cursor.execute(
                "INSERT INTO settings(guild, authrole, position, amount, tag) VALUES($1, $2, $3, $4, $5)", guild, role,
                position, tag)
            await ctx.send("Custom Set Successfully!")
        else:
            await cursor.execute(
                "UPDATE settings SET authrole = $1, position = $2, amount = $3, tag = $4 WHERE guild = $5", role,
                position, amount, tag, guild)
            await ctx.send("Custom Set Successfully!")
        await self.bot.db.release(cursor)
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def voice(self, ctx, channel: discord.VoiceChannel, role: discord.Role):
        """Sets what role to give and remove depending on the user joining the set voice channel"""
        chan = str(channel.id)
        cursor = await self.bot.db.acquire()
        result = await cursor.fetchval("SELECT channel FROM boost WHERE date = $1 role = $2 and guild = $3 and type = $4", chan, role.id, ctx.guild.id, 'voice')
        if not result == channel.id:
            await cursor.execute("INSERT INTO bosot(guild, role, date, type) VALUES($1, $2, $3, $4)", ctx.guild.id, role.id, chan, 'voice')
            await ctx.send("Voice Role Set Successfully!")
        else:
            await cursor.execute("DELETE FROM boost WHERE role = $1 and date =  $2 and guild = $3 and type = $4", chan, role.id, ctx.guild.id, 'voice')
            await ctx.send("Voice Role Deleted Successfully!")
        await self.bot.db.release()

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def stickyrole(self, ctx, *, role: discord.Role):
        """Sets what role will "stick" to the user upon getting the defined role"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        rolemaster = role.id
        result = await cursor.fetchval("SELECT role FROM reward WHERE role = $1 and guild = $2 and type = $3", rolemaster, guild, 'sticky')
        if not result == rolemaster:
            await cursor.execute("INSERT INTO reward(guild, role, type) VALUES($1, $2, $3)", guild, rolemaster, 'sticky')
            await ctx.send("Sticky Role Set Successfully!")
        else:
            await cursor.execute("DELETE FROM reward WHERE role = $1 and guild = $2 and type = $3", rolemaster, guild, 'sticky')
            await ctx.send("Sticky Role Deleted Successfully!")
        await self.bot.db.release()

    @commands.command()
    async def suggestions(self, ctx, *, channel: discord.TextChannel):
        """Sets what channel guild suggestions should be sent to"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT suggest FROM settings WHERE suggest = $1 and guild = $2", channel.id, guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE suggest = $1 and guild = $2", channel.id, guild)
        if result is not None:
            await cursor.execute("UPDATE settings SET suggest = NULL WHERE guild = ?", guild)
            await ctx.send("Suggestions Channel Successfully Removed!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(guild, suggest) VALUES(?, ?)", guild, channel.id)
            await ctx.send("Suggestions Channel Set Successfully!")
        else:
            await cursor.execute("UPDATE settings SET suggest = ? WHERE guild = ?", guild, channel.id)
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
    async def boosterreward(self, ctx, day: int, *, role: discord.Role):
        """Allows you to set an booster reward based on how long a booster boosted for"""
        cursor = await self.bot.db.acquire
        guild = ctx.guild.id
        rolemaster = role.id
        result = await cursor.fetchval("SELECT role FROM boost WHERE date = $1 and role = $2 and guild = $3 and type = $4", day, rolemaster, guild, 'boost')
        if result is None:
            await cursor.execute(f"INSERT INTO boost(guild, date, role, type) VALUES($1, $2, $3, $4)", guild, day, rolemaster, 'boost')
            await ctx.send("Booster Reward Set Successfully!")
        else:
            await cursor.execute(f"DELETE FROM boost WHERE role = $1 and date = $2 and guild = $3 and type = $4", day, rolemaster, guild, 'boost')
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
    async def overwrites(self, ctx, *, role: discord.Role):
        """Sets if user defined channel overwrites be given back if the member rejoins by set role"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        role = role.id
        result = await cursor.fetchval("SELECT recovery FROM settings WHERE recovery = $1 and guild = $2", role, guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
        if result is not None:
            await cursor.execute("UPDATE settings SET recovery = NULL WHERE guild = $1", guild)
            await ctx.send("Overwrites Recovery Disabled Successfully!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(guild, recovery) VALUES($1, $2)", guild, role)
            await ctx.send("Overwrites Enabled Successfully!")
        else:
            await cursor.execute("UPDATE settings SET recovery = $1 WHERE guild = $2", role, guild)
            await ctx.send("Overwrites Enabled Successfully!")
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
    async def removal(self, ctx):
        """Sets if an custom roles, text channels, and voice should be automatically removed once the set required role gets removed from the user"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT remove FROM settings WHERE remove = $1 and guild = $2", 'customrole', guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
        if result is not None:
            await cursor.execute("UPDATE settings SET remove = NULL and guild = $1", guild)
            await ctx.send("Role Removal Disabled Successfully!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(guild, remove) VALUES($1, $2)", guild, 'customrole')
            await ctx.send("Role Removal Enabled Successfully!")
        else:
            await cursor.execute("UPDATE settings SET remove = $1 WHERE guild = $2", 'customrole', guild)
            await ctx.send("Role Removal Enabled Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autorole(self, ctx, *, role: discord.Role):
        """Sets what role will be given automatically to the user upon joining the guild"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT prefix FROM settings WHERE prefix = $1 and guild = $2", role.id, guild)
        search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
        if result is not None:
            await cursor.execute("UPDATE settings SET prefix = NULL WHERE guild = $1", guild)
            await ctx.send("Auto Role Successfully Removed!")
        elif search is None:
            await cursor.execute("INSERT INTO settings(prefix, guild) VALUES($1, $2)", role.id, guild)
            await ctx.send("Auto Role Set Successfully!")
        else:
            await cursor.execute("UPDATE settings SET prefix = $1 WHERE guild = $2", role.id, guild)
            await ctx.send("Auto Role Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def flags(self, ctx, flag, *, role: discord.Role):
        """Allows you to set what role to give automatically depending on what flags the user has"""
        cursor = await self.bot.db.acquire()
        if flag in ('staff', 'partner', 'hypesquad', 'bug_hunter', 'hypesquad_bravery', 'hypesquad_brilliance', 'hypesquad_balance', 'early_supporter', 'team_user', 'system', 'bug_hunter_level_2', 'verified_bot', 'verified_bot_developer'):
            guild = ctx.guild.id
            result = await cursor.fetchval("SELECT role FROM boost WHERE role = $1 and date = $2 and guild = $3 and type = $4", role.id, flag, guild, 'flag')
            print(result)
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
        check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and level = $3 and difficulty = $4 and type = $5 and role = $6", ctx.guild.id, 'partners', amount, reward, channel, role)
        if check is not None:
            await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and level = $3 and difficulty = $4 and type = $5 and role = $6", ctx.guild.id, 'partners', amount, reward, channel, role)
            await ctx.send("Partner Requirement Deleted Successfully!")
        else:
            await cursor.execute(f"INSERT INTO leveling(guild, system, level, difficulty, type, role) VALUES($1, $2, $3, $4, $5, $6)", ctx.guild.id, 'partners', amount, reward, channel, role)
            await ctx.send("Partner Requirement Set Successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="Define 'type' as blacklist to set which role/channel cannot level, multiplier for what channel/role gains an xp bounus, or weight for how hard it is level up per voice/message/default")
    @commands.has_permissions(manage_guild=True)
    async def leveling(self, ctx, type, main: typing.Union[discord.TextChannel, discord.Role, discord.VoiceChannel, str], number: typing.Union[int, bool]=None):
        """Allows you to set ignored channels/roles, multipliers, or behavior"""
        cursor = await self.bot.db.acquire()
        if type == "blacklist":
            if isinstance(main, discord.TextChannel) or isinstance(main, discord.VoiceChannel) or isinstance(main, discord.Role):
                check = await cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3", ctx.guild.id, 'blacklist', main.id)
                if check is not None:
                    await cursor.execute("DELETE FROM LEVELING WHERE guild = $1 and system = $2 and role = $3",  ctx.guild.id, 'blacklist', main.id)
                    await ctx.send(f"Blacklist Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role) VALUES($1, $2, $3)", ctx.guild.id, 'blacklist', main.id)
                    await ctx.send(f"Blacklist Set Successfully!")
            else:
                await ctx.send("'main' must be defined as an role or channel")
        elif type == "multiplier":
            if isinstance(main, discord.TextChannel) or isinstance(main, discord.TextChannel) or isinstance(main, discord.Role):
                check = await cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", ctx.guild.id, 'multiplier', main, number)
                if check is not None:
                    await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", ctx.guild.id, 'multiplier', main, number)
                    await ctx.send(f"Multiplier Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role, dificulty) VALUES($1, $2, $3, $4)", ctx.guild.id, 'multiplier', main, number)
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
                diff = "levels"
                check = await cursor.fetchval(
                    "SELECT role FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4",
                    ctx.guild.id, diff, main.id, number)
                if check is not None:
                    await cursor.execute(
                        "DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4",
                        ctx.guild.id, diff, main.id, number)
                    await ctx.send(f"{diff} Deleted Successfully!")
                else:
                    await cursor.execute("INSERT INTO leveling(guild, system, role, level) VALUES($1, $2, $3, $4)", ctx.guild.id, diff, main.id, number)
                    await ctx.send(f"{diff} Set Successfully!")
        else:
            await ctx.send("The 'type' must be defined as blacklist, weight, multiplier, or behavior")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def clubs(self, ctx, channel: discord.TextChannel, category: discord.CategoryChannel, role: discord.Role):
        """Sets what members are allowed to create clubs"""
        cursor = await self.bot.db.acquire()
        category = category.id
        level = channel.id
        role = role.id
        type = await cursor.fetchval("SELECT system FROM leveling WHERE guild = $1 and system= $2", ctx.guild.id, 'points')
        check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = ? and system = ? and role = ? and level = ? and type = ?", ctx.guild.id, 'points', category, level, role)
        if check is not None:
            await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4 and type = $5", ctx.guild.id, 'points', category, level, role)
            await ctx.send("Clubs Requirement Deleted Successfully!")
        elif type is None:
            await cursor.execute("INSERT INTO leveling(guild, system, role, level, type) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, 'points', category, level, role)
            await ctx.send("Clubs Requirement Set Successfully!")
        else:
            await cursor.execute("UPDATE leveling SET role = $1, level = $2, type = $3 WHERE guild = $4 and system = $5", category, level, role, ctx.guild.id, 'points')
            await ctx.send("Clubs Requirement Updated Successfully!")
        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Settings(bot))
