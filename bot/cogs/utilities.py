import asyncio
import datetime
import random
import re

import discord
import typing

from parsedatetime import Calendar
from discord.ext import commands


class Utilities(commands.Cog, name='Utilities'):
    """[Utilites found within the bot](https://github.com/SrS2225a/role-manager-bot/wiki/Utilities)"""
    def __init__(self, bot):
        self.bot = bot

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
        
    @commands.command(description='Supply type with list to list your reminders, delete to delete and reminder, or me/dm/here to set the destination of the reminder')
    async def remind(self, ctx, type: typing.Union[discord.TextChannel, str], duration=None, *, description=None):
        """Sets a reminder with an given time"""
        cursor = await self.bot.db.acquire()
        if type == 'list':
            reminders = await cursor.fetch("SELECT * FROM remind WHERE account = $1", ctx.author.id)
            embed = discord.Embed(title=f"{ctx.author} Reminders")
            if not reminders:
                embed.description = 'You Have No Reminders!'
            else:
                for remind in reminders:
                    chan = f"{self.bot.get_guild(remind[5])} — #{self.bot.get_channel(remind[4])}" if self.bot.get_channel(remind[4]) is not None else 'dm'
                    date = datetime.datetime.utcfromtimestamp(remind[2]).strftime('%a %b %d %Y %I:%M:%S %p UTC')
                    embed.add_field(name=f"Reminder [`{remind[1]}`]", value=f"```Time: {date}\nWhere: {chan}\nReason: {remind[3]}```", inline=False)
            await ctx.send(embed=embed)

        elif type == 'delete':
            await cursor.execute('DELETE FROM remind WHERE account = $1 and message = $2', ctx.author.id, duration)
            await ctx.send(f"Reminder Deleted Successfully!")
        else:
            if type == 'dm' or type == 'here' or isinstance(type, discord.TextChannel):
                user = ctx.author if type == 'dm' else ctx.channel if type == 'here' else type

                def date_convert_seconds(s):
                    current, result = Calendar().parse(s)
                    t = datetime.datetime(*current[:6])
                    futureDate = int((t-datetime.datetime.now()).total_seconds())
                    return futureDate+1, result

                def display_time(duration):
                    intervals = (('years', 31556952), ('months', 2592000), ('weeks', 604800), ('days', 86400), ('hours', 3600), ('minutes', 60), ('seconds', 1))

                    result = []

                    for name, count in intervals:
                        value = duration // count
                        if value:
                            duration -= value * count
                            result.append(f'{round(value)} {name}')

                    return ' '.join(result)

                time = date_convert_seconds(duration)
                if time[1] < 1:
                    await ctx.send("I do not recognise that time!")
                else:
                    time = time[0]
                    delta = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
                    stamp = delta.timestamp()
                    rand = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
                    remind_id = random.choices(rand, k=6)
                    escaped = discord.utils.escape_mentions(description)
                    await cursor.execute("INSERT INTO remind(guild, message, date, win, type, account) VALUES($1, $2, $3, $4, $5, $6)", ctx.guild.id, ''.join(remind_id), stamp, description, user.id, ctx.author.id)
                    await ctx.send(f"Reminding you in {display_time(time)} about: {escaped}")
                    await asyncio.sleep(time)
                    reminders = await cursor.fetchrow("SELECT * FROM remind WHERE account = $1 and message = $2", ctx.author.id, ''.join(remind_id))
                    if reminders is not None:
                        await user.send(f"{ctx.author.mention} {display_time(time)} ago you asked me to remind you about: {escaped}")
                        await cursor.execute("DELETE FROM remind WHERE account = $1 and message = $2", ctx.author.id, ''.join(remind_id))
            else:
                await ctx.send('Argument 1 should be dm, here or a channel')
            await self.bot.db.release(cursor)

    @commands.command(aliases=["makevote"])
    @commands.has_permissions(manage_messages=True)
    async def createpoll(self, ctx, multiple: bool, topic, duration, *questions):
        """Allows you to create a poll"""
        cursor = await self.bot.db.acquire()
        await ctx.message.delete()
        if len(questions) > 20:
            await ctx.send("You can only have a maximum of 20 questions!")
        else:
            def convert_to_seconds(s):
                current, result = Calendar().parse(s)
                t = datetime.datetime(*current[:6])
                futureDate = int((t - datetime.datetime.now()).total_seconds())
                return futureDate + 1, result

            time = convert_to_seconds(duration)
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            else:
                time = time[0]
                delta = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
                ends = datetime.datetime.strftime(delta, '%a %b %d %Y %I:%M:%S %p UTC')
                type = "Multiple Options" if multiple is True else "Single Option"
                embed = discord.Embed(title=topic)
                embed.set_footer(text=f"Ends At {ends} - {type}")
                indicators = self.bot.emoji[1648:1668][::-1]
                for item, feilds in enumerate(questions):
                    embed.add_field(name=indicators[item], value=feilds)
                sent = await ctx.send(embed=embed)
                for button in range(len(questions)):
                    await sent.add_reaction(indicators[button])
                voting = sent.id + sent.channel.id
                await cursor.execute("INSERT INTO vote(guild, message, win, date, type) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, voting, multiple, time, "poll")
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

    @commands.command(aliases=["makegiveaway", "giveaway"])
    @commands.has_permissions(manage_messages=True)
    async def creategiveaway(self, ctx, name: str, winners: int, duration, requirement=None):
        """Allows you to create and host your own giveaway"""
        cursor = await self.bot.db.acquire()

        def convert_to_seconds(s):
            current, result = Calendar().parse(s)
            t = datetime.datetime(*current[:6])
            futureDate = int((t - datetime.datetime.now()).total_seconds())
            return futureDate + 1, result

        time = convert_to_seconds(duration)
        if time[1] < 1:
            await ctx.send("I do not recognise that time!")
        else:
            time = time[0]
            now = datetime.datetime.utcnow()
            delta = now + datetime.timedelta(seconds=time)
            ends = datetime.datetime.strftime(delta, '%a %b %d %Y %I:%M:%S %p UTC')
            embed = discord.Embed(title=name, description=f"**React With 🎉 To Enter** \n Host: {ctx.author.mention} \nRequirement: {requirement} \n Winners: {winners}")
            embed.set_footer(text=f"Ends At: {ends}")
            sent = await ctx.send(embed=embed)
            await sent.add_reaction('🎉')
            await cursor.execute("INSERT INTO vote(guild, message, date, win, type) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, sent.id, delta.timestamp(), winners, "giveaway")
            await asyncio.sleep(time)

            sent = await ctx.channel.fetch_message(sent.id)
            vote = sent.reactions
            for reaction in vote:
                if reaction.emoji == '🎉':
                    users = await reaction.users().flatten()
                    winner = random.choices([winner.mention for winner in users if not winner.bot], k=winners)
                    winner = "\n".join(winner)
                    embed = discord.Embed(title=name, description=f"**Giveaway Ended** \n Host: {ctx.author.mention} \nRequirement: {requirement} \n Winners: {winner}")
                    embed.set_footer(text=f"Ended At: {ends}")
                    await cursor.execute("UPDATE vote SET type = $1 WHERE guild = $2 and message = $3 and type = $4", "giveaway end", ctx.guild.id, sent.id, "giveaway")
                    await sent.edit(embed=embed)
                    break

            await self.bot.db.release(cursor)

    @commands.command(aliases=["cancelgiveaway"])
    @commands.has_permissions(manage_messages=True)
    async def endgiveaway(self, ctx, message: discord.Message):
        """Allows you to end a running giveaway"""
        cursor = await self.bot.db.acquire()
        sent = await ctx.channel.fetch_message(message.id)
        execute = await cursor.fetchrow("SELECT date, win FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, sent.id, "giveaway")
        if execute is not None:
            vote = sent.reactions
            for reaction in vote:
                if reaction.emoji == '🎉':
                    data = sent.embeds[0]
                    stamp = datetime.datetime.fromtimestamp(execute[0])
                    time = datetime.datetime.utcnow().timestamp()
                    if datetime.datetime.utcnow() < stamp:
                        now = datetime.datetime.utcnow()
                        ends = datetime.datetime.strftime(now, '%a %b %d %Y %I:%M:%S %p UTC')
                        users = await reaction.users().flatten()
                        winner = random.choices([winner.mention for winner in users if not winner.bot], k=execute[1])
                        winner = "\n".join(winner)
                        embed = discord.Embed(title=data.title, description=f"**Giveaway Ended** \nHost: {re.search(r'<@(!?)([0-9]*)>', data.description)[0]}\nWinners:{winner}")
                        embed.set_footer(text=f"Ended At: {ends}")
                        await sent.edit(embed=embed)
                        await cursor.execute("UPDATE vote SET date = $1, type = $2 WHERE guild = $3 and message = $4 and type = $5", time, "giveaway end", ctx.guild.id, sent.id, "giveaway")
                        await ctx.send("Ended Giveaway", delete_after=2.8)
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
                    users = await reaction.users().flatten()
                    winner = random.choices([winner.mention for winner in users if not winner.bot], k=execute)
                    winners = "\n".join(winner)
                    embed = discord.Embed(name=data.title, description=f"**Giveaway Ended** \nHost: {re.search(r'<@(!?)([0-9]*)>', data.description)[0]}\nWinners:{winners}")
                    embed.set_footer(text=f"Ended At: {data.footer.text}")
                    await sent.edit(embed=embed)
                    await ctx.send("Giveaway rerolled", delete_after=2.8)
                    break
        else:
            await ctx.send("This Giveaway Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

def setup(bot):
    bot.add_cog(Utilities(bot))
