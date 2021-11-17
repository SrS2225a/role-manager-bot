import re

import discord
from discord.ext import commands
import datetime

from parsedatetime import Calendar


def date_convert_seconds(s):
    current, result = Calendar().parse(s)
    t = datetime.datetime(*current[:6])
    futureDate = int((t - datetime.datetime.now()).total_seconds())
    return futureDate + 1, result


class Role(commands.Cog, name="Roles"):
    """[Lets you do various things with roles](https://github.com/SrS2225a/role-manager-bot/wiki/Roles)"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description='Supply type with add/remove to add or remove that role and to with everyone to '
                                  'execute for everyone in the guild, members to execute for all members, '
                                  'bots to execute for all bots, or an user', brief='giverole member everyone')
    @commands.has_permissions(manage_roles=True)
    async def giverole(self, ctx, type, role: discord.Role, to):
        """Allows you to add or remove an role from members, bots, or everyone"""
        if type not in ("add", "remove"):
            await ctx.send("The first argument must be defined as add or remove")
        else:
            await ctx.send(f"Changing role {role.name} for {to}")
            # detects how we want to add or remove the role to member(s)
            try:
                if to in "everyone":
                    for member in ctx.guild.members:
                        # checks if we want to add a role and if the member already has it
                        if role.id not in [role.id for role in member.roles] and type in "add":
                            await member.add_roles(role)
                        # checks if we want to remove a role and if the member already does not has it
                        elif role.id in [role.id for role in member.roles] and type in "remove":
                            await member.remove_roles(role)
                elif to in "bots":
                    for member in ctx.guild.members:
                        if member.bot and role.id not in [role.id for role in member.roles] and type in "add":
                            await member.add_roles(role)
                        elif member.bot and role.id in [role.id for role in member.roles] and type in "remove":
                            await member.remove_roles(role)
                elif to in "members":
                    for member in ctx.guild.members:
                        if not member.bot and role.id not in [role.id for role in member.roles] and type in "add":
                            await member.add_roles(role)
                        elif not member.bot and role.id in [role.id for role in member.roles] and type in "remove":
                            await member.remove_roles(role)
                else:
                    member = await commands.MemberConverter().convert(ctx, to)
                    if role.id not in [role.id for role in member.roles] and type in "add":
                        await member.add_roles(role)
                    elif role.id in [role.id for role in member.roles] and type in "remove":
                        await member.remove_roles(role)
            except discord.NotFound:
                pass

            await ctx.send(f"Successfully {type} role {role} for {to}")

    @commands.group(invoke_without_command=True, hidden=True)
    async def role(self, ctx):
        """Allows you to create, edit, or delete an role"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @role.command(name='create', brief='role create member')
    @commands.has_permissions(manage_roles=True)
    async def cr(self, ctx, name):
        """Creates a role with the specified name"""
        if len(name) < 50:
            await ctx.guild.create_role(name=name)
            await ctx.send("Role Created Successfully!")
        else:
            await ctx.send(f"Role Name Must Not Contain More Than 50 Characters!")

    @role.command(brief='role position mod 25')
    @commands.has_permissions(manage_roles=True)
    async def position(self, ctx, role: discord.Role, position: int):
        """Edit a role's current position"""
        await role.edit(position=position)
        await ctx.send("Role Position Edited Successfully!")

    @role.command(aliases=["colour"], brief='role color mod #fffaaa')
    @commands.has_permissions(manage_roles=True)
    async def color(self, ctx, role: discord.Role, *, hex):
        """Edit a role's current color"""
        if re.search(r"#([0-9a-fA-F]{6})", hex):
            await role.edit(reason=None, color=discord.Colour(int(hex[1:], 16)))
            await ctx.send("Role Color Edited Successfully!")
        else:
            ctx.send("Role Color Must Be A Hex")

    @role.command(brief='role name members member')
    @commands.has_permissions(manage_roles=True)
    async def name(self, ctx, role: discord.Role, *, name):
        """Edits a role's current name"""
        if len(name) < 50:
            await role.edit(name=name)
            await ctx.send(f"Role Name Edited Successfully!")
        else:
            await ctx.send(f"Role Name Must Not Contain More Than 50 Characters!")

    @role.command()
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx, role: discord.Role):
        """Deletes the specified role"""
        await role.delete()
        await ctx.send("Role Deleted Successfully!")

    @commands.group(invoke_without_command=True, hidden=True, brief='autorole add member 7d')
    @commands.has_permissions(manage_guild=True)
    async def autorole(self, ctx):
        """Sets what role will be given or removed automatically to the user upon joining the guild; you can also optionally set a time for when this should occur"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @autorole.command()
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx, role: discord.Role, delay=None):
        """Adds a role upon the user joining the guild"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT role FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id,
                                       guild, 'add')
        if result is None:
            time = (0, 2) if delay is None else date_convert_seconds(delay)
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            else:
                await cursor.execute("INSERT INTO roles(guild, role, member, type) VALUES($1, $2, $3, $4)", guild,
                                     role.id, time[0], 'add')
                await ctx.send(f"Auto Role Set successfully!")
        else:
            await cursor.execute("DELETE FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id, guild,
                                 'add')
            await ctx.send(f"Auto Role Removed successfully!")

        await self.bot.db.release(cursor)

    @autorole.command()
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx, role: discord.Role, delay=None):
        """Removes a role upon the user joining the guild"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT role FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id,
                                       guild, 'remove')
        if result is None:
            time = (0, 2) if delay is None else date_convert_seconds(delay)
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            else:
                await cursor.execute("INSERT INTO roles(guild, role, member, type) VALUES($1, $2, $3, $4)", guild,
                                     role.id, time[0], 'remove')
                await ctx.send(f"Auto Role Set successfully!")
        else:
            await cursor.execute("DELETE FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id, guild,
                                 'add')
            await ctx.send(f"Auto Role Removed successfully!")

        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def stickyrole(self, ctx, *, role: discord.Role):
        """Sets what role will "stick" to the user upon getting the defined role"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        rolemaster = role.id
        result = await cursor.fetchval("SELECT role FROM reward WHERE role = $1 and guild = $2 and type = $3",
                                       rolemaster, guild, 'sticky')
        if not result == rolemaster:
            await cursor.execute("INSERT INTO reward(guild, role, type) VALUES($1, $2, $3)", guild, rolemaster,
                                 'sticky')
            await ctx.send("Sticky Role Set Successfully!")
        else:
            await cursor.execute("DELETE FROM reward WHERE role = $1 and guild = $2 and type = $3", rolemaster, guild,
                                 'sticky')
            await ctx.send("Sticky Role Deleted Successfully!")
        await self.bot.db.release(cursor)

    @commands.group(aliases=['autopn'], invoke_without_command=True, hidden=True,
                    brief='autoposition join legendary member 1y')
    @commands.has_permissions(manage_guild=True)
    async def autoposition(self, ctx):
        """Allows you to automatically add roles based on someones account creation or server join date"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @autoposition.command()
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx, role: discord.Role, *, delay):
        """Adds a role based on someones account creation date"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT role FROM roles WHERE role = $1 and type = $2 and guild = $3", role.id,
                                       type, 'create')
        if result is None:
            time = date_convert_seconds(delay)
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            else:
                await cursor.execute("INSERT INTO roles(guild, role, member, type) VALUES($1, $2, $3, $4)", guild,
                                     role.id, time[0], 'create')
                await ctx.send("Auto Position Set Successfully!")
        else:
            await cursor.execute("DELETE FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id, guild,
                                 'create')
            await ctx.send("Auto Position Deleted Successfully!")

        await self.bot.db.release(cursor)

    @autoposition.command()
    @commands.has_permissions(manage_guild=True)
    async def join(self, ctx, role: discord.Role, *, delay):
        """Adds a role based on someones server join date"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        result = await cursor.fetchval("SELECT role FROM roles WHERE role = $1 and type = $2 and guild = $3", role.id,
                                       type, 'join')
        if result is None:
            time = date_convert_seconds(delay)
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            else:
                await cursor.execute("INSERT INTO roles(guild, role, member, type) VALUES($1, $2, $3, $4)", guild,
                                     role.id, time[0], 'join')
                await ctx.send("Auto Position Set Successfully!")
        else:
            await cursor.execute("DELETE FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id, guild,
                                 'join')
            await ctx.send("Auto Position Deleted Successfully!")

        await self.bot.db.release(cursor)

    @commands.command(aliases=['rr'],
                      description="Supply type with 'r' to signify default reaction roles, 'o' for one time only reaction roles, or 'n' for toggle reaction roles in an reaction role category",
                      brief='reactionrole 853147608654807081 1️⃣ introvert n')
    @commands.has_permissions(manage_guild=True)
    async def reactionrole(self, ctx, message: discord.Message, emoji, role: discord.Role, type,
                           blacklist: discord.Role = None):
        """Sets a reaction role with an defined message and emoji"""
        global roles, mark
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        role = role.id
        main = message.id + ctx.channel.id
        roles = blacklist.id if blacklist is not None else 0
        emote = re.search(r'(\d+)\s*', emoji)
        # checks if the following emoji is valid
        mark = True if int(emote.group()) in [emojis.id for emojis in await ctx.guild.fetch_emojis()] or \
                       emoji in self.bot.emoji else False
        result = await cursor.fetchval("SELECT role FROM reaction WHERE master = $1 and guild = $2", main, guild)
        # prevents conflicts with a reaction role category and makes sure that the user is defining the right type
        if result is not None and "r" in str(result):
            type = "r"
            role = type + str(role)
        elif result is not None and "o" in str(result):
            type = "o"
            role = type + str(role)
        elif result is not None and "n" in str(result):
            type = "n"
            role = type + str(role)
        elif type in ("r", "o", "n"):
            role = type + str(role)
        else:
            await ctx.send("The reaction role emoji has been incorrectly defined for this category!")
        if type in ("r", "o", "n"):
            if mark:
                # adds support for custom emojis
                reaction = emote.group() if emote is not None else emoji
                results = await cursor.fetchval(
                    "SELECT role FROM reaction WHERE role = $1 and master = $2 and guild = $3", role, main, guild)
                if not results == role:
                    await cursor.execute(
                        "INSERT INTO reaction(guild, role, master, type, blacklist) VALUES($1, $2, $3, $4, $5)", guild,
                        role, main, reaction, roles)
                    await message.add_reaction(emoji)
                    await ctx.send("Reaction Role Set Successfully!")
                else:
                    await cursor.execute("DELETE FROM reaction WHERE role = $1 and master = $2 and guild = $3", role,
                                         main, guild)
                    await ctx.send("Reaction Role Deleted Successfully!")
            else:
                await ctx.send("I do not recognise that emoji!")
        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Role(bot))
