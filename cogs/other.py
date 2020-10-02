import asyncio
import datetime
import random
import re

import discord
import typing
from discord.ext import commands, menus


class Other(commands.Cog, name='Other Commands'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Note: The graphic must be a link to an image")
    async def createclub(self, ctx, name, description, graphic, time, *owners: discord.Member):
        """Allows you to create your very own club"""
        cursor = await self.bot.db.acquire()
        if len(owners) > 3:
            await ctx.send('You can only set up to 3 Representatives!')
            return
        guild = ctx.guild
        club = await cursor.fetchrow("SELECT level, role, type, difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
        chan = guild.get_channel(club[0])
        category = guild.get_channel(club[1])
        role = guild.get_role(club[2])
        give = guild.get_role(club[3])
        mention = ' '.join([owner.mention for owner in owners])
        mention1 = chan.mention
        default = ctx.guild.default_role
        if club[2] in [role.id for role in ctx.author.roles]:
            loading = await ctx.send(f"Creating The Club With The Name {name}")
            emote = '☑'
            color = 'fffdd0'
            embed = discord.Embed(title=f"{name} club",
                                  description=f"{description} \n\n**Representatives:** {mention} \n\n**Weekly Events:** {time} UTC \n\nReact With {emote} To Join")
            embed.set_image(url=graphic)
            created = await guild.create_role(name=name, colour=discord.Colour(int(color, 16)),
                                              reason="Newly Created Club")
            overwrites = {created: discord.PermissionOverwrite(read_messages=True, send_messages=True), default: discord.PermissionOverwrite(read_messages=False, send_messages=False), owners: discord.PermissionOverwrite(mention_everyone=True)}
            channel = await guild.create_text_channel(name, category=category, overwrites=overwrites, topic=description,
                                                      reason="Newly Created Club")
            sent = await chan.send(embed=embed)
            message = sent.channel.id + sent.id
            await sent.add_reaction(emote)
            master = "r" + str(created.id)
            for owner in owners:
                await owner.add_roles(created)
                await owner.add_roles(give)
            await cursor.execute("INSERT INTO points(guild_id, channel, exp, lvl) VALUES($1, $2, $3, $4)", guild.id, channel.id, sent.id, created.id)
            await cursor.execute("INSERT INTO reaction(guild, role, master, type, blacklist) VALUES($1, $2, $3, $4, $5)", guild.id, master, message, emote, 0)
            started = await channel.send(f"Welcome to your club {mention}! To get started please read the instructions in {mention1}. Have fun!")
            await started.pin()
            await loading.edit(content=f"Club {name} created successfully!")
        else:
            raise commands.MissingRole(role.name)
        await self.bot.db.release(cursor)

    @commands.command(description="Note: The graphic must be a link to an image")
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
        hosts = message.mentions
        role = guild.get_role(club[2])
        give = guild.get_role(channel[1])
        if club[2] in [role.id for role in ctx.author.roles]:
            overwrites = {hosts: discord.PermissionOverwrite(), owners: discord.PermissionOverwrite(mention_everyone=True)}
            loading = await ctx.send(f"Editing The Club With The Name {name}")
            emote = '☑'
            await role.edit(name=name)
            await new.edit(name=name, topic=description, overwrites=overwrites)
            for host in hosts:
                if host.id not in [owner.id for owner in owners]:
                    await host.remove_role(give)
                for owner in owners:
                    await owner.add_roles(role)
                    await owner.add_roles(give)
            embed = discord.Embed(title=f'{name} club',
                                  description=f"{description} \n\n**Representatives:** {mention} \n\n**Weekly Events:** {time} UTC \n\nReact With {emote} To Join")
            embed.set_image(url=graphic)
            await message.edit(embed=embed)
            await loading.edit(content=f"Club {name} edited successfully!")
        else:
            raise commands.MissingRole(role.name)
        await self.bot.db.release(cursor)

    @commands.command()
    async def deleteclub(self, ctx, channel: discord.TextChannel):
        """Deletes your created club"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        owner = await cursor.fetchrow("SELECT level, type, difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
        role = guild.get_role(owner[1])
        main = guild.get_channel(owner[0])
        give = guild.get_role(owner[2])
        if role.id in [role.id for role in ctx.author.roles]:
            loading = await ctx.send(f"Deleting The Club With The Name {channel}")
            delete = await cursor.fetchrow(f"SELECT channel, exp, lvl FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
            if delete is None:
                await ctx.send(f"This club does not exist! Create One With `{ctx.prefix}createclub`")
                return
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
            await cursor.execute("DELETE FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
            await cursor.execute("DELETE FROM reaction WHERE role = $1 and master = $2 and guild = $3", menu.id, main, ctx.guild.id)
            await loading.edit(content=f"Club {category.name} deleted successfully!")
        await self.bot.db.release(cursor)

    @commands.command(description="Supply type with 'r' to signify default reaction roles, 'o' for one time only reaction roles, or 'n' for toggle reaction roles in an reaction role catagorey")
    @commands.has_permissions(manage_guild=True)
    async def reactionrole(self, ctx, message: discord.Message, emoji, role: discord.Role, type, blacklist: discord.Role = None):
        """Sets a reaction role with an defined message and emoji"""
        global roles, mark
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        role = role.id
        main = message.id + ctx.channel.id
        emote = re.findall(r'(\d+)\s*', emoji)
        roles = blacklist.id if blacklist is not None else 0
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

    @commands.command()
    async def apply(self, ctx, view=None):
        """Allows you to create an application or view current questions"""
        cursor = await self.bot.db.acquire()
        if view == "view" or view == "questions" or view == "list":
            view = await cursor.fetch("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'question')

            class Source(menus.ListPageSource):
                def __init__(self, data):
                    super().__init__(data, per_page=10)

                async def format_page(self, menu, entry):
                    offset = menu.current_page * self.per_page
                    joined = '\n'.join(f'{i}. {v}' for i, v in enumerate(entry, start=1 + offset))
                    return f'```{joined}```\nPage {menu.current_page + 1}/{self.get_max_pages()}'

            pages = menus.MenuPages(source=Source([view[0] for view in view]), clear_reactions_after=True)
            await pages.start(ctx)

        else:
            member = ctx.author
            role = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'require')
            if int(role) in [role.id for role in member.roles]:
                questions = await cursor.fetch("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'question')
                await cursor.execute("INSERT INTO owner(guild, member, type) VALUES($1, $2, $3)", ctx.guild.id, member.id, 'app')
                questions = [questions[0] for questions in questions]
                q = '\n'.join(f'{i}. **{v}**' for i, v in enumerate(questions, start=1))
                embed = discord.Embed(title=f"{ctx.guild} Current Questions", description=f"{q} \n\nRespond with `start` to start the application! This will expire in 60 seconds")
                try:
                    await member.send(embed=embed)
                    await ctx.send("The Application is ready to be started in your dm's")
                except discord.Forbidden:
                    await ctx.send("The Application could not be sent in your dm's! Ensure Dionysus can send you dm's then try again")
                await self.bot.db.release(cursor)
            else:
                await ctx.send("You are not allowed to create Applications!")

    @commands.command(aliases=["makevote"])
    @commands.has_permissions(manage_messages=True)
    async def createpoll(self, ctx, multiple: bool, topic, duration, *questions):
        """Allows you to create a poll"""
        cursor = await self.bot.db.acquire()
        await ctx.message.delete()
        if len(questions) > 20:
            await ctx.send("You can only have a maximum of 20 questions!")
            return

        units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}

        def convert_to_seconds(s):
            return int(datetime.timedelta(**{
                units.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
                for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smhdw]?)', s, flags=re.I)
            }).total_seconds())

        time = convert_to_seconds(duration)
        delta = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
        ends = datetime.datetime.strftime(delta, '%A %d %B %Y @ %H:%M:%S UTC')
        type = "Multiple Options" if multiple is True else "Single Option"
        embed = discord.Embed(title=topic)
        embed.set_footer(text=f"Ends At {ends} - {type}")
        indicators = self.bot.emoji[1648:1668][::-1]
        item = 0
        for feilds in questions:
            embed.add_field(name=indicators[item], value=feilds)
            item += 1
        sent = await ctx.send(embed=embed)
        for button in range(item):
            await sent.add_reaction(indicators[button])
        voting = sent.id + sent.channel.id
        await cursor.execute("INSERT INTO vote(guild, message, win, date, type) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, voting, multiple, item, "poll")
        await asyncio.sleep(time)
        execute = await cursor.fetchval("SELECT message FROM vote WHERE guild = $1 and message = $2 and win = $3 and type = $4", ctx.guild.id, voting, multiple, "poll")
        if execute is not None:
            sent = await ctx.channel.fetch_message(sent.id)
            data = sent.embeds[0]
            name = [value.name for value in data.fields]
            questions = [value.value for value in data.fields]
            votes = sum([reaction.count - 1 for reaction in sent.reactions if reaction.emoji in name])
            embed = discord.Embed(title="Poll Results", description=topic)
            result = 0
            for reaction in sent.reactions:
                if reaction.emoji in name:
                    embed.add_field(name=questions[result], value=f"{reaction.count - 1} - {round((reaction.count - 1) * 100 / votes, 2) if votes != 0 else 0.0}%")
                    result += 1
            await sent.edit(embed=embed)
            await sent.clear_reactions()
        await cursor.execute("DELETE FROM vote WHERE guild = $1 and message = $2 and win = $3 and type = $4", ctx.guild.id, voting, multiple, "poll")
        await self.bot.db.release(cursor)

    @commands.command(aliases=["endvote"])
    @commands.has_permissions(manage_messages=True)
    async def endpoll(self, ctx, message: int):
        """Allows you to end a running poll"""
        cursor = await self.bot.db.acquire()
        await ctx.message.delete()
        sent = await ctx.channel.fetch_message(message)
        voting = sent.id + sent.channel.id
        execute = await cursor.fetchval("SELECT message FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, voting, "poll")
        if execute is not None:
            data = sent.embeds[0]
            title = data.title
            name = [value.name for value in data.fields]
            questions = [value.value for value in data.fields]
            votes = sum([reaction.count - 1 for reaction in sent.reactions if reaction.emoji in name])
            embed = discord.Embed(title="Poll Results", description=title)
            result = 0
            for reaction in sent.reactions:
                if reaction.emoji in name:
                    embed.add_field(name=questions[result], value=f"{reaction.count - 1} - {round((reaction.count - 1) * 100 / votes, 2) if votes != 0 else 0}%")
                    result += 1
            await sent.edit(embed=embed)
            await sent.clear_reactions()
            await cursor.execute("DELETE FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, voting, "poll")
        else:
            await ctx.send("This Poll Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

    @commands.command(aliases=["makegiveaway"])
    @commands.has_permissions(manage_messages=True)
    async def creategiveaway(self, ctx, name, winners: int, duration, requirement=None):
        """Allows you to create and host your own giveaway"""
        global winner
        cursor = await self.bot.db.acquire()
        cursor.row_factory = lambda cursor, row: row[0]
        units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}

        def convert_to_seconds(s):
            return int(datetime.timedelta(**{
                units.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
                for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smhdw]?)', s, flags=re.I)
            }).total_seconds())

        await cursor.execute("DELETE FROM vote WHERE date < DATE_SUB(NOW(), INTERVAL 7 DAY) and type = $1", "giveaway end")
        time = convert_to_seconds(duration)
        now = datetime.datetime.utcnow()
        delta = now + datetime.timedelta(seconds=time)
        ends = datetime.datetime.strftime(delta, '%A %d %B %Y @ %H:%M:%S UTC')
        stamp = delta.timestamp()
        embed = discord.Embed(title=name, description=f"**React With 🎉 To Enter** \n Winners: {winners} \nRequirement: {requirement} \nGiveaway Ends At: {ends}")
        sent = await ctx.send(embed=embed)
        await sent.add_reaction('🎉')
        await cursor.execute("INSERT INTO vote(guild, message, date, win, type) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, sent.id, stamp, winners, "giveaway")
        await ctx.send("Giveaway Created")
        await asyncio.sleep(time)
        execute = await cursor.fetchval("SELECT date FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, sent.id, "giveaway")
        stamp = datetime.datetime.fromtimestamp(execute[0])
        if execute is not None and datetime.datetime.utcnow() < stamp:
            sent = await ctx.channel.fetch_message(sent.id)
            vote = sent.reactions
            for reaction in vote:
                if reaction.emoji == '🎉':
                    users = await reaction.users().flatten()
                    winner = random.choices(users, k=winners)
                    winner = "\n".join([winner.mention for winner in winner if winner.id != 653484307423297536])
                    embed = discord.Embed(title=name, description=f"**Giveaway Ended** \nWinners:{winner}")
                    embed.set_footer(text=f"Ended At: {ends}")
                    await sent.edit(embed=embed)
                    await cursor.execute("UPDATE vote SET type = $1 WHERE guild = $2 and message = $3 and type = $4", "giveaway end", ctx.guild.id, sent.id, "giveaway")
                    break
        else:
            await ctx.send("This Giveaway Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def endgiveaway(self, ctx, message: int):
        """Allows you to end a running giveaway"""
        cursor = await self.bot.db.acquire()
        sent = await ctx.channel.fetch_message(message)
        execute = await cursor.fetchrow("SELECT date, win FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, sent.id, "giveaway")
        if execute is not None:
            vote = sent.reactions
            for reaction in vote:
                if reaction.emoji == '🎉':
                    data = sent.embeds[0]
                    name = data.title
                    stamp = datetime.datetime.fromtimestamp(execute[0])
                    time = datetime.datetime.utcnow().timestamp()
                    if datetime.datetime.utcnow() < stamp:
                        now = datetime.datetime.utcnow()
                        ends = datetime.datetime.strftime(now, '%A %d %B %Y @ %H:%M:%S UTC')
                        users = await reaction.users().flatten()
                        winner = random.choices(users, k=execute[1])
                        winners = "\n".join([winner.mention for winner in winner if winner.id != 437447118127366154])
                        embed = discord.Embed(title=name, description=f"**Giveaway Ended** \nWinners:{winners}")
                        embed.set_footer(text=f"Ended At: {ends}")
                        await sent.edit(embed=embed)
                        await cursor.execute("UPDATE vote SET date = $1, type = $2 WHERE guild = $3 and message = $4 and type = $5", time, "giveaway end", ctx.guild.id, sent.id, "giveaway")
                        await cursor.execute(
                            "UPDATE vote SET date = $1 WHERE guild = $2 and message = $3 and type = $4", time,
                            ctx.guild.id, sent.id, "giveaway end")
                        await ctx.send("Ended Giveaway")
                        break
                    else:
                        await ctx.send("That Giveaway Has Already Ended!")
        else:
            await ctx.send("This Giveaway Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def rerollgiveaway(self, ctx, message: int):
        """Allows you to reroll the winners selected for the giveaway"""
        cursor = await self.bot.db.acquire()
        sent = await ctx.channel.fetch_message(message)
        execute = await cursor.fetchval("SELECT win FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, sent.id, "giveaway end")
        if execute is not None:
            vote = sent.reactions
            for reaction in vote:
                if reaction.emoji == '🎉':
                    data = sent.embeds[0]
                    name = data.title
                    ends = data.footer.text
                    users = await reaction.users().flatten()
                    winner = random.choices(users, k=execute[0])
                    winner = "\n".join([winner.mention for winner in winner if winner.id != 437447118127366154])
                    embed = discord.Embed(name=name, description=f"**Giveaway Ended** \nWinners:{winner}")
                    embed.set_footer(text=f"Ended At: {ends}")
                    await sent.edit(embed=embed)
                    break
        else:
            await ctx.send("This Giveaway Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

    # @commands.command(aliases=["createembed"])
    # @commands.has_permissions(manage_messages=True)
    # async def embed(self, ctx):
    #     """Allows you to create your own custom embed"""
    #     db = self.bot.db
    #     cursor = db.cursor()
    #     list = ['👁️', '↩', '✏️', '❎', '💾', '🇹', '🇩', '🇨', '🇫', '🇮', '🇪', '❌']
    #     rand = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    #     embed_id = random.choices(rand, k=7)
    #     embed = discord.Embed(title="Dionysus Embed Creation Tool", color=ctx.author.color)
    #     embed.add_field(name=list[0] + ' Preview', value='Preview The Current Embed')
    #     embed.add_field(name=list[1] + ' Send', value='Send The Current Embed')
    #     embed.add_field(name=list[2] + ' Edit', value='Edits Existing Embed')
    #     embed.add_field(name=list[3] + ' Delete', value='Deletes Existing Embed')
    #     embed.add_field(name=list[4] + ' Saves', value='Saves Or Loads An Custom Embed')
    #     embed.add_field(name=list[5] + ' Title', value='Adds An Title To The Embed')
    #     embed.add_field(name=list[6] + ' Description', value='Adds An Description To The Embed')
    #     embed.add_field(name=list[7] + ' Color', value='Changed The Color To The Embed')
    #     embed.add_field(name=list[8] + ' Footer', value='Adds Footer Text To The Embed')
    #     embed.add_field(name=list[9] + ' Thumbnail Image', value='Adds A Thumbnail To The Embed')
    #     embed.add_field(name=list[10] + ' Fields', value='Allows You To Manage Embed Fields')
    #     embed.add_field(name=list[11] + ' Close', value='Closes The Embed Creation Tool')
    #     custom = await ctx.send(embed=embed)
    #
    #     for reaction in list:
    #         await custom.add_reaction(reaction)
    #     await cursor.execute(f"INSERT INTO embed(member, name) VALUES(?, ?)", (ctx.author.id, embed_id))
    #     db.commit()
    #     cursor.close()

    #
    # @embed.error
    # async def embed_error(self, ctx, error):
    #     if isinstance(error, commands.CommandInvokeError):
    #         embed = discord.Embed(title="An Exception Occurred",
    #                               description=f"Durning handling of this command, an unexpected error has occured \n This error has been sent to the bot dev and will get to it ASAP \n\n `{error}`")
    #         await ctx.send(embed=embed)
    #         for me in owner:
    #             user = self.bot.get_user(me)
    #             await user.send(await error_return("EMBED", error))
    #         return
    #     else:
    #         await ctx.send(await error_return("EMBED", error))
    #         return

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def updaterank(self, ctx, member: discord.Member, rank: int):
        """Updates someones rank for the leveling system"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        if rank < 0:
            await ctx.send("Integer Cannot Be Less Than 0!")
            return
        if member is not None:
            mem = member.id
            check = await cursor.fetchval("SELECT guild_id FROM levels WHERE guild_id = $1 and user_id = $2", ctx.guild.id, mem)
            if check is not None:
                await cursor.execute("UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and user_id = $4", rank, 0, guild, mem)
                await ctx.send(f"All levels updated successfully for {member.name}!")
            else:
                await cursor.execute("INSERT INTO levels(lvl, exp, guild_id, user_id) VALUES(?, ? ,?, ?)", rank, 0, guild, mem)
                await ctx.send(f"All levles updated successfully for {member.name}!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, channel: discord.TextChannel, *, message):
        """Sends a message to an defined channel, as though it was sent by the bot"""
        channel = ctx.channel if not channel else channel
        await ctx.message.delete()
        await channel.send(message)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def dm(self, ctx, to: typing.Union[discord.Member, discord.Role], *, message):
        """Sends a direct message to an user or people in a role as tho it was sent by the bot"""
        loading = await ctx.send(f"Messaging users for {to}")
        try:
            if isinstance(to, discord.Member):
                await to.send(message)
            elif isinstance(to, discord.Role):
                for member in to.members:
                    await member.send(message)
        except discord.Forbidden:
            pass

        await loading.edit(content=f"Successfully sent message to users in {to}")


def setup(bot):
    bot.add_cog(Other(bot))
