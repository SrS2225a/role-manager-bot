import asyncio
import datetime
import random
import re

import discord
import typing
import asyncpg

from parsedatetime import Calendar
from discord.ext import commands


def date_convert_seconds(s):
    current, result = Calendar().parse(s)
    futureDate = int((datetime.datetime(*current[:6]) - datetime.datetime.now()).total_seconds())
    return futureDate + 1, result


class Utilities(commands.Cog, name='Utilities'):
    """[Utilities found within the bot](https://github.com/SrS2225a/role-manager-bot/wiki/Utilities)"""

    def __init__(self, bot):
        self.bot = bot
        self._have_data = asyncio.Event(loop=bot.loop)
        self._current_timer = None
        self.__have_data = asyncio.Event(loop=bot.loop)
        self.__current_timer = None
        self.have_data = asyncio.Event(loop=bot.loop)
        self.current_timer = None
        self._task = bot.loop.create_task(self.dispatch_remind())  # remind task
        self.__task = bot.loop.create_task(self.dispatch_poll())  # poll task
        self.task = bot.loop.create_task(self.dispatch_giveaway())  # giveaway task

    # if the cog gets unloaded in someway, stop all current running tasks
    def cog_unload(self):
        self.task.cancel()
        self._task.cancel()
        self.__task.cancel()


    class MaybeAcquire:
        def __init__(self, connection, *, pool):
            self.connection = connection
            self.pool = pool
            self._cleanup = False

        async def __aenter__(self):
            if self.connection is None:
                self._cleanup = True
                self._connection = c = await self.pool.acquire()
                return c
            return self.connection

        async def __aexit__(self, *args):
            if self._cleanup:
                await self.pool.release(self._connection)

    async def wait_for_active_reminders(self, *, connection=None, days=None):
        timer = await connection.fetchrow("SELECT * FROM remind WHERE date < (CURRENT_DATE + $1::interval) ORDER BY "
                                          "date LIMIT 1;", datetime.timedelta(days=days))
        if timer is not None:
            self._have_data.set()
            return timer

        self._have_data.clear()
        self._current_timer = None
        await self._have_data.wait()

    async def call_remind(self, timer):
        try:
            msg = f'<@{timer[0]}> <t:{round(timer[6].timestamp())}:R> you asked me to remind you about: ' \
                  f'{discord.utils.escape_mentions(timer[3])}'
            if timer[4] == timer[0]:
                user = self.bot.get_user(timer[0]) or await self.bot.fetch_user(timer[0])
                await user.send(msg)
            else:
                channel = self.bot.get_channel(timer[4]) or await self.bot.fetch_channel(timer[4])
                await channel.send(msg)
        except (discord.HTTPException, discord.Forbidden):
            return

    async def dispatch_remind(self):
        try:
            while not self.bot.is_closed():
                async with self.MaybeAcquire(connection=self.bot.db, pool=self.bot.db) as con:
                    now = datetime.datetime.now()
                    timer = self._current_timer = await self.wait_for_active_reminders(connection=con, days=48)

                    if timer[2] >= now:
                        to_sleep = (timer[2] - now).total_seconds()
                        await asyncio.sleep(to_sleep)

                    if not timer[5]:
                        await con.execute("DELETE FROM remind WHERE message = $1 and account = $2", timer[1], timer[0])
                    else:
                        time = (timer[2] - timer[6]).total_seconds()
                        await con.execute(
                            "UPDATE remind SET date = $1, assigned = $2 WHERE message = $3 and account = $4",
                            timer[2] + datetime.timedelta(seconds=time), timer[6] + datetime.timedelta(seconds=time),
                            timer[1], timer[0])

                    await self.call_remind(timer)

        except asyncio.CancelledError:
            raise
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_remind())

    async def wait_for_active_polls(self, *, connection=None, days=None):
        timer = await connection.fetchrow("SELECT * FROM vote WHERE date < (CURRENT_DATE + $1::interval) and type = "
                                          "$2 ORDER BY date LIMIT 1", datetime.timedelta(days=days), 'poll')
        if timer is not None:
            self.__have_data.set()
            return timer

        self.__have_data.clear()
        self.__current_timer = None
        await self.__have_data.wait()

    async def dispatch_poll(self):
        try:
            while not self.bot.is_closed():
                async with self.MaybeAcquire(connection=self.bot.db, pool=self.bot.db) as con:
                    now = datetime.datetime.now()
                    timer = self.__current_timer = await self.wait_for_active_polls(connection=con, days=48)

                    if timer[4] >= now:
                        to_sleep = (timer[4] - now).total_seconds()
                        await asyncio.sleep(to_sleep)

                    await con.execute("DELETE FROM vote WHERE guild = $1 and message = $2 and type = $3",
                                      timer[0], timer[1], "poll")
                    await self.call_poll(timer)

        except asyncio.CancelledError:
            raise
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            self.__task.cancel()
            self.__task = self.bot.loop.create_task(self.dispatch_poll())

    async def call_poll(self, timer):
        try:
            channel = self.bot.get_channel(timer[5]) or await self.bot.fetch_channel(timer[5])
            sent = await channel.fetch_message(timer[1])
            data = sent.embeds[0]
            name = [value.name for value in data.fields]
            questions = [value.value for value in data.fields]
            votes = sum([reaction.count - 1 for reaction in sent.reactions if reaction.emoji in name])
            embed = discord.Embed(title="Poll Results", description=data.title)
            result = 0
            for reaction in sent.reactions:
                if reaction.emoji in name:
                    embed.add_field(name=questions[result],
                                    value=f"{reaction.count - 1} - "
                                          f"{round((reaction.count - 1) * 100 / votes, 2) if votes != 0 else 0.0}%")
                    result += 1
            await sent.edit(embed=embed)
            await sent.clear_reactions()
        except (discord.HTTPException, discord.Forbidden):
            return

    async def wait_for_active_giveaways(self, *, connection=None, days=None):
        timer = await connection.fetchrow(
            "SELECT * FROM vote WHERE date < (CURRENT_DATE + $1::interval)  and type = $2 ORDER BY date LIMIT 1",
            datetime.timedelta(days=days), 'giveaway')
        if timer is not None:
            self.have_data.set()
            return timer

        self.have_data.clear()
        self.current_timer = None
        await self.have_data.wait()

    async def dispatch_giveaway(self):
        try:
            while not self.bot.is_closed():
                async with self.MaybeAcquire(connection=self.bot.db, pool=self.bot.db) as con:
                    now = datetime.datetime.now()
                    timer = self.current_timer = await self.wait_for_active_giveaways(connection=con, days=48)

                    if timer[4] >= now:
                        to_sleep = (timer[4] - now).total_seconds()
                        await asyncio.sleep(to_sleep)

                    await con.execute("UPDATE vote SET type = $1 WHERE guild = $2 and message = $3 and type = $4",
                                      "giveaway end", timer[0], timer[1], "giveaway")
                    await self.call_giveaway(timer)

        except asyncio.CancelledError:
            raise
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_giveaway())

    async def call_giveaway(self, timer):
        channel = self.bot.get_channel(timer[5]) or await self.bot.fetch_channel(timer[5])
        sent = await channel.fetch_message(timer[1])
        data = sent.embeds[0]
        ends = datetime.datetime.strftime(datetime.datetime.now(), '%a %b %d %Y %I:%M:%S %p UTC')
        for reaction in sent.reactions:
            if reaction.emoji == '🎉':
                users = await reaction.users().flatten()
                if reaction.count < timer[2]:
                    embed = discord.Embed(title=data.title,
                                          description=f"**Giveaway Ended** \nHost: "
                                                      f"{re.search(r'<@(!?)([0-9]*)>', data.description)[0]}"
                                                      f"\nWinners: No Winners!")
                    embed.set_footer(text=f"Ended At: {ends}")
                    await sent.edit(embed=embed)
                else:
                    winner = random.choices([winner.mention for winner in users if not winner.bot], k=timer[2])
                    winner = "\n".join(winner)
                    embed = discord.Embed(title=data.title,
                                          description=f"**Giveaway Ended** \nHost: "
                                                      f"{re.search(r'<@(!?)([0-9]*)>', data.description)[0]}"
                                                      f"\nWinners:{winner}")
                    embed.set_footer(text=f"Ended At: {ends}")
                    winAlert = await channel.send(winner)
                    try:
                        await winAlert.delete()
                    except discord.Forbidden:
                        pass
                    await sent.edit(embed=embed)
                break

    @commands.group(description='Supply type with a channel, dm or here to set the destination of the reminder',
                    brief='remind here 5m false do something', invoke_without_command=True)
    async def remind(self, ctx, type: typing.Union[discord.TextChannel, str], duration, repeat: bool, *, description):
        """Sets a reminder with an given time"""
        cursor = await self.bot.db.acquire()
        if type == 'dm' or type == 'here' or isinstance(type, discord.TextChannel):
            thing = ctx.author if type == 'dm' else ctx.channel if type == 'here' else type

            def display_time(duration):
                intervals = (('years', 31556952), ('months', 2592000), ('weeks', 604800), ('days', 86400),
                             ('hours', 3600), ('minutes', 60), ('seconds', 1))

                result = []

                for name, count in intervals:
                    value = duration // count
                    if value:
                        duration -= value * count
                        result.append(f'{round(value)} {name}')

                return ' '.join(result)

            time = date_convert_seconds(duration)

            # checks if a valid time
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            elif time[0] < 1:
                await ctx.send("Times cannot be in the past!")
            else:
                time = time[0]
                now = datetime.datetime.now()
                delta = now + datetime.timedelta(seconds=time)
                rand = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                        'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
                remind_id = random.choices(rand, k=6)
                escaped = discord.utils.escape_mentions(description)
                if repeat:
                    # disallows the creation of the reminder if th repeating reminder is being sent to a server and less
                    # than 1 hour to prevent spam
                    if time < 3600 and isinstance(thing, discord.TextChannel):
                        await ctx.send("To prevent spam in servers, repeating reminders must be more than 1 hour. Try "
                                       "having the reminder send to your dm or increase the reminder time")
                        return
                    else:
                        # for user friendliness in repeating reminders use display_time()
                        # converts as e.x.: 1 years 12 months 7 weeks 30 days 1 hours 60 minutes 60 seconds
                        await ctx.send(f"Ok, reminding you every {display_time(time)} about: {escaped}")
                else:
                    await ctx.send(f"Ok, reminding you at <t:{round(delta.timestamp())}> about: {escaped}")
                await cursor.execute("INSERT INTO remind(repeat, message, date, win, type, account, assigned) VALUES("
                                     "$1, $2, $3, $4, $5, $6, $7)",
                                     repeat, ''.join(remind_id), delta, description, thing.id, ctx.author.id, now)

                # restarts the task if the sleep time is less than the current timer
                if self._current_timer and delta < self._current_timer[2] or self._current_timer is None:
                    if (delta - now).total_seconds() <= (86400 * 48):  # 48 days
                        self._have_data.set()
                    self._task.cancel()
                    self._task = self.bot.loop.create_task(self.dispatch_remind())
        else:
            await ctx.send('Argument type should be dm, here or a channel')
        await self.bot.db.release(cursor)

    @remind.command()
    async def list(self, ctx):
        """Allows you to see a list of your reminders"""
        cursor = await self.bot.db.acquire()
        reminders = await cursor.fetch("SELECT * FROM remind WHERE account = $1", ctx.author.id)
        embed = discord.Embed(title=f"{ctx.author} Reminders")
        if not reminders:
            embed.description = 'You Have No Reminders!'
        else:
            for remind in reminders:
                get = self.bot.get_channel(remind[4])
                if get is not None:
                    chan = f"{get.guild} — {get.mention}"
                else:
                    chan = 'dm'
                embed.add_field(name=f"Reminder [`{remind[1]}`]" if remind[5] is False else f"Reminder [`{remind[1]}`] "
                                                                                            f"(Repeats)",
                                value=f"Time: <t:{round(remind[2].timestamp())}>\nWhere: {chan}\nReason: {remind[3]}",
                                inline=False)
        await ctx.send(embed=embed)
        await self.bot.db.release(cursor)

    @remind.command(
        description="You can optionally supply code with all if you want to delete all your reminders at once")
    async def delete(self, ctx, code):
        """Allows you to delete a reminder"""
        cursor = await self.bot.db.acquire()
        if code == "all":
            await cursor.execute('DELETE FROM remind WHERE account = $1', ctx.author.id)
            await ctx.send(f"All Reminders Deleted Successfully!")
        else:
            await cursor.execute('DELETE FROM remind WHERE account = $1 and message = $2', ctx.author.id, code)
            await ctx.send(f"Reminder Deleted Successfully!")
        self._task.cancel()
        self._task = self.bot.loop.create_task(self.dispatch_remind())
        await self.bot.db.release(cursor)

    @commands.command(aliases=["makegiveaway", "giveaway"], brief='creategiveaway "Nitro Classic" 2 2h')
    @commands.has_permissions(manage_messages=True)
    async def creategiveaway(self, ctx, name: str, winners: int, duration, requirement=None):
        """Allows you to create and host your own giveaway"""
        cursor = await self.bot.db.acquire()
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        time = date_convert_seconds(duration)

        # checks if a valid time
        if time[1] < 1:
            await ctx.send("I do not recognise that time!")
        elif time[0] < 1:
            await ctx.send("Times cannot be in the past!")
        else:
            time = time[0]
            now = datetime.datetime.now()
            delta = now + datetime.timedelta(seconds=time)
            ends = datetime.datetime.strftime(delta, '%a %b %d %Y %I:%M:%S %p UTC')
            embed = discord.Embed(title=name, description=f"**React With 🎉 To Enter** \n Host: {ctx.author.mention} "
                                                          f"\nRequirement: {requirement} \n Winners: {winners}")
            embed.set_footer(text=f"Ends At: {ends}")
            sent = await ctx.send(embed=embed)
            await sent.add_reaction('🎉')
            await cursor.execute("INSERT INTO vote(guild, message, date, win, type, channel) VALUES($1, $2, $3, $4, "
                                 "$5, $6)", ctx.guild.id, sent.id, delta, winners, "giveaway", ctx.channel.id)

            # restarts the task if the sleep time is less than the current timer
            if (delta - now).total_seconds() <= (86400 * 48):  # 48 days
                self.have_data.set()
            if self.current_timer and delta < self.current_timer[4] or self.current_timer is None:
                self.task.cancel()
                self.task = self.bot.loop.create_task(self.dispatch_giveaway())
            await self.bot.db.release(cursor)

    @commands.command(aliases=["cancelgiveaway"])
    @commands.has_permissions(manage_messages=True)
    async def endgiveaway(self, ctx, message: discord.Message):
        """Allows you to end a running giveaway"""
        cursor = await self.bot.db.acquire()
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        sent = await ctx.channel.fetch_message(message.id)
        execute = await cursor.fetchcval("SELECT date FROM vote WHERE guild = $1 and message = $2 and type = $3",
                                        ctx.guild.id, sent.id, "giveaway")
        # checks if the giveaway exists
        if execute is not None:
            time = datetime.datetime.now()
            # checks the the giveaway has already ended
            if time < execute:
                await cursor.execute(
                    "UPDATE vote SET date = $1 WHERE guild = $2 and message = $3 and type = $4",
                    time, ctx.guild.id, sent.id, "giveaway")
                # restarts the task
                self.task.cancel()
                self.task = self.bot.loop.create_task(self.dispatch_giveaway())
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
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        sent = await ctx.channel.fetch_message(message)
        execute = await cursor.fetchrow("SELECT * FROM vote WHERE guild = $1 and message = $2 and type = $3",
                                        ctx.guild.id, sent.id, "giveaway end")
        # checks if the giveaway exists
        if execute is not None:
            # trigger the giveaway
            await self.call_giveaway(execute)
        else:
            await ctx.send("This Giveaway Does Not Exist!")
        await self.bot.db.release(cursor)

    @commands.command(aliases=["makevote"],
                      brief='createpoll true "Whats your favorite color?" 4h red blue green orange purple')
    @commands.has_permissions(manage_messages=True)
    async def createpoll(self, ctx, multiple: bool, topic, duration, *questions):
        """Allows you to create a poll"""
        cursor = await self.bot.db.acquire()
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        # because of discord limitations, check the following
        if len(questions) > 20:
            await ctx.send("You can only have a maximum of 20 questions!")
        else:
            time = date_convert_seconds(duration)

            # checks if a valid time
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            elif time[0] < 1:
                await ctx.send("Times cannot be in the past!")
            else:
                now = datetime.datetime.now()
                delta = now + datetime.timedelta(seconds=time[0])
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
                await cursor.execute(
                    "INSERT INTO vote(guild, message, win, type, date, channel) VALUES($1, $2, $3, $4, $5, $6)",
                    ctx.guild.id, sent.id, multiple, "poll", delta, ctx.channel.id)
                # restarts the task if the sleep time is less than the current timer
                if (delta - now).total_seconds() <= (86400 * 48):  # 48 days
                    self.__have_data.set()
                if self.__current_timer and delta < self.__current_timer[4] or self.__current_timer is None:
                    self.__task.cancel()
                    self.__task = self.bot.loop.create_task(self.dispatch_poll())
                await self.bot.db.release(cursor)

    @commands.command(aliases=["endvote"])
    @commands.has_permissions(manage_messages=True)
    async def endpoll(self, ctx, *, message: discord.Message):
        """Allows you to end a running poll"""
        cursor = await self.bot.db.acquire()
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        execute = await cursor.fetchval("SELECT message FROM vote WHERE guild = $1 and message = $2 and type = $3",
                                        ctx.guild.id, message.id, "poll")
        # checks if the poll exists
        if execute is not None:
            await cursor.execute("UPDATE vote SET date = $1 WHERE guild = $2 and message = $3 and type = $4",
                                 datetime.datetime.now(), ctx.guild.id, message.id,
                                 "poll")  # update this instead to current date to trigger the endpoll and reload task
            self.__task.cancel()
            self.__task = self.bot.loop.create_task(self.dispatch_poll())
        else:
            await ctx.send("This Poll Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

    @commands.group(hidden=True, invoke_without_command=True)
    async def createcustom(self, ctx):
        """Allows you to create your own custom role, text channel or voice channel"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @createcustom.command(name='role')
    async def create_role(self, ctx, color, *, name):
        """Allows you to create your own custom role"""
        cursor = await self.bot.db.acquire()
        author = ctx.message.author
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id

        roleauth = await cursor.fetchval("SELECT role FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
        missing = ctx.guild.get_role(roleauth)
        if roleauth in [role.id for role in ctx.author.roles]:
            # checks if we already have a custom role
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                           guildid, memID, 'role')
            if result is None:
                # checks where the newly created custom role should be placed in hierarchy
                default = await cursor.fetchrow("SELECT position, tag FROM custom WHERE guild = $1 and system = $2",
                                                guildid, 'role')
                custom = f"{name} ({default[1]})" if default[1] is not None else name
                # because of discord limitations, check the following
                if not re.search("#([0-9a-fA-F]{6})", color):
                    await ctx.send(f"The first argument Must Be A Hex")
                elif len(custom) > 50:
                    await ctx.send(f"The role name cannot be over 50 characters!")
                else:
                    # creates custom role and inserts role information into our database for future use
                    role = await guild.create_role(reason='User created an custom role', name=custom,
                                                   color=discord.Colour(int(color[1:], 16)))
                    pos = guild.get_role(role_id=default[0])
                    await role.edit(position=pos.position)
                    await author.add_roles(role)
                    await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guildid,
                                         memID, role.id, 'role')
                    await ctx.send("Custom Role created successfully!")
            else:
                await ctx.send(f"You already have a custom role!")
        else:
            raise commands.MissingRole(missing.name) if missing is not None else commands.CommandError(
                f'Creating custom roles have not been set up yet by server owner!')
        await self.bot.db.release(cursor)

    @createcustom.command(name='text')
    async def create_text(self, ctx, name, *, topic):
        """Allows you to create your own custom text channel"""
        cursor = await self.bot.db.acquire()
        author = ctx.message.author
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        # checks if we already have a custom text channel
        roleauth = await cursor.fetchval("SELECT role FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
        missing = ctx.guild.get_role(roleauth)
        if roleauth in [role.id for role in ctx.author.roles]:
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                           guildid, memID, 'text')
            if result is None:
                # checks which channel category the newly created custom text channel should be placed
                default = await cursor.fetchrow("SELECT position, tag FROM custom WHERE guild = $1 and system = $2",
                                                guildid, 'text')
                custom = f"{topic} __**({default[1]})**__" if default[1] is not None else topic
                # because of discord limitations, check the following
                if len(custom) > 1024:
                    await ctx.send("The channel topic cannot be over 1024 characters!")
                elif len(name) > 100:
                    await ctx.send("The channel name cannot be over 100 Characters!")
                else:
                    # creates custom text channel and inserts channel information into our database for future use
                    category = guild.get_channel(default[0])
                    permissions = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                        author: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
                    channel = await guild.create_text_channel(name, topic=custom, overwrites=permissions,
                                                              category=category,
                                                              reason='User Created Custom Text Channel')
                    await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guildid,
                                         memID, channel.id, 'text')
                    await ctx.send("Custom Text Channel Created Successfully!")
            else:
                await ctx.send("You already have a custom text channel!")
        else:
            raise commands.MissingRole(missing.name) if missing is not None else commands.CommandError(
                f'Creating custom text channels have not been set up yet by server owner!')
        await self.bot.db.release(cursor)

    @createcustom.command(name='voice')
    async def create_voice(self, ctx, name, *, limit):
        cursor = await self.bot.db.acquire()
        author = ctx.message.author
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id

        roleauth = await cursor.fetchval("SELECT role FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
        missing = ctx.guild.get_role(roleauth)
        if roleauth in [role.id for role in ctx.author.roles]:
            # checks if we already have a custom voice channel
            result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                           guildid, memID, 'voice')
            if result is None:
                # checks which channel catagorey the newly created custom voice channel should be placed
                default = await cursor.fetchrow("SELECT position, tag FROM custom WHERE guild = $1 and system = $2",
                                                guildid, 'voice')
                custom = f"{name} ({default[1]})" if default[1] is not None else name
                # because of discord limitations, check the following
                if len(name) > 100:
                    await ctx.send("The channel name cannot be over 100 Characters!")
                elif int(limit) > 99:
                    await ctx.send("The user limit cannot be over 99 members!")
                else:
                    # creates custom voice channel and inserts channel information into our database for future use
                    category = guild.get_channel(default[0])
                    permissions = {guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
                                   author: discord.PermissionOverwrite(view_channel=True, connect=True,
                                                                       move_members=True)}
                    channel = await guild.create_voice_channel(custom, user_limit=limit, overwrites=permissions,
                                                               category=category,
                                                               reason='User Created Custom Voice Channel')
                    await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guildid,
                                         memID, channel.id, 'voice')
                    await ctx.send("Custom Voice Channel Created Successfully!")
            else:
                await ctx.send("You already have a custom voice channel!")
        else:
            raise commands.MissingRole(missing.name) if missing is not None else commands.CommandError(
                f'Creating custom voice channels have not been set up yet by server owner!')
        await self.bot.db.release(cursor)

    @commands.group(hidden=True, invoke_without_command=True)
    async def editcustom(self, ctx):
        """Allows you to edit your custom role, text channel or voice channel"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @editcustom.command(name='role')
    async def edit_role(self, ctx, color, *, name):
        """Allows you to edit your own cusotm role"""
        cursor = await self.bot.db.acquire()
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id

        # checks if the custom role does not exist
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                       guildid, memID, 'role')
        if result is not None:
            # gets our custom role
            role = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID,
                                         guildid, 'role')
            default = await cursor.fetchval("SELECT tag FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
            custom = f"{name} ({default})" if default is not None else name
            # because of discord limitations, check the following
            if not re.search(r"#([0-9a-fA-F]{6})", color):
                await ctx.send(f"The first argument Must Be A Hex")
            elif len(custom) > 50:
                await ctx.send(f"Role Name cannot be over 50 characters!")
            else:
                # edits our custom role
                crole = guild.get_role(role_id=role)
                await crole.edit(reason=None, name=name, color=discord.Colour(int(color[1:], 16)))
                await ctx.send("Custom Role Edited Successfully!")
        else:
            await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)

    @editcustom.command(name='text')
    async def edit_text(self, ctx, name, *, topic):
        """Allows you to edit your own custom text channel"""
        cursor = await self.bot.db.acquire()
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        # checks if the custom text channel does not exist
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                       guildid, memID, 'text')
        if result is not None:
            # gets our custom text channel
            channel = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3",
                                            memID, guildid, 'text')
            default = await cursor.fetchval("SELECT tag FROM custom WHERE guild = $1 and system = $2", guildid, 'text')
            custom = f"{topic} __**({default})**__" if default is not None else topic
            # because of discord limitations, check the following
            if len(topic) > 1024:
                await ctx.send("The channel topic cannot be over 1024 characters!")
            elif len(name) > 100:
                await ctx.send("The channel name cannot be over 100 characters!")
            else:
                # edits our custom text channel
                cchannel = guild.get_channel(channel)
                await cchannel.edit(name=name, topic=custom)
                await ctx.send("Custom Text Channel Edited Successfully!")
        else:
            await ctx.send(
                f"You need to have a custom text channel first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)

    @editcustom.command(name='voice')
    async def edit_voice(self, ctx, name, *, limit):
        """Allows you to edit your own cusotm voice channel"""
        cursor = await self.bot.db.acquire()
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        # checks if the custom voice channel does not exist
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                       guildid, memID, 'voice')
        if result is not None:
            # gets our custom voice channel
            channel = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3",
                                            memID, guildid, 'voice')
            default = await cursor.fetchval("SELECT tag FROM custom WHERE guild = $1 and system = $2", guildid, 'voice')
            custom = f"{name} ({default})" if default is not None else name
            # because of discord limitations, check the following
            if len(custom) > 100:
                await ctx.send("The channel name cannot be over 100 Characters!")
            elif int(limit) > 99:
                await ctx.send("The user limit cannot be over 99 members!")
            else:
                # edits our custom voice channel
                cchannel = guild.get_channel(channel)
                await cchannel.edit(name=name, user_limit=limit)
                await ctx.send("Custom Voice Channel Edited Successfully!")
        else:
            await ctx.send(
                f"You need to have a custom voice channel first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)

    @commands.group()
    async def deletecustom(self, ctx):
        """Deletes your custom role, text channel or voice channel that you have created"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @deletecustom.command(name='role')
    async def delete_role(self, ctx):
        """Allows you to delete your own custom role"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        # checks if the custom role exists           
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                       guildid, memID, 'role')
        if result is not None:
            # deletes our custom role
            role = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID,
                                         guildid, 'role')
            crole = guild.get_role(role)
            await crole.delete()
            await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4",
                                 guildid, role, memID, 'role')
            await ctx.send(f"Custom Role Deleted Successfully!")
        else:
            await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)

    @deletecustom.command(name='text')
    async def delete_text(self, ctx):
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        # checks if the custom text channel exists
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                       guildid, memID, 'text')
        if result is not None:
            # deletes our custom text channel
            channel = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3",
                                            memID, guildid, 'text')
            cchannel = guild.get_channel(channel)
            await cchannel.delete()
            await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4",
                                 guildid, channel, memID, 'text')
            await ctx.send(f"Custom Text Channel Deleted Successfully!")
        else:
            await ctx.send(
                f"You need to have a custom text channel first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)

    @deletecustom.command(name='voice')
    async def delete_voice(self, ctx):
        """Allows you to delete your own custom voice channel"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        # checks if the custom voice channel exists
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                       guildid, memID, 'voice')
        if result is not None:
            # deletes our custom voice channel
            channel = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3",
                                            memID, guildid, 'voice')
            cchannel = guild.get_channel(channel)
            await cchannel.delete()
            await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4",
                                 guildid, channel, memID, 'voice')
            await ctx.send(f"Custom Text Channel Deleted Successfully!")
        else:
            await ctx.send(
                f"You need to have a custom voice channel first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)

    @commands.group(
        description='Supply action with role/text/voice to give that custom and type with add/remove to add or remove an custom role')
    async def givecustom(self, ctx):
        """Allows you to add or remove your custom role, text channel or voice channel to someone"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @givecustom.command()
    async def role(self, ctx, action, *, member: discord.Member):
        """Allows you to add or remove your custom role to someone"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        number = await cursor.fetchval("SELECT amount FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
        result = await cursor.fetchval("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid,
                                       memID, 'role')
        # checks if the custom role exists
        if result is not None:
            crole = guild.get_role(result)
            if action not in ("add", "remove"):
                await ctx.send("The 'type' argument must be defined as add or remove")
            elif memID == member.id:
                await ctx.send("You cannot Add or Remove custom roles you already own to yourself")
            else:
                if not member.bot and crole.id not in [role.id for role in member.roles] and action in "add":
                    # checks if we have more members than is allowed
                    if len(crole.members) > number:
                        await ctx.send(f"You can only give this custom role to an max of {number} members")
                    else:
                        await member.add_roles(crole)
                elif not member.bot and crole.id in [role.id for role in member.roles] and action in "remove":
                    await member.remove_roles(crole)
                await ctx.send(content=f"Successfully {action} custom role to {member.name}")
        else:
            await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)

    @givecustom.command()
    async def text(self, ctx, action, *, member: discord.Member):
        """Allows you to add or remove your custom text channel to someone"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        number = await cursor.fetchval("SELECT amount FROM custom WHERE guild = $1 and system = $2", guildid, 'text')
        result = await cursor.fetchval("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid,
                                       memID, 'text')
        # checks if the custom text channel exxists
        if result is not None:
            cchannel = guild.get_channel(result)
            if action not in ("add", "remove"):
                await ctx.send("The 'type' argument must be defined as add or remove")
            elif memID == member.id:
                await ctx.send("You cannot Add or Remove custom text channels you already own to yourself")
                return
            else:
                if not member.bot and not cchannel.permissions_for(member).read_messages and action == "add":
                    # checks if we have more members than is allowed
                    if len(cchannel.members) > number:
                        await ctx.send(
                            f"You can only give this custom text channel access to an max of {number} members")
                        return
                    else:
                        await cchannel.set_permissions(member, read_messages=True, send_messages=True)
                elif not member.bot and cchannel.permissions_for(member).read_messages and action in "remove":
                    await cchannel.set_permissions(member, overwrite=None)
                await ctx.send(content=f"Successfully {action} custom text channel access to {member.name}")
        else:
            await ctx.send(
                f"You need to have a custom text channel first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)

    @givecustom.command()
    async def voice(self, ctx, action, *, member: discord.Member):
        """Allows you to add or remove your custom voice channel to someone"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        result = await cursor.fetchval("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid,
                                       memID, 'voice')
        # checks if the custom voice channel exists
        if result is not None:
            number = await cursor.fetchval("SELECT amount FROM custom WHERE guild = $1 and system = $2", guildid,
                                           'voice')
            cchannel = guild.get_channel(result)
            if action not in ("add", "remove"):
                await ctx.send("The 'type' argument must be defined as add or remove")
            elif memID == member.id:
                await ctx.send("You cannot Add or Remove custom text channels you already own to yourself")
            else:
                if not member.bot and not cchannel.permissions_for(member).view_channel and action == "add":
                    # checks if we have more members than is allowed
                    if len(cchannel.members) > number:
                        await ctx.send(
                            f"You can only give this custom voice channel access to an max of {number} members")
                    else:
                        await cchannel.set_permissions(member, view_channel=True, connect=True)
                elif not member.bot and cchannel.permissions_for(member).view_channel and action in "remove":
                    await cchannel.set_permissions(member, overwrite=None)
                await ctx.send(f"Successfully {action} custom voice channel access to {member.name}")
        else:
            await ctx.send(
                f"You need to have a custom voice channel first! Use `{ctx.prefix}createcustom` to create one!")
        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Utilities(bot))
