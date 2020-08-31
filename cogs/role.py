import re

import discord
from discord.ext import commands

client = discord.Client()


class Role(commands.Cog, name="Role Commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description='Supply type with add/remove to add or remove that role and to with everyone to execute for everyone in the guild, members to execute for all members, bots to execute for all bots, or an user')
    @commands.has_permissions(manage_messages=True)
    async def giverole(self, ctx, type, role: discord.Role, to):
        """Allows you to add or remove an role from members, bots, or everyone"""
        if type not in ("add", "remove"):
            await ctx.send("The first argument must be defined as add or remove")
            return
        loading = await ctx.send(f"{type}ing role for {to}")
        if to in "everyone":
            for member in ctx.guild.members:
                if role.id not in [role.id for role in member.roles] and type in "add":
                    await member.add_roles(role)
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
            print('member')
            if role.id not in [role.id for role in member.roles] and type in "add":
                print('add')
                await member.add_roles(role)
            elif role.id in [role.id for role in member.roles] and type in "remove":
                await member.remove_roles(role)
            to = member.name
        await loading.edit(content=f"Successfully {type}ed role {role.name} for {to}")

    @commands.command(description="Supply type with color to edit a roles color, name to edit an roles name, position to edit a role position, create to create a role or delete to delete a role")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, type, role: discord.Role, arg=None):
        """Allows you to create, edit, or delete an role"""
        guild = ctx.guild
        global perms
        if type not in ("color", "name", "position", "create", "delete"):
            await ctx.send("The 'type' must be defined as add or type")
            return
        if type in "position":
            if re.search(r"(\D*)\d*", arg):
                await role.edit(position=int(arg))
                await ctx.send("Role Position Edited Successfully!")
            elif role is None:
                await ctx.send(f"Missing Role Argument")
            else:
                ctx.send("Role Position Must Be An Integer")
        if type in "color":
            if re.search(r"#([0-9a-fA-F]{6})", arg):
                await role.edit(reason=None, color=discord.Colour(int(arg[1:], 16)))
                await ctx.send("Role Color Edited Successfully!")
            elif role is None:
                await ctx.send(f"Missing Role Argument")
            else:
                ctx.send("Role Color Must Be A Hex")
        if type in "name":
            if re.search("^[!-~][ -~]{0,49}$", arg):
                await role.edit(name=arg)
                await ctx.send(f"Role Name Edited Successfully!")
            elif role is None:
                await ctx.send(f"Missing Role Argument")
            else:
                await ctx.send(f"Role Name Must Not Contain More Than 50 Characters!")
        if type in "create":
            if re.search("^[!-~][ -~]{0,49}$", arg):
                await guild.create_role(name=arg)
                await ctx.send("Role Created Successfully!")
            else:
                await ctx.send(f"Role Name Must Not Contain More Than 50 Characters!")
        if type in "delete":
            await role.delete()
            await ctx.send("Role Deleted Successfully!")


def setup(bot):
    bot.add_cog(Role(bot))
