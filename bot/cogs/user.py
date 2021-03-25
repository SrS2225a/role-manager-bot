import asyncio
import io
import re

import discord
from discord.ext import commands, menus
from tabulate import tabulate
from tqdm import tqdm

class User(commands.Cog, name='User Commands'):
    """Basic commands anyone can run relating to Discord or the Bot itself"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Responds with the bots ping between the client and discord"""
        # gets the bots current ping
        await ctx.send(f"The ping is: {round(self.bot.latency * 1000)} ms!")

    @commands.command()
    async def apply(self, ctx, list=None):
        """Allows you to create an application or view current questions"""
        cursor = await self.bot.db.acquire()
        # allows the user to see a list of questions for applying
        if list == "view" or list == "questions" or list == "list":
            list = await cursor.fetch("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'question')

            if not list:
                await ctx.send("No results!")
            else:
                # puts results in a navigatable page interface
                class Source(menus.ListPageSource):
                    def __init__(self, data):
                        super().__init__(data, per_page=10)

                    async def format_page(self, menu, entry):
                        offset = menu.current_page * self.per_page
                        joined = '\n'.join(f'{i}. {v}' for i, v in enumerate(entry, start=1 + offset))
                        return f'```{joined}```\nPage {menu.current_page + 1}/{self.get_max_pages()}'

                pages = menus.MenuPages(source=Source([view[0] for view in list]), clear_reactions_after=True)
                await pages.start(ctx)

        else:
            # gets settings for applications
            member = ctx.author
            guild = ctx.guild
            check = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'require')
            channel = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'channel')
            role = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'role')
            # checks if the user can create an application
            if channel is None:
                await ctx.send("Applications Are Currently Disabled For This Bot!")
            elif check is not None and int(check) in [role.id for role in member.roles]:
                await ctx.send("You are not allowed to create Applications!")
            else:
                # feteches questions
                questions = await cursor.fetch("SELECT text FROM questions WHERE guild = $1 and type = $2", ctx.guild.id, 'question')
                questions = [questions[0] for questions in questions]
                q = '\n'.join(f'{i}. **{v}**' for i, v in enumerate(questions, start=1))
                embed = discord.Embed(title=f"{ctx.guild} Current Questions", description=q)
                embed.set_footer(text="Respond with 'start' to start the application! This will expire in 60 seconds")
                # checks if we can start the application in dm's
                try:
                    await member.send(embed=embed)
                    await ctx.send("The Application is ready to be started in your dm's")
                except discord.Forbidden:
                    await ctx.send("The Application could not be sent in your dm's! Ensure Dionysus can send you dm's then try again")
                else:
                    responses = []
                    send = True
                    def check(m):
                        return m.guild is None and m.author.id == member.id
                    try:
                        # asks the user to confirm the application proccess then records responses
                        confirm = await self.bot.wait_for('message', check=check, timeout=60)
                        if confirm.content == 'start':
                            for i, v in enumerate(questions, start=1):
                                await member.send(f"Question {i}. {v}")
                                response = await self.bot.wait_for('message', check=check)
                                responses.append((v, response.content))
                        else:
                            await member.send("Canceled")
                            send = False
                    except asyncio.TimeoutError:
                        await member.send("You took too long to confirm this current application. Canceled!")
                        send = False
                    if send:
                        # sends and tells the bot where to send finished applicants
                        yes = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", guild.id, 'accept')
                        no = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", guild.id, 'deny')
                        channel = await cursor.fetchval("SELECT text FROM questions WHERE guild = $1 and type = $2", guild.id, 'channel')
                        complete = guild.get_channel(int(channel))
                        await member.send("Your response has been recorded! You will receive a response soon letting you know if you have been accepted or not")
                        
                        # creates a simple aceppt/deny reaction menu
                        class Menu(menus.Menu):
                            def __init__(self, data):
                                super().__init__(delete_message_after=True)
                                self.data = data

                            # checks if we have actually reacted to the menu
                            def reaction_check(self, payload):
                                if payload.message_id != self.message.id:
                                    return False
                                if payload.user_id == self.bot.user.id:
                                    return False
                                return payload.emoji in self.buttons
                            
                            #sends the application as a text file
                            async def send_initial_message(self, ctx, channel):
                                joined = '\n'.join(f"**{v[0]}**\n{i}. {v[1]}\n\n" for i, v in enumerate(self.data, start=1))
                                file = io.StringIO(joined)
                                return await channel.send(f"New Applicant From {member} [{member.id}]", file=discord.File(file, filename=f"{member}-applicant.txt"))

                            # adds reaction for accepting the application
                            @menus.button('\N{WHITE HEAVY CHECK MARK}')
                            async def on_confirm(self, _):
                                if role is not None:
                                    staff = guild.get_role(int(role))
                                    await member.add_roles(staff)
                                embed = discord.Embed(title=f"Your application been accepted from {guild}!", description=yes if yes is not None else "Congrats! You been accepted", color=discord.Colour.green())
                                await member.send(embed=embed)
                                await complete.send("This Response Has Been Sent!", delete_after=3.4)
                                self.stop()
    
                            # adds reaction for denying an applcation
                            @menus.button('\N{CROSS MARK}')
                            async def on_deny(self, _):
                                embed = discord.Embed(title=f"Your application been denied from {guild}!", description=no if no is not None else "Oh no! You been denied", color=discord.Colour.red())
                                await member.send(embed=embed)
                                await complete.send("This Response Has Been Sent!", delete_after=3.4)
                                self.stop()

                        pages = Menu(responses)
                        await pages.start(ctx, channel=complete)

        await self.bot.db.release(cursor)


    @commands.command(aliases=['top', 'lb'], description='Supply type with rankings/invites/partnerships to view that particular leaderboard')
    async def leaderboard(self, ctx, type):
        """Shows top rankings"""
        global result, check, user
        cursor = await self.bot.db.acquire()
        # shows the leaderboard for leveling
        if type == 'rankings':
            # checks if the sever has leveling enabled for Dionysus
            diff1 = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.author.guild.id, 'difficulty')
            if diff1 is not None:
                # gets our leaderboard results
                result = await cursor.fetch("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, exp DESC", ctx.guild.id)
                table = []
                for row in result:
                    user = self.bot.get_user(id=int(row[0]))
                    if user is not None:
                        table.append([row[1], row[2], user.name + "#" + user.discriminator])

                # puts results in a navigatable page interface and formats our data into a text table
                class Source(menus.ListPageSource):
                    def __init__(self, data):
                        super().__init__(data, per_page=20)

                    async def format_page(self, menu, entry):
                        offset = menu.current_page * self.per_page
                        embed = discord.Embed(title=f"Dionysus Rankings (Showing Entries {1 + offset} - {50 + offset if len(entry) == 50 else len(entry) + offset})",
                                              description=f"```{tabulate(entry, headers=['XP', 'LV', 'USER'], tablefmt='presto')}```")
                        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                        return embed

                pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
                await pages.start(ctx)
            elif diff1 is None:
                await ctx.send("Rankings is currently disabled for this server!")
                                              
        # shows the leaderboard for invites
        elif type == 'invites':
            # gets our leaderboard results
            result = await cursor.fetch(f"SELECT member, SUM(amount), SUM(amount2), SUM(amount3) FROM invite WHERE guild = $1 GROUP BY member ORDER BY SUM(amount) DESC, SUM(amount2) DESC, SUM(amount3) DESC", ctx.guild.id)
            table = []
            for row in result:
                user = self.bot.get_user(id=int(row[0]))
                if user is not None:
                    table.append([row[1], row[2], row[3], user.name + "#" + user.discriminator])

            # puts results in a navigatable page interface and formats our data into a text table
            class Source(menus.ListPageSource):
                def __init__(self, data):
                    super().__init__(data, per_page=20)

                async def format_page(self, menu, entry):
                    offset = menu.current_page * self.per_page
                    embed = discord.Embed(
                        title=f"Dionysus Invites (Showing Entries {1 + offset} - {50 + offset if len(entry) == 50 else len(entry) + offset})",
                        description=f"```{tabulate(entry, headers=['JOINS', 'LEAVES', 'FAKES', 'USER'], tablefmt='presto')}```")
                    embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                    return embed

            pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
            await pages.start(ctx)

        # shows the leaderboard for invites      
        elif type == 'partnerships':
            # checks if the sever has partnerships enabled for Dionysus
            diff1 = await cursor.fetchval(f"SELECT system FROM leveling WHERE guild = $1 and system = $2", ctx.author.guild.id, 'partners')
            if diff1 is not None:
                result = await cursor.fetch("SELECT member, number FROM partner WHERE guild = $1 ORDER BY number DESC", ctx.guild.id)
                table = []
                for row in result:
                    user = self.bot.get_user(id=int(row[0]))
                    if user is not None:
                        table.append([row[1], user.name + "#" + user.discriminator])

                # puts results in a navigatable page interface and formats our data into a text table
                class Source(menus.ListPageSource):
                    def __init__(self, data):
                        super().__init__(data, per_page=20)

                    async def format_page(self, menu, entry):
                        offset = menu.current_page * self.per_page
                        embed = discord.Embed(
                            title=f"Dionysus Partners (Showing Entries {1 + offset} - {50 + offset if len(entry) == 50 else len(entry) + offset})",
                            description=f"```{tabulate(entry, headers=['PARTNERS', 'USER'], tablefmt='presto')}```")
                        embed.set_footer(
                            text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                        return embed

                pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
                await pages.start(ctx)
            elif diff1 is None:
                await ctx.send("Partnerships is currently disabled for this server!")
        else:
            await ctx.send("The argument must be defined as rankings/invites/partnerships")
        await self.bot.db.release(cursor)
    

    @commands.command(aliases=['level'])
    async def rank(self, ctx, *, user: discord.Member = None):
        """Shows your ranking status or someone else's"""
        global channel
        cursor = await self.bot.db.acquire()
        member = ctx.author if not user else user
        # checks if the sever has leveling enabled for Dionysus
        difficulty = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'difficulty')
        if difficulty is not None:
            # gets our rank results from a user or ours
            result = await cursor.fetchrow("SELECT exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2", ctx.guild.id, member.id)
            ranking = await cursor.fetch("SELECT user_id FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, exp DESC", ctx.guild.id)

            # detects if we have been ranked yet
            if result is None:
                embed = discord.Embed(
                    title='Level Ranking - Undefined Rank',
                    description='The user is not yet ranked.',
                    colour=discord.Colour.red()
                )

                await ctx.send(embed=embed)
            else:
                # shows various information about our rank
                i = 0
                for row in ranking:
                    i += 1
                    if row[0] == member.id:
                        break
                xp_end = round(result[1] * difficulty + result[1] * difficulty)
                bar = tqdm(total=xp_end, ncols=20, miniters=1, ascii='□◧■', bar_format='{l_bar}{bar}')
                bar.update(result[0])

                embed = discord.Embed(
                    title=f'Level Ranking - {member}',
                    colour=discord.Colour.blue()
                )

                embed.add_field(name='XP', value=str(result[0]) + " / " + str(xp_end))
                embed.add_field(name='Level', value=str(result[1]))
                embed.add_field(name='Ranking', value=str(i))
                embed.add_field(name='Progress', value=str(bar))

                await ctx.send(embed=embed)

        else:
            await ctx.send("This leveling feature is currently disabled for this bot!")
        await self.bot.db.release(cursor)

    @commands.command()
    async def afk(self, ctx, *, reason = None):
        """Marks you as AFK"""
        cursor = await self.bot.db.acquire()
        reason = 'AFK' if not reason else reason
        member = ctx.author
        # detects if we are already AFK
        afk = await cursor.fetchval("SELECT member FROM afk WHERE guild = $1 and member = $2", ctx.guild.id, member.id)
        # unmarks us as AFK we are
        if afk is not None:
            try:
                nick = member.display_name
                await member.edit(nick=nick.split('[AFK]')[0])
            except discord.Forbidden:
                pass
            await cursor.execute("DELETE FROM afk WHERE guild = $1 and member = $2", ctx.guild.id, member.id)
            await ctx.send(f"{member.mention} I marked you as no longer AFK!")
        else:
           # marks us as AFK if we are
            try:
                nick = member.display_name + ' [AFK]'
                await member.edit(nick=nick)
            except discord.Forbidden:
                pass
            await cursor.execute("INSERT INTO afk(guild, member, message) VALUES($1, $2, $3)", ctx.guild.id, member.id, reason)
            await ctx.send(f"{member.mention} I marked you as AFK!")
        await self.bot.db.release(cursor)

    @commands.command()
    async def invites(self, ctx, *, member: discord.Member = None):
        """Shows info about how many members you invited, or someone else"""
        cursor = await self.bot.db.acquire()
        # shows various information about how many members we invited, or someone elses
        guild = ctx.guild
        member = ctx.author if not member else member
        full = await cursor.fetchrow("SELECT SUM(amount), SUM(amount2), SUM(amount3) FROM invite WHERE guild = $1 and member = $2", guild.id, member.id)
        full = full if full[0] is not None else [0, 0, 0]
        leave = full[1] + full[2]
        server = round(full[0] * 100 / len(guild.members), 2) if full[0] != 0 else 0.0
        deficit = round(leave * 100 / full[0], 2) if full[0] != 0 else 0.0
        embed = discord.Embed(title=f"{member} Invites", description=f"{full[0]} joins, {full[1]} leaves, {full[2]} fakes \n You currently have a deficit {deficit}% and invited {server}% of server", color=member.color)
        await ctx.send(embed=embed)
        await self.bot.db.release(cursor)

    @commands.command()
    async def suggest(self, ctx, *, suggestion):
        """Allows you to make an suggestion for the guild"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        vote = ['✔', '❌']
        # checks if suggestions are enabled for the server
        result = await cursor.fetchval("SELECT suggest FROM settings WHERE guild = $1", guild.id)
        channel = guild.get_channel(result)
        if channel is not None:
            # sends the suggestion to the defined channel
            embed = discord.Embed(title=f"{ctx.author} Suggestion", description=suggestion)
            sent = await channel.send(embed=embed)
            for reaction in vote:
                await sent.add_reaction(reaction)
        else:
            await ctx.send("Suggestions are currently not enabled for this guild!")
        await self.bot.db.release(cursor)

    @commands.command(description="Supply type with role/text/voice to edit that custom and argument with a hex color for roles, user limit for voice channels, or topic for text channels")
    async def createcustom(self, ctx, type, argument, *, name):
        """Allows you to create your own custom role or channel"""
        cursor = await self.bot.db.acquire()
        author = ctx.message.author
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id

       # checks if we can create a custom text channel, voice channel, or role
        async def check(argument):
            roleauth = await cursor.fetchval("SELECT role FROM custom WHERE guild = $1 and system = $2", guildid, argument)
            missing = ctx.guild.get_role(roleauth)
            if roleauth in [role.id for role in ctx.author.roles]:
                return True
            else:
                raise commands.MissingRole(missing.name) if missing is not None else commands.CommandError(f'Creating this custom role/channel is currently disabled for this bot!')
        
        # allows us to create a custom role
        if type == 'role':
            await check(type)
            # checks if we alreadly have a custom role
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'role')
            if result is None:
                # checks where the newly created custom role should be placed in hierarchy
                default = await cursor.fetchrow("SELECT position, tag FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
                custom = f"{name} ({default[1]})" if default[1] is not None else name
                # checks if all arguments are correct
                if not re.search("#([0-9a-fA-F]{6})", argument):
                    await ctx.send(f"The first argument Must Be A Hex")
                elif len(custom) > 50:
                    await ctx.send(f"The role name cannot be over 50 characters!")
                else:
                    # creates custom role and inserts role information into our database for future use
                    role = await guild.create_role(reason='User created an custom role', name=custom, color=discord.Colour(int(argument[1:], 16)))
                    pos = guild.get_role(role_id=default[0])
                    await role.edit(position=pos.position)
                    await author.add_roles(role)
                    await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guildid, memID, role.id, 'role')
                    await ctx.send("Custom Role created successfully!")
            else:
                await ctx.send(f"You already have a custom role!")
                            
        # allows us to create a custom text channel
        elif type == 'text':
            await check(type)
            # checks if we alreadly have a custom text channel
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'text')
            if result is None:
                # checks which channel catagorey the newly created custom text channel should be placed
                default = await cursor.fetchrow("SELECT position, tag FROM custom WHERE guild = $1 and system = $2", guildid, 'text')
                custom = f"{argument} __**({default[1]})**__" if default[1] is not None else argument
                # checks if all arguments are correct
                if len(custom) > 1024:
                    await ctx.send("The channel topic cannot be over 1024 characters!")
                elif len(name) > 100:
                    await ctx.send("The channel name cannot be over 100 Characters!")
                else:
                    # creates custom text channel and inserts channel information into our database for future use
                    category = guild.get_channel(default[0])
                    permissions = {guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False), author: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
                    channel = await guild.create_text_channel(argument, topic=custom, overwrites=permissions, category=category, reason='User Created Custom Text Channel')
                    await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guildid, memID, channel.id, 'text')
                    await ctx.send("Custom Text Channel Created Successfully!")
            else:
                await ctx.send("You already have a custom text channel!")
                            
       # allows us to create a custom voice channel
        elif type == 'voice':
            await check(type)
            # checks if we alreadly have a custom voice channel
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'voice')
            if result is None:
                # checks which channel catagorey the newly created custom voice channel should be placed
                default = await cursor.fetchrow("SELECT position, tag FROM custom WHERE guild = $1 and system = $2", guildid, 'voice')
                custom = f"{name} ({default[1]})" if default[1] is not None else name
                # checks if all arguments are correct
                if len(name) > 100:
                    await ctx.send("The channel name cannot be over 100 Characters!")
                elif int(argument) > 99:
                    await ctx.send("The user limit cannot be over 99 members!")
                else:
                   # creates custom voice channel and inserts channel information into our database for future use
                    category = guild.get_channel(default[0])
                    permissions = {guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False), author: discord.PermissionOverwrite(view_channel=True, connect=True, move_members=True)}
                    channel = await guild.create_voice_channel(custom, user_limit=argument, overwrites=permissions, category=category, reason='User Created Custom Voice Channel')
                    await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guildid, memID, channel.id, 'voice')
                    await ctx.send("Custom Voice Channel Created Successfully!")
            else:
                await ctx.send("You already have a custom voice channel!")
        else:
            await ctx.send("The 'type' argument should be defined as role, text, or voice")
        await self.bot.db.release(cursor)

    @commands.command(description="Supply type with role/text/voice to edit that custom and argument with a hex color for roles, user limit for voice channels, or topic for text channels")
    async def editcustom(self, ctx, type, argument, *, name):
        """Allows you to edit your custom role or channel"""
        cursor = await self.bot.db.acquire()
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        
        # allows us to edit a custom role
        if type == 'role':
            # checks if the custom role does not exist
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'role')
            if result is not None:
                # gets our custom role
                role = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'role')
                default = await cursor.fetchval("SELECT tag FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
                custom = f"{name} ({default})" if default is not None else name
                # checks if all arguments are correct
                if not re.search(r"#([0-9a-fA-F]{6})", argument):
                    await ctx.send(f"The first argument Must Be A Hex")
                elif len(custom) > 50:
                    await ctx.send(f"Role Name Is Over 50 Characters!")
                else:
                    # edits our custom role
                    crole = guild.get_role(role_id=role)
                    await crole.edit(reason=None, name=custom, color=discord.Colour(int(argument[1:], 16)))
                    await ctx.send("Custom Role Edited Successfully!")
            else:
                await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createcustom` to create one!")
                            
        # allows us to edit a custom text channel
        elif type == 'text':
            # checks if the custom text channel does not exist
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'text')
            if result is not None:
                # gets our custom text channel
                channel = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'text')
                default = await cursor.fetchval("SELECT tag FROM custom WHERE guild = $1 and system = $2", guildid, 'text')
                custom = f"{argument} __**({default})**__" if default is not None else argument
                # checks if all arguments are correct
                if len(argument) > 1024:
                    await ctx.send("The channel topic cannot be over 1024 characters!")
                elif len(name) > 100:
                    await ctx.send("The channel name cannot be over 100 characters!")
                else:
                    # edits our custom text channel
                    cchannel = guild.get_channel(channel)
                    await cchannel.edit(name=argument, topic=custom)
                    await ctx.send("Custom Text Channel Edited Successfully!")
            else:
                await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createcustom` to create one!")
                            
        # allows us to edit a custom voice channel
        elif type == 'voice':
            # checks if the custom voice channel does not exist
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'voice')
            if result is not None:
                # gets our custom voice channel
                channel = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'voice')
                default = await cursor.fetchval("SELECT tag FROM custom WHERE guild = $1 and system = $2", guildid, 'voice')
                custom = f"{name} ({default})" if default is not None else name
                # checks if all arguments are correct
                if len(custom) > 100:
                    await ctx.send("The channel name cannot be over 100 Characters!")
                elif int(argument) > 99:
                    await ctx.send("The user limit cannot be over 99 members!")
                else:
                    # edits our custom voice channel
                    cchannel = guild.get_channel(channel)
                    await cchannel.edit(name=custom, user_limit=argument)
                    await ctx.send("Custom Voice Channel Edited Successfully!")
            else:
                await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createcustom` to create one!")
        else:
            await ctx.send("The 'type' argument should be defined as role, text, or voice")

        await self.bot.db.release(cursor)

    @commands.command(description="Supply type with role/text/voice to delete that custom")
    async def deletecustom(self, ctx, type):
        """Deletes your custom role or channel that you have created"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
         
        # allows us to delete a custom role
        if type == 'role':
            # checks if the custom role exists           
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'role')
            if result is not None:
                # deletes our custom role
                role = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'role')
                crole = guild.get_role(role)
                await crole.delete()
                await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", guildid, role, memID, 'role')
                await ctx.send(f"Custom Role Deleted Successfully!")
            else:
                await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createcustom` to create one!")
                            
        # allows us to delete a custom text channel
        elif type == 'text':
            # checks if the custom text channel exists
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'text')
            if result is not None:
                # deletes our custom text channel
                channel = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'text')
                cchannel = guild.get_channel(channel)
                await cchannel.delete()
                await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", guildid, channel, memID, 'text')
                await ctx.send(f"Custom Text Channel Deleted Successfully!")
            else:
                await ctx.send(f"You need to have a custom text channel first! Use `{ctx.prefix}createcustom` to create one!")
                            
         # allows us to delete a custom voice channel
        elif type == 'voice':
            # checks if the custom voice channel exists
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'voice')
            if result is not None:
                # deletes our custom voice channel
                channel = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'voice')
                cchannel = guild.get_channel(channel)
                await cchannel.delete()
                await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", guildid, channel, memID, 'voice')
                await ctx.send(f"Custom Text Channel Deleted Successfully!")
            else:
                await ctx.send(f"You need to have a custom voice channel first! Use `{ctx.prefix}createcustom` to create one!")
        else:
            await ctx.send("The 'type' argument should be defined as role, text, or voice")
        await self.bot.db.release(cursor)

    @commands.command(description='Supply action with role/text/voice to give that custom and type with add/remove to add or remove an custom role')
    async def givecustom(self, ctx, action, type, member: discord.Member):
        # for channel givecustom use the checking of members and add them as overwrite if applicable
        """Allows you to add or remove your custom role or channe to someone"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        if action == 'role':
            number = await cursor.fetchval("SELECT amount FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
            result = await cursor.fetchval("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'role')
            if result is not None:
                crole = guild.get_role(result)
                if type not in ("add", "remove"):
                    await ctx.send("The 'type' argument must be defined as add or remove")
                elif memID == member.id:
                    await ctx.send("You cannot Add or Remove custom roles you already own to yourself")
                else:
                    if not member.bot and crole.id not in [role.id for role in member.roles] and type in "add":
                        if len(crole.members) > number:
                            await ctx.send(f"You can only give this custom role to an max of {number} members")
                            return
                        else:
                            await member.add_roles(crole)
                    elif not member.bot and crole.id in [role.id for role in member.roles] and type in "remove":
                        await member.remove_roles(crole)
                    await ctx.send(content=f"Successfully {type} custom role to {member.name}")
            else:
                await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createcustom` to create one!")
        elif action == 'text':
            number = await cursor.fetchval("SELECT amount FROM custom WHERE guild = $1 and system = $2", guildid, 'text')
            result = await cursor.fetchval("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'text')
            if result is not None:
                cchannel = guild.get_channel(result)
                if type not in ("add", "remove"):
                    await ctx.send("The 'type' argument must be defined as add or remove")
                elif memID == member.id:
                    await ctx.send("You cannot Add or Remove custom text channels you already own to yourself")
                    return
                else:
                    if not member.bot and not cchannel.permissions_for(member).read_messages and type == "add":
                        if len(cchannel.members) > number:
                            await ctx.send(f"You can only give this custom text channel access to an max of {number} members")
                            return
                        else:
                            await cchannel.set_permissions(member, read_messages=True, send_messages=True)
                    elif not member.bot and cchannel.permissions_for(member).read_messages and type in "remove":
                        await cchannel.set_permissions(member, overwrite=None)
                    await ctx.send(content=f"Successfully {type} custom text channel access to {member.name}")
            else:
                await ctx.send(f"You need to have a custom text channel first! Use `{ctx.prefix}createcustom` to create one!")
        elif action == 'voice':
            number = await cursor.fetchval("SELECT amount FROM custom WHERE guild = $1 and system = $2", guildid, 'voice')
            result = await cursor.fetchval("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'voice')
            if result is not None:
                cchannel = guild.get_channel(result)
                if type not in ("add", "remove"):
                    await ctx.send("The 'type' argument must be defined as add or remove")
                elif memID == member.id:
                    await ctx.send("You cannot Add or Remove custom text channels you already own to yourself")
                else:
                    if not member.bot and not cchannel.permissions_for(member).view_channel and type == "add":
                        if len(cchannel.members) > number:
                            await ctx.send(f"You can only give this custom text channel access to an max of {number} members")
                            return 
                        else:
                            await cchannel.set_permissions(member, view_channel=True, connect=True)
                    elif not member.bot and cchannel.permissions_for(member).view_channel and type in "remove":
                        await cchannel.set_permissions(member, overwrite=None)
                    await ctx.send(content=f"Successfully {type} custom voice channel access to {member.name}")
            else:
                await ctx.send(f"You need to have a custom voice channel first! Use `{ctx.prefix}createcustom` to create one!")
        else:
            await ctx.send("The 'type' argument should be defined as role, text, or voice")
        await self.bot.db.release(cursor)





def setup(bot):
    bot.add_cog(User(bot))
