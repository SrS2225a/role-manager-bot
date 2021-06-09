import discord
import typing
import tabulate
import re
import asyncio
import io

from discord.ext import commands, menus


class Info(commands.Cog, name='Miscellaneous'):
    """[These commands are miscellaneous](https://github.com/SrS2225a/role-manager-bot/wiki/Miscellaneous)"""

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def settings(self, ctx, setting=None):
        """List your configured bot settings for your server"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        tabulate.MIN_PADDING = 0
        ident_flag = False if setting is not None else True
        message = f"***{guild} Server Settings***\n\n\n"

        if setting == "custom" or ident_flag:
            custom = await cursor.fetch("SELECT * FROM custom WHERE guild = $1", guild.id)
            custom_table = []
            for custom in custom:
                role = guild.get_role(custom[2])
                position = guild.get_role(custom[3])
                custom_table.append([custom[1], role, position, custom[4], custom[5], custom[6]])
            if custom_table:
                message += f"**Custom Settings**\n```{tabulate.tabulate(custom_table, headers=['Type', 'Role', 'Position', 'Amount', 'Tag', 'Remove'], tablefmt='presto', disable_numparse=True)}```\n\n"

        if setting == "count" or ident_flag:
            count = await cursor.fetch("SELECT channel, role, count, delay FROM count WHERE guild = $1", guild.id)
            count_table = []
            for count in count:
                channel = guild.get_channel(count[0])
                role = guild.get_role(count[1])
                count_table.append([channel, role, count[2], count[3]])
            if count_table:
                message += f"**Counter Settings**\n```{tabulate.tabulate(count_table, headers=['Channel', 'Role', 'Count', 'Delay'], tablefmt='presto', disable_numparse=True)}```\n\n"
            
        if setting == "booster" or ident_flag:
            booster = await cursor.fetch("SELECT role, date FROM boost WHERE guild = $1 and type = $2", guild.id, 'boost')
            boost_table = []
            for booster in booster:
                role = guild.get_role(booster[0])
                boost_table.append([role, booster[1]])
            if boost_table:
                message += f"**Booster Reward Settings**\n```{tabulate.tabulate(boost_table, headers=['Role', 'Day'], tablefmt='presto', disable_numparse=True)}```\n\n"

        if setting == "invite" or ident_flag:
            invite = await cursor.fetch("SELECT role, date FROM boost WHERE guild = $1 and type = $2", guild.id, 'invite')
            invite_table = []
            for invite in invite:
                role = guild.get_role(invite[0])
                invite_table.append([role, invite[1]])
            if invite:
                message += f"**Invite Reward Settings**\n```{tabulate.tabulate(invite_table, headers=['Role', 'Day'], tablefmt='presto', disable_numparse=True)}```\n\n"

        if setting == "overwrite" or ident_flag:
            overwrite = await cursor.fetch("SELECT member, role FROM roles WHERE guild = $1 and type = $2", guild.id, 'recover')
            overwrite_table = []
            for overwrite in overwrite:
                channel = guild.get_channel(overwrite[0])
                role = guild.get_role(overwrite[1])
                overwrite_table.append([channel, role])
            if overwrite_table:
                message += f"**Channel Overwrites Settings**\n```{tabulate.tabulate(overwrite_table, headers=['Channel', 'Role'], tablefmt='presto', disable_numparse=True)}```\n\n"

        if setting == "position" or ident_flag:
            position = await cursor.fetch("SELECT type, role, member FROM roles WHERE guild = $1 and type = $2 or type = $3", guild.id, 'create', 'join')
            position_table = []
            for position in position:
                role = guild.get_role(position[1])
                position_table.append(position[0], role, position[2])
            if position_table:
                message += f"**Auto Position Settings**\n```{tabulate.tabulate(position_table, headers=['Type', 'Role', 'Time'], tablefmt='presto', disable_numparse=True)}```\n\n"

        if setting == "autorole" or ident_flag:
            autorole = await cursor.fetch("SELECT type, role, member FROM roles WHERE guild = $1 and type = $2 or type = $3", guild.id, 'add', 'remove')
            autorole_table = []
            for autorole in autorole:
                role = guild.get_role(autorole[1])
                autorole_table.append([autorole[0], role, autorole[2]])
            if autorole_table:
                 message += f"**Auto Role Settings**\n```{tabulate.tabulate(autorole_table, headers=['Type', 'Role', 'Time'], tablefmt='presto', disable_numparse=True)}```\n\n"
        
        if setting == "announce" or ident_flag:
            announce = await cursor.fetchval("SELECT announce FROM settings WHERE guild = $1", guild.id)
            announce = guild.get_channel(announce)
            if announce:
                message += f"**Announce Settings**\n```{announce}```\n\n"

        if setting == "suggest" or ident_flag:
            suggest = await cursor.fetchval("SELECT suggest FROM settings WHERE guild = $1", guild.id)
            suggest = guild.get_channel(suggest)
            if suggest:
                message += f"**Sugggest Settings**\n```{suggest}```\n\n"

        if setting == "livestream" or ident_flag:
            livestream = await cursor.fetchval("SELECT live FROM settings WHERE guild = $1", guild.id)
            livestream = guild.get_role(livestream)
            if livestream:
                message += f"**Livestream Settings**\n ````{livestream}```\n\n"

        if setting == "flags" or ident_flag:
            flags = await cursor.fetch("SELECT role, date FROM boost WHERE guild = $1 and type = $2", guild.id, 'flag')
            flags_table = []
            for flags in flags:
                role = guild.get_role(flags[0])
                flags_table.append([role, flags[1]])
            if flags_table:
                message += f"**Flag Settings**\n```{tabulate.tabulate(flags_table, headers=['Role', 'Flag'], tablefmt='presto', disable_numparse=True)}```"

        if setting == "partnership" or ident_flag:
            partnership = await cursor.fetch("SELECT level, difficulty, type, role FROM leveling WHERE guild = $1 and system = $2", guild.id, 'partners')
            partnership_table = []
            for partnership in partnership:
                channel = guild.get_channel(partnership[2])
                role = guild.get_role(partnership[3])
                reward = guild.get_role(partnership[1])
                flags_table.append([channel, role, reward, partnership[0]])
            if partnership_table:
                message += f"**Partnership Settings**\n```{tabulate.tabulate(partnership_table, headers=['Channel', 'Role', 'Reward', 'Amount'], tablefmt='presto', disable_numparse=True)}```\n\n"

        if setting == "leveling" or ident_flag:
            leveling = await cursor.fetch("SELECT * FROM leveling WHERE guild = $1 AND not system = $2 AND not system = $3", guild.id, 'partners', 'points')
            leveling_table = []
            for leveling in leveling:
                converter = commands.RoleConverter()
                if leveling[1] == 'blacklist':
                    main = guild.get_role(leveling[3])
                    main2 = guild.get_channel(leveling[3])
                    leveling_table.append([leveling[1], leveling[2], main, main2])
                elif leveling[1] == 'multiplier':
                    main = guild.get_role(leveling[3])
                    main2 = guild.get_channel(leveling[3])
                    leveling_table.append([leveling[1], leveling[2], main, main2])
                elif leveling[1] == 'levels':
                    role = guild.get_role(leveling[3])
                    leveling_table.append([leveling[1], None, role, leveling[4]])

                elif leveling[1] in ('message', 'voice', 'difficulty', 'keep', 'clear'):
                    leveling.appened([leveling[1], None, None, leveling[2]])
            if leveling_table:
                message += f"**Leveling Settings**\n```{tabulate.tabulate(leveling_table, headers=['Type', 'Channel', 'Role', 'Value'], tablefmt='presto', disable_numparse=True)}```\n\n"

            reaction = await cursor.fetch("SELECT * FROM reaction WHERE guild = $1", guild.id)
            reaction_table = []
            for reaction in reaction:
                add = True
                if 'r' in reaction[1]:
                    type = 'default'
                elif 'n' in reaction[1]:
                    type = 'toggle'
                elif 'o' in reaction[1]:
                    type = 'once'
                else:
                    add = False
                
                if add:
                    role = guild.get_role(int(re.findall(r'\d*', reaction[1])[1]))
                    blacklist = guild.get_role(reaction[4])
                    reaction_table.append([type, role, reaction[2], reaction[3], blacklist])
            if reaction_table:
                message += f"**Reaction Settings**\n```{tabulate.tabulate(reaction_table, headers=['Type', 'Role', 'Message', 'Emoji', 'Blacklist'], tablefmt='presto', disable_numparse=True)}```\n\n"

        if setting == "clubs" or ident_flag:
            clubs = await cursor.fetch("SELECT role, level, type, difficulty FROM leveling WHERE guild = $1 AND system = $2", guild.id, 'points')
            clubs_table = []
            for clubs in clubs:
                catagorey = guild.get_channel(clubs[0])
                channel = guild.get_channel(clubs[1])
                role = guild.get_role(clubs[2])
                give = guild.get_role(clubs[3])
                clubs_table.append([catagorey, channel, role, give])
            if clubs_table:
                message += f"**Club Settings**\n```{tabulate.tabulate(clubs_table, headers=['Catagorey', 'Channel', 'Role', 'Give'], tablefmt='presto', disable_numparse=True)}```\n\n"

        if setting not in ("clubs", "leveling", "partnership", "flags", "announce", "suggest", "livestream", "postiion", "overwrite", "invite", "booster", "count", "custom") and ident_flag is False:
            await ctx.send('The setting option must be defined as "clubs", "leveling", "partnership", "flags", "announce", "suggest", "livestream", "postiion", "overwrite", "invite", "booster", "count", "custom"; or none')
        else:
            await ctx.send(message)

        await self.bot.db.release(cursor)

    @commands.group(invoke_without_command=True, hidden=True)
    async def club(self, ctx):
        """Allows you to manage clubs"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @club.command(brief='club setup clubs general staff')
    @commands.has_permissions(manage_guild=True)
    async def setup(self, ctx, channel: discord.TextChannel, category: discord.CategoryChannel, role: discord.Role=None):
        """Sets what members are allowed to create clubs"""
        cursor = await self.bot.db.acquire()
        category = category.id
        level = channel.id
        if role is not None:
            role = role.id
        type = await cursor.fetchval("SELECT system FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
        check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4 and type = $5 and difficulty = $5", ctx.guild.id, 'points', category, level, role)
        if check is not None:
            await cursor.execute("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4 and difficulty = $5", ctx.guild.id, 'points', category, level, role)
            await ctx.send("Clubs Requirement Deleted Successfully!")
        elif type is None:
            await cursor.execute("INSERT INTO leveling(guild, system, role, level, difficulty) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, 'points', category, level, role)
            await ctx.send("Clubs Requirement Set Successfully!")
        else:
            await cursor.execute("UPDATE leveling SET role = $1, level = $2, difficulty = $3 WHERE guild = $4 and system = $5", category, level, role, ctx.guild.id, 'points')
            await ctx.send("Clubs Requirement Updated Successfully!")
        await self.bot.db.release(cursor)

    @club.command(brief='club create #art-&-drawing "Art & Design" "A place to design and draw art" https://example.com/link/to-image.jpg "Wensdays 2:00 PM"')
    @commands.has_permissions(manage_messages=True)
    async def create(self, ctx, name, description, graphic, time, *owners: discord.Member):
        """Allows you to create your very own club"""
        cursor = await self.bot.db.acquire()
        # checks if the user creating the club did not hit the limit and notify us
        if len(owners) > 3+1:
            await ctx.send('You can only set up to 3 Representatives!')
        else:
            guild = ctx.guild
            # gets our settings for how the club should be created
            club = await cursor.fetchrow("SELECT level, role, difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
            chan = guild.get_channel(club[0])
            category = guild.get_channel(club[1])
            give = guild.get_role(club[2])
            # sends a message that shows information about the club itself and how to join it
            mention = ' '.join([owner.mention for owner in owners])
            loading = await ctx.send(f"Creating The Club With The Name {name}!")
            emote = '☑'
            embed = discord.Embed(title=f"{name} Club", description=f"{description} \n\n**Representatives:** {mention} \n\n**Weekly Events:** {time}\n\nReact With {emote} To Join")
            embed.set_image(url=graphic)
            # creates the club
            created = await guild.create_role(name=name, colour=discord.Colour(int('fffdd0', 16)), reason="Newly Created Club")
            overwrites = {created: discord.PermissionOverwrite(read_messages=True, send_messages=True), ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False)}
            for owner in owners:
                await owner.add_roles(created)
                if give is not None:
                    await owner.add_roles(give)
                overwrites.update({owner: discord.PermissionOverwrite(mention_everyone=True, manage_messages=True)})
            channel = await guild.create_text_channel(name, category=category, overwrites=overwrites, topic=description, reason="Newly Created Club")
            sent = await chan.send(embed=embed)
            await sent.add_reaction(emote)
            # inserts our club information into the database for future use later
            message = sent.channel.id + sent.id
            master = 'c' + str(created.id)
            await cursor.execute("INSERT INTO points(guild_id, channel, exp, lvl) VALUES($1, $2, $3, $4)", guild.id, channel.id, sent.id, created.id)
            await cursor.execute("INSERT INTO reaction(guild, role, master, type, blacklist) VALUES($1, $2, $3, $4, $5)", guild.id, master, message, emote, 0)
            started = await channel.send(f"Welcome to your club {mention}! To get started please read the instructions in {chan.mention}. Have fun!")
            await started.pin()
            await loading.edit(content=f"Club {name} created successfully!")
        await self.bot.db.release(cursor)

    @club.command(brief='club edit #art-&-drawing "Art & Design" "A place to discuss, design and draw art" https://example.com/link/to-image.jpg "Wensdays 2:00 PM"')
    @commands.has_permissions(manage_messages=True)
    async def edit(self, ctx, channel: discord.TextChannel, name, description, graphic, time, *owners: discord.Member):
        """Allows you to edit your very own club"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        # checks if the channel is a club from our database
        club = await cursor.fetchrow("SELECT channel, exp, lvl FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
        channel = await cursor.fetchrow("SELECT level, difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
        # edits the message that shows information about the club itself and how to join it
        mention = ' '.join([owner.mention for owner in owners])
        chan = guild.get_channel(channel[0])
        new = guild.get_channel(club[0])
        message = await chan.fetch_message(club[1])
        role = guild.get_role(club[2])
        give = guild.get_role(channel[1])
        search = re.findall(r"<@(!?)([0-9]*)>", message.embeds[0].description)
        # edits the club
        overwrites = {role: discord.PermissionOverwrite(read_messages=True, send_messages=True), ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False)}
        loading = await ctx.send(f"Editing The Club With The Name {name}")
        for host in search:
            user = guild.get_member(int(host[1]))
            if user is not None and user.id not in [owner.id for owner in owners]:
                await user.remove_roles(give)
            for owner in owners:
                await owner.add_roles(role)
                if give is not None:
                    await owner.add_roles(give)
                overwrites.update({owner: discord.PermissionOverwrite(mention_everyone=True, manage_messages=True)})
        await role.edit(name=name)
        await new.edit(name=name, topic=description, overwrites=overwrites)
        embed = discord.Embed(title=f'{name} Club', description=f"{description} \n\n**Representatives:** {mention} \n\n**Weekly Events:** {time} UTC \n\nReact With {'☑'} To Join")
        embed.set_image(url=graphic)
        await message.edit(embed=embed)
        await loading.edit(content=f"Club {name} edited successfully!")
        await self.bot.db.release(cursor)

    @club.command(brief='club delete #art-&-drawing')
    @commands.has_permissions(manage_messages=True)
    async def delete(self, ctx, channel: discord.TextChannel):
        """Deletes your created club"""
        cursor = await self.bot.db.acquire()
        # checks if the channel is a club from our database
        guild = ctx.guild
        owner = await cursor.fetchrow("SELECT level, difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'points')
        main = guild.get_channel(owner[0])
        give = guild.get_role(owner[1])
        loading = await ctx.send(f"Deleting The Club With The Name {channel}")
        delete = await cursor.fetchrow(f"SELECT channel, exp, lvl FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
        if delete is None:
            await ctx.send(f"This club does not exist! Create One With `{ctx.prefix}createclub`")
        # deletes the club
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

    @club.command(brief="clubblacklist @Sugden#0562 #art-&-drawing")
    @commands.has_permissions(manage_messages=True)
    async def blacklist(self, ctx, member: discord.Member, channel: discord.TextChannel, *, reason=None):
        """Allows you to blacklists someone from a club"""
        cursor = await self.bot.db.acquire()
        # checks if the channel is a club from our database
        guild = ctx.guild
        club = await cursor.fetchrow(f"SELECT lvl, exp FROM points WHERE guild_id = $1 and channel = $2", ctx.guild.id, channel.id)
        if club is None:
            await ctx.send("The channel specified is not a valid Club!")
        else:
            # checks if the member was blacklisted from our club alreadly, and if they were remove them from the blacklist
            check = await cursor.fetchval("SELECT member FROM owner WHERE guild = $1 and member = $2 and message = $3 and type = $4", guild.id, member.id, club[1], 'club')
            if check is None:
                # blacklists a member from a club
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


    @commands.command()
    async def roles(self, ctx):
        """Shows a list of all roles in the server"""
        # finds all of the server roles
        roles = []
        for role in ctx.guild.roles[::-1]:
            roles.append(role.name + " " + str(role.id))

        # puts results in a navigatable page interface
        class Source(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=20)

            async def format_page(self, menu, entry):
                offset = menu.current_page * self.per_page
                joined = '\n'.join(f'{i}. {v}' for i, v in enumerate(entry, start=1 + offset))
                return f'```{joined}```\nPage {menu.current_page + 1}/{self.get_max_pages()} | Total Roles: {len(roles)}'

        pages = menus.MenuPages(source=Source(roles), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command(description="You can supply arg with 'None' to list members without a specified role")
    async def listmembers(self, ctx, *, role):
        """List members by a role or no role"""
        # finds members based on if they don't have any roles
        if role.find("--no-roles") > -1:
            members = []
            for member in ctx.guild.members:
                if len(member.roles) == 1:
                    members.append(member.name + "#" + member.discriminator)
                    
        # finds members without the specified role
        elif role.find("--none") > -1:
            role = await commands.RoleConverter().convert(ctx, role.split(" --none")[0])
            members = []
            for member in ctx.guild.members:
                if role.id not in [role.id for role in member.roles]:
                    members.append(member.name + "#" + member.discriminator + " " + str(member.id))
        # finds members with the specifed role
        else:
            role = await commands.RoleConverter().convert(ctx, role)
            members = []
            for member in ctx.guild.members:
                if role.id in [role.id for role in member.roles]:
                    members.append(member.name + "#" + member.discriminator + " " + str(member.id))
                    
        # puts results in a navigatable page interface
        class Source(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=20)

            async def format_page(self, menu, entry):
                offset = menu.current_page * self.per_page
                joined = '\n'.join(f'{i}. {v}' for i, v in enumerate(entry, start=1 + offset))
                return f'```{joined}```\nPage {menu.current_page + 1}/{self.get_max_pages()} | Total Members: {len(members)}'

        if not members:
            await ctx.send('No members')
        else:
            pages = menus.MenuPages(source=Source(members), clear_reactions_after=True)
            await pages.start(ctx)

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
        else:
           # marks us as AFK if we are
            try:
                nick = member.display_name + ' [AFK]'
                if len(nick) < 32:
                    await member.edit(nick=nick)
            except discord.Forbidden:
                pass
            await cursor.execute("INSERT INTO afk(guild, member, message) VALUES($1, $2, $3)", ctx.guild.id, member.id, reason)
            await ctx.send(f"{member.mention} I marked you as AFK!")
        await self.bot.db.release(cursor)

    @commands.group(invoke_without_command=True)
    async def apply(self, ctx):
        """Allows you to create an application"""
        cursor = await self.bot.db.acquire()
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
            if questions:
                try:
                    await member.send(embed=embed)
                    await ctx.send("The Application is ready to be started in your dm's")
                except discord.Forbidden:
                    await ctx.send("The Application could not be sent in your dm's! Ensure Dionysus can send you dm's then try again")
                else:
                    responses = []
                    send = True
                    def check(m: discord.Message):
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
                                super().__init__(clear_reactions_after=True, timeout=None)
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
                                embed = discord.Embed(title=f"Your application been accepted from {guild}!", description=yes or "Congrats! You been accepted", color=discord.Colour.green())
                                await member.send(embed=embed)
                                await complete.send("This Response Has Been Sent!", delete_after=3.4)
                                self.stop()
    
                            # adds reaction for denying an applcation
                            @menus.button('\N{CROSS MARK}')
                            async def on_deny(self, _):
                                embed = discord.Embed(title=f"Your application been denied from {guild}!", description=no or "Oh no! You been denied", color=discord.Colour.red())
                                await member.send(embed=embed)
                                await complete.send("This Response Has Been Sent!", delete_after=3.4)
                                self.stop()

                        pages = Menu(responses)
                        await pages.start(ctx, channel=complete)
            else:
                await ctx.send("Cannot start your application. Questions have not been set yet by an administator!")
        await self.bot.db.release(cursor)

    @apply.command(aliases=['view', 'questions'])
    async def list(self, ctx):
        """Allows you to view current application questions"""
        # allows the user to see a list of questions for applying
        cursor = await self.bot.db.acquire()
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
            await self.bot.db.release(cursor)


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def updaterank(self, ctx, member: discord.Member, rank: int):
        """Updates someones rank for the leveling system"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        if rank < 0:
            await ctx.send("Integer Cannot Be Less Than 0!")
        elif member is not None:
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
            await ctx.send("Suggestion successfully sent!")
        else:
            await ctx.send("Suggestions are currently not enabled for this guild!")
        await self.bot.db.release(cursor)


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def say(self, ctx, channel: discord.TextChannel, *, message):
        """Sends a message to an defined channel, as though it was sent by the bot"""
        channel = ctx.channel if not channel else channel
        escaped = discord.utils.escape_mentions(message)
        await ctx.message.delete()
        await channel.send(escaped)

    @commands.command(aliases=['av'])
    async def avatar(self, ctx, *, member: discord.User = None):
        """Enlarges a members avatar"""
        # enhances a users avatar
        member = member or ctx.author
        embed = discord.Embed(title=f"{member} Avatar")
        embed.set_image(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Responds with the bots ping between the client and discord"""
        # gets the bots current ping
        await ctx.send(f"The ping is: {round(self.bot.latency * 1000)} ms!")


def setup(bot):
    bot.add_cog(Info(bot))
