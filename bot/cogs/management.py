import re

import discord
from discord.ext import commands


class Management(commands.Cog, name="Management Commands"):
    """Basic commands moderators can run relating to Discord or the Bot itself"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Note: The graphic must be a link to an image")
    @commands.has_permissions(manage_messages=True)
    async def createclub(self, ctx, name, description, graphic, time, *owners: discord.Member):
        """Allows you to create your very own club"""
        cursor = await self.bot.db.acquire()
        if len(owners) > 3+1:
            await ctx.send('You can only set up to 3 Representatives!')
        else:
            guild = ctx.guild
            club = await cursor.fetchrow("SELECT level, role, type, difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
            chan = guild.get_channel(club[0])
            category = guild.get_channel(club[1])
            give = guild.get_role(club[3])
            mention = ' '.join([owner.mention for owner in owners])
            loading = await ctx.send(f"Creating The Club With The Name {name}")
            emote = '☑'
            embed = discord.Embed(title=f"{name} Club", description=f"{description} \n\n**Representatives:** {mention} \n\n**Weekly Events:** {time} UTC \n\nReact With {emote} To Join")
            embed.set_image(url=graphic)
            created = await guild.create_role(name=name, colour=discord.Colour(int('fffdd0', 16)), reason="Newly Created Club")
            overwrites = {created: discord.PermissionOverwrite(read_messages=True, send_messages=True), ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False)}
            for owner in owners:
                await owner.add_roles(created)
                await owner.add_roles(give)
                overwrites.update({owner: discord.PermissionOverwrite(mention_everyone=True)})
            channel = await guild.create_text_channel(name, category=category, overwrites=overwrites, topic=description, reason="Newly Created Club")
            sent = await chan.send(embed=embed)
            await sent.add_reaction(emote)
            message = sent.channel.id + sent.id
            master = 'c' + str(created.id)
            await cursor.execute("INSERT INTO points(guild_id, channel, exp, lvl) VALUES($1, $2, $3, $4)", guild.id, channel.id, sent.id, created.id)
            await cursor.execute("INSERT INTO reaction(guild, role, master, type, blacklist) VALUES($1, $2, $3, $4, $5)", guild.id, master, message, emote, 0)
            started = await channel.send(f"Welcome to your club {mention}! To get started please read the instructions in {chan.mention}. Have fun!")
            await started.pin()
            await loading.edit(content=f"Club {name} created successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="Note: The graphic must be a link to an image")
    @commands.has_permissions(manage_messages=True)
    async def editclub(self, ctx, channel: discord.TextChannel, name, description, graphic, time, *owners: discord.Member):
        """Allows you to edit your very own club"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        club = await cursor.fetchrow("SELECT channel, exp, lvl FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
        channel = await cursor.fetchrow("SELECT level, difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
        mention = ' '.join([owner.mention for owner in owners])
        chan = guild.get_channel(channel[0])
        new = guild.get_channel(club[0])
        message = await chan.fetch_message(club[1])
        role = guild.get_role(club[2])
        give = guild.get_role(channel[1])
        search = re.findall(r"<@(!?)([0-9]*)>", message.embeds[0].description)
        overwrites = {role: discord.PermissionOverwrite(read_messages=True, send_messages=True), ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False)}
        loading = await ctx.send(f"Editing The Club With The Name {name}")
        for host in search:
            user = guild.get_member(int(host[1]))
            if user is not None and user.id not in [owner.id for owner in owners]:
                await user.remove_roles(give)
            for owner in owners:
                await owner.add_roles(role)
                await owner.add_roles(give)
                overwrites.update({owner: discord.PermissionOverwrite(mention_everyone=True)})
        await role.edit(name=name)
        await new.edit(name=name, topic=description, overwrites=overwrites)
        embed = discord.Embed(title=f'{name} Club', description=f"{description} \n\n**Representatives:** {mention} \n\n**Weekly Events:** {time} UTC \n\nReact With {'☑'} To Join")
        embed.set_image(url=graphic)
        await message.edit(embed=embed)
        await loading.edit(content=f"Club {name} edited successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def deleteclub(self, ctx, channel: discord.TextChannel):
        """Deletes your created club"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        owner = await cursor.fetchrow("SELECT level, difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
        main = guild.get_channel(owner[0])
        give = guild.get_role(owner[1])
        loading = await ctx.send(f"Deleting The Club With The Name {channel}")
        delete = await cursor.fetchrow(f"SELECT channel, exp, lvl FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
        if delete is None:
            await ctx.send(f"This club does not exist! Create One With `{ctx.prefix}createclub`")
        category = guild.get_channel(delete[0])
        message = await main.fetch_message(delete[1])
        menu = guild.get_role(role_id=delete[2])
        main = message.channel.id + category.id
        hosts = message.mentions
        for host in hosts:
            await host.remove_role(give)
        await category.delete()
        await menu.delete()
        await message.delete()
        master = "r" + str(menu.id)
        await cursor.execute("DELETE FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
        await cursor.execute("DELETE FROM reaction WHERE role = $1 and master = $2 and guild = $3", master, main, ctx.guild.id)
        await loading.edit(content=f"Club {category.name} deleted successfully!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clubblacklist(self, ctx, member: discord.Member, channel: discord.TextChannel, *, reason=None):
        """Allows you to blacklists someone from a club"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        club = await cursor.fetchrow(f"SELECT lvl, exp FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
        if club is None:
            await ctx.send("The channel specified is not a valid Club!")
        else:
            check = await cursor.fetchval("SELECT member FROM owner WHERE guild = $1 and member = $2 and message = $3 and type = $4", guild.id, member.id, club[1], 'club')
            if check is None:
                give = guild.get_role(club[0])
                await member.remove_roles(give)
                await cursor.execute("INSERT INTO owner(guild, member, message, type) VALUES($1, $2, $3, $4)", guild.id, member.id, club[1], 'club')
                isIn = 'You have automatically been removed from this club.' if give.id in [role.id for role in ctx.author.roles] else ''
                await member.send(f"You have been Blacklisted from joining the Club {channel.mention} in the server {guild} for the reason: {reason}. {isIn}")
                await ctx.send(f"User blacklisted successfully from club {channel}")
            else:
                await cursor.execute("DELETE FROM owner WHERE guild = $1 and member = $2 and message = $3 and type = $4", guild.id, member.id, club[1], 'club')
                await ctx.send(f"User unblacklisted successfully from club {channel}")
        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Management(bot))
