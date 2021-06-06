import re

import discord
from discord.ext import commands
import datetime

from parsedatetime import Calendar

class Role(commands.Cog, name="Roles"):
    """[Lets you do various things with roles](https://github.com/SrS2225a/role-manager-bot/wiki/Roles)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description='Supply type with add/remove to add or remove that role and to with everyone to execute for everyone in the guild, members to execute for all members, bots to execute for all bots, or an user')
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

    @commands.command(description="Supply type with color to edit a roles color, name to edit an roles name, position to edit a role position, create to create a role or delete to delete a role")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, type, role: discord.Role, arg=None):
        """Allows you to create, edit, or delete an role"""
        guild = ctx.guild
        if type not in ("color", "name", "position", "create", "delete"):
            await ctx.send("The 'type' must be defined as add or type")
            return
        # allows us to edit a position of a a role
        if type in "position":
            if re.search(r"(\D*)\d*", arg):
                await role.edit(position=int(arg))
                await ctx.send("Role Position Edited Successfully!")
            elif role is None:
                await ctx.send(f"Missing Role Argument")
            else:
                ctx.send("Role Position Must Be An Integer")
        # allows us to edit the color of a role
        if type in "color":
            if re.search(r"#([0-9a-fA-F]{6})", arg):
                await role.edit(reason=None, color=discord.Colour(int(arg[1:], 16)))
                await ctx.send("Role Color Edited Successfully!")
            elif role is None:
                await ctx.send(f"Missing Role Argument")
            else:
                ctx.send("Role Color Must Be A Hex")
        # allows us to edit the name of a role
        if type in "name":
            if re.search("^[!-~][ -~]{0,49}$", arg):
                await role.edit(name=arg)
                await ctx.send(f"Role Name Edited Successfully!")
            elif role is None:
                await ctx.send(f"Missing Role Argument")
            else:
                await ctx.send(f"Role Name Must Not Contain More Than 50 Characters!")
        # allows us to create a new role
        if type in "create":
            if re.search("^[!-~][ -~]{0,49}$", arg):
                await guild.create_role(name=arg)
                await ctx.send("Role Created Successfully!")
            else:
                await ctx.send(f"Role Name Must Not Contain More Than 50 Characters!")
        # allows us to delete an alreadly existing role
        if type in "delete":
            await role.delete()
            await ctx.send("Role Deleted Successfully!")

    @commands.command(description="Supply type with add/remove to add or remove the role to the user")
    @commands.has_permissions(manage_guild=True)
    async def autorole(self, ctx, type, role: discord.Role, delay=None):
        """Sets what role will be given or removed automatically to the user upon joining the guild"""
        if type is None or type in ("add", "remove"):
            cursor = await self.bot.db.acquire()
            guild = ctx.guild.id
            result = await cursor.fetchval("SELECT role FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id, guild, type)
            if result is None:
                def date_convert_seconds(s):
                    current, result = Calendar().parse(s)
                    t = datetime.datetime(*current[:6])
                    futureDate = int((t - datetime.datetime.now()).total_seconds())
                    return futureDate + 1, result

                time = (0, 2) if delay is None else date_convert_seconds(delay)
                if time[1] < 1:
                    await ctx.send("I do not recognise that time!")
                else:
                    await cursor.execute("INSERT INTO roles(guild, role, member, type) VALUES($1, $2, $3, $4)", guild, role.id, time[0], type)
                    await ctx.send(f"Auto Role Set successfully!")
            else:
                await cursor.execute("DELETE FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id, guild, type)
                await ctx.send(f"Auto Role Removed successfully!")
            await self.bot.db.release(cursor)
        else:
            await ctx.send("The first argument must be defined as add or remove")

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
        await self.bot.db.release(cursor)


    @commands.command(aliases=['autopn'])
    @commands.has_permissions(manage_guild=True)
    async def autopostition(self, ctx, type, role: discord.Role, delay):
        """Allows you to automatically add roles based on someone's creation or server join date"""
        if type in ("create", "join"):
            cursor = await self.bot.db.acquire()
            guild = ctx.guild.id
            result = await cursor.fetchval("SELECT role FROM roles WHERE role = $1 and type = $2 and guild = $3", role.id, type, guild)
            if result is None:
                def date_convert_seconds(s):
                    current, result = Calendar().parse(s)
                    t = datetime.datetime(*current[:6])
                    futureDate = int((t - datetime.datetime.now()).total_seconds())
                    return futureDate + 1, result

                time = date_convert_seconds(delay)
                if time[1] < 1:
                    await ctx.send("I do not recognise that time!")
                else:
                    await cursor.execute("INSERT INTO roles(guild, role, member, type) VALUES($1, $2, $3, $4)", guild, role.id, time[0], type)
                    await ctx.send("Auto Position Set Successfully!")
            else:
                await cursor.execute("DELETE FROM roles WHERE role = $1 and guild = $2 and type = $3", role.id, guild, type)
                await ctx.send("Auto Position Deleted Successfully!")

            await self.bot.db.release(cursor)
        else:
            await ctx.send("The first argument must be defined as create or join")

    @commands.command(aliases=['rr'], description="Supply type with 'r' to signify default reaction roles, 'o' for one time only reaction roles, or 'n' for toggle reaction roles in an reaction role catagorey")
    @commands.has_permissions(manage_guild=True)
    async def reactionrole(self, ctx, message: discord.Message, emoji, role: discord.Role, type, blacklist: discord.Role = None):
        """Sets a reaction role with an defined message and emoji"""
        global roles, mark
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        role = role.id
        main = message.id + ctx.channel.id
        roles = blacklist.id if blacklist is not None else 0
        emote = re.findall(r'(\d+)\s*', emoji)
        mark = True if emote and int(emote[0]) in [emojis.id for emojis in await ctx.guild.fetch_emojis()] else False
        unicode = True if emoji in self.bot.emoji else False
        result = await cursor.fetchval("SELECT role FROM reaction WHERE master = $1 and guild = $2", main, guild)
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
        if unicode or mark:
            reaction = emote[0] if mark else emoji
            results = await cursor.fetchval("SELECT role FROM reaction WHERE role = $1 and master = $2 and guild = $3", role, main, guild)
            if not results == role:
                await cursor.execute("INSERT INTO reaction(guild, role, master, type, blacklist) VALUES($1, $2, $3, $4, $5)", guild, role, main, reaction, roles)
                await message.add_reaction(emoji)
                await ctx.send("Reaction Role Set Successfully!")
            else:
                await cursor.execute("DELETE FROM reaction WHERE role = $1 and master = $2 and guild = $3", role, main, guild)
                await ctx.send("Reaction Role Deleted Successfully!")
        else:
            await ctx.send("I do not recognise that emoji!")
        await self.bot.db.release(cursor)



def setup(bot):
    bot.add_cog(Role(bot))
