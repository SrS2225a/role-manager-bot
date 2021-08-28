import asyncpg
import asyncio
import datetime
import random
import re
import traceback

import discord
from discord.ext import commands, tasks


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # creates a cooldown mapping for messages and voice
        self._cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.member)
        self.__cd = commands.CooldownMapping.from_cooldown(1.0, 80.0, commands.BucketType.default)

        # turns the function dispatch_timers() into a discord.py task loop
        self._have_data = asyncio.Event(loop=bot.loop)
        self._current_timer = None
        self._task = bot.loop.create_task(self.dispatch_timers())

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

    # if the cog gets unloaded in someway, stop all current running tasks
    def cog_unload(self):
        self._task.cancel()

    async def create_timer(self, argument, connection=None):
        # creates a timer
        member = argument[0]
        now = datetime.datetime.now()
        delta = now + datetime.timedelta(seconds=int(argument[3]))
        await connection.execute("INSERT INTO autorole(guild, member, role, date, action) VALUES($1, $2, $3, $4, $5)",
                             member.guild.id, member.id, argument[1], delta, argument[2])
        if self._current_timer and delta < self._current_timer[3] or self._current_timer is None:
            # restarts the task if the sleep time is less than the current timer
            if (delta - now).total_seconds() <= (86400 * 48):  # 48 days
                self._have_data.set()
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

    async def wait_for_active_timers(self, *, connection=None, days=None):
        # if a timer exists start it where the date is less than the current timestamp,
        # else wait until one becomes available
        timer = await connection.fetchrow(
            "SELECT * FROM autorole WHERE date < (CURRENT_DATE + $1::interval) ORDER BY date LIMIT 1",
            datetime.timedelta(days=days))
        if timer is not None:
            self._have_data.set()
            return timer

        self._have_data.clear()
        self._current_timer = None
        await self._have_data.wait()
        return timer

    async def dispatch_timers(self):
        try:
            while not self.bot.is_closed():
                async with self.MaybeAcquire(connection=None, pool=self.bot.db) as con:
                    now = datetime.datetime.now()
                    timer = self._current_timer = await self.wait_for_active_timers(connection=con, days=48)
                    if timer[3] > now:
                        to_sleep = (timer[3] - now).total_seconds()
                        await asyncio.sleep(to_sleep)

                    await con.execute("DELETE FROM autorole WHERE member = $1 and guild = $2 and role = $3 and date = $4",
                                      timer[1], timer[0], timer[2], timer[3])

                    await self.call_timers(timer)

        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError, asyncio.CancelledError):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())
            raise

    async def call_timers(self, timer):
        try:
            server = self.bot.get_guild(timer[0])
            user = await server.fetch_member(timer[1])
            role = server.get_role(timer[2])
            if timer[4]:
                await user.add_roles(role)
            else:
                await user.remove_roles(role)
        except (discord.Forbidden, discord.NotFound):
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        # set the bots custom status
        print(
            f'\n\nCreated by: Nyx#8614 and Vendron#2001\nLogged in as: {self.bot.user} - {self.bot.user.id}\ndiscord'
            f'.py Version: {discord.__version__}\n')
        await self.bot.change_presence(activity=discord.Game("the greek multi-bot @ dionysus.gg"),
                                       status=discord.Status.online, afk=None)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # FOR LEVELING

        # checks if we are a real user
        if message.guild is not None and not message.author.bot:
            async with self.bot.db.acquire() as cursor:
                async with cursor.transaction():
                    # code for message graph
                    # increment member messages by 1 else add on a new date
                    date = datetime.date.today()
                    dateval = await cursor.prepare(
                        "SELECT messages, day, member, channel FROM message WHERE guild = $1 and member = $2 and "
                        "channel = $3 and day = $4 LIMIT 1")
                    dateval = await dateval.fetchrow(message.author.guild.id, message.author.id, message.channel.id,
                                                     date)

                    if dateval is None:
                        await cursor.execute("DELETE FROM message WHERE day < $1",
                                             (date - datetime.timedelta(days=120)))
                        await cursor.execute(
                            "INSERT INTO message(guild, messages, day, member, channel) VALUES($1, $2, $3, $4, "
                            "$5) on conflict do nothing",
                            message.author.guild.id, 1, date, message.author.id, message.channel.id)
                    else:
                        await cursor.execute(
                            "UPDATE message SET messages = $1 WHERE day = $2 and guild = $3 and member = $4 and "
                            "channel = $5",
                            dateval[0] + 1, dateval[1], message.author.guild.id, message.author.id, message.channel.id)

                    # ranking cooldown ratelimiter
                    retry_after = self._cd.update_rate_limit(message)
                    if not retry_after:

                        # checks if the guild has enabled ranking and role/channel not in blacklist
                        enabled = await cursor.prepare(
                            "SELECT difficulty FROM leveling WHERE guild = $1 and system = $2")
                        difficulty = await enabled.fetchval(message.guild.id, 'difficulty')
                        if difficulty is not None:
                            blacklist = await cursor.prepare(
                                "SELECT role FROM leveling WHERE guild = $1 and system = $2")
                            blacklist = await blacklist.fetch(message.author.guild.id, 'blacklist')
                            if [no[0] for no in blacklist] != message.channel.id or [no[0] for no in blacklist] \
                                    not in [role.id for role in message.author.roles]:
                                result = await cursor.prepare(
                                    "SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2 LIMIT 1")
                                result = await result.fetchrow(message.author.guild.id, message.author.id)
                                if result is None:
                                    await cursor.execute(
                                        "INSERT INTO levels(guild_id, user_id, channel_id, exp, lvl) VALUES($1,$2,$3,"
                                        "$4,$5)", message.author.guild.id, message.author.id, message.channel.id, 0, 1)
                                    result = [message.author.id, 0, 1]

                                # checks if we have leveled up then updates the members level, else just give them xp
                                if int(100 * result[2] * difficulty / 3) < result[1]:
                                    lvl_start = result[2] + 1
                                    embed = discord.Embed(title='Congratulations!',
                                                          description=f'{message.author.mention} has just leveled up '
                                                                      f'to level {lvl_start}')
                                    embed.set_thumbnail(url=message.author.avatar_url)
                                    await message.channel.send(embed=embed)
                                    await cursor.execute(
                                        "UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and user_id = $4",
                                        lvl_start, 0, message.guild.id, message.author.id)

                                    # checks if we should replace the level role, or just add it
                                    levels = await cursor.fetch(
                                        "SELECT level, role FROM leveling WHERE guild = $1 and system = $2",
                                        message.author.guild.id, 'levels')
                                    check = await cursor.fetchval(
                                        "SELECT type FROM leveling WHERE guild = $1 and system = $2 LIMIT 1",
                                        message.author.guild.id, 'keep') or 1
                                    for level in levels:
                                        if lvl_start >= level[0] and check == 1:
                                            lvl_role = message.guild.get_role(level[1])
                                            await message.author.add_roles(lvl_role, reason='User leveled up')
                                        elif lvl_start >= level[0] and check == 0:
                                            lvl_role = message.guild.get_role(level[1])
                                            await message.author.add_roles(lvl_role, reason='User leveled up')

                                            for role in levels:
                                                if role[0] in [role.id for role in message.author.roles] \
                                                        and role[0] != lvl_role.id:
                                                    roles = message.guild.get_role(role_id=role[0])
                                                    await message.author.remove_roles(roles,
                                                                                      reason='Leveling Role Replace')
                                else:
                                    weight = await cursor.fetch(
                                        "SELECT role, difficulty, system FROM leveling WHERE guild = $1 and system = "
                                        "$2 or system = $3",
                                        message.author.guild.id, 'multiplier', 'message')
                                    if weight:
                                        value = 0
                                        for multi in weight:
                                            if multi[2] == 'message' or multi[0] == message.channel.id or multi[0] \
                                                    in [role.id for role in message.author.roles]:
                                                value += multi[1]
                                    else:
                                        value = 8

                                    await cursor.execute(
                                        "UPDATE levels SET exp = $1, channel_id = $2 WHERE guild_id = $3 and user_id "
                                        "= $4",
                                        result[1] + random.randint(1, value), message.channel.id, message.guild.id,
                                        message.author.id)

                    # FOR COUNTING
                    count = await cursor.prepare(
                        "SELECT channel, role, member, number, count, delay FROM count WHERE guild = $1 LIMIT 1")
                    current = await count.fetchrow(message.guild.id)

                    # checks if we have counted in the correct channel and continue
                    if current is not None and current[0] == message.channel.id:
                        channel = message.guild.get_channel(current[0])
                        role = message.guild.get_role(current[1])

                        # updates count if we are not the same member or made a mistake
                        if current[2] != message.author.id:
                            if message.content == str(current[3]):
                                await cursor.execute("UPDATE count SET number = $1, member = $2 WHERE guild = $3",
                                                     current[3] + 1, message.author.id, message.guild.id)
                                # if enabled update channel topic to the new number
                                if current[4]:
                                    level = current[3] + 1
                                    text = re.match(r"(\D*)\d*", channel.topic).group(
                                        1) if channel.topic is not None else 'The next number is: '
                                    topic = f"{text}{level}".strip()
                                    await channel.edit(topic=topic, reason='New Counter Number')
                            else:
                                await message.delete()
                                await channel.send(f"{message.author.mention} just forgot how to count!",
                                                   delete_after=4.7)
                                # if enabled disable us from counting for a bit 
                                if current[5] > 0:
                                    await message.author.add_roles(role)
                                    await asyncio.sleep(current[5])
                                    await message.author.remove_roles(role)
                        else:
                            await message.delete()
                            await channel.send(f"{message.author.mention} is lonely and needs someone to count with!",
                                               delete_after=4.7)

                    # FOR PARTNERSHIPS
                    allowed = await cursor.prepare(
                        "SELECT type, role, level, difficulty, number, announce FROM leveling FULL JOIN partner USING "
                        "(guild) JOIN settings USING (guild) WHERE guild = $1 and system = $2 LIMIT 1")
                    partner = await allowed.fetchrow(message.guild.id, 'partners')
                    # checks if partnerships tracking been enabled
                    if partner is not None:
                        role = message.guild.get_role(partner[1])
                        if partner[0] == message.channel.id and role.id in [role.id for role in message.author.roles]:
                            # checks if the partner manager has completed an partnership, then give them a point
                            if re.search(r".*[https://]?discord(.*(gg))\S?\w{7}.*\n?", message.content):
                                if partner[4] is None:
                                    await cursor.execute(
                                        "INSERT INTO partner(guild, member, number) VALUES($1, $2, $3)",
                                        message.guild.id, message.author.id, 1)
                                else:
                                    amount = partner[4] + 1
                                    await cursor.execute(
                                        "UPDATE partner SET number = $1 WHERE guild = $2 and member = $3", amount,
                                        message.guild.id, message.author.id)
                                    # if enabled congratulates the partner manager if they complete a number of
                                    # partnerships
                                    if amount >= partner[2]:
                                        reward = message.guild.get_role(partner[3])
                                        chan = message.guild.get_channel(partner[5])
                                        if chan is not None and reward.id not in [role.id for role in
                                                                                  message.author.roles]:
                                            await chan.send(
                                                f"Congrats to {message.author.mention} for completing {amount}"
                                                f" partnerships for {message.guild}!")
                                        if reward is not None:
                                            await message.author.add_roles(reward)

                    # FOR AFK
                    afk = await cursor.prepare("SELECT member, message, count FROM afk WHERE guild = $1")
                    channel = message.channel
                    member = message.author
                    for user in await afk.fetch(message.guild.id):
                        # checks the the member marked as AFK talked then removes them as AFK automatically
                        if user[0] == member.id:
                            if user[2] >= 3:
                                try:
                                    nick = member.display_name
                                    await member.edit(nick=nick.split('[AFK]')[0])
                                except discord.Forbidden:
                                    pass
                                await cursor.execute("DELETE FROM afk WHERE guild = $1 and member = $2", message.guild.id,
                                                     message.author.id)
                                await channel.send(f"{message.author.mention} I marked you as no longer AFK!")
                            else:
                                await cursor.execute("UPDATE afk SET count = $1 WHERE guild = $2 and member = $3",
                                                     user[2]+1, message.guild.id, message.author.id)
                        # checks if the mentioned user is afk, and if they are, tell the member that mentioned them
                        elif user[0] in [msg.id for msg in message.mentions]:
                            him = message.guild.get_member(user[0])
                            await channel.send(
                                f"{message.author.mention} {him} is currently AFK with the reason: {user[1]}!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        # VOICE ROLES
        guild = member.guild
        async with self.bot.db.acquire() as cursor:
            async with cursor.transaction():
                date = datetime.date.today()
                channel = before.channel or after.channel
                await cursor.execute("DELETE FROM message WHERE day < $1", (date - datetime.timedelta(days=120)))
                voices = await cursor.prepare(
                    "SELECT voice, voice2, day, member, channel, created FROM voice WHERE guild = $1 AND member "
                    "= $2 and channel = $3 and day = $4 LIMIT 1")
                dateval = await voices.fetchrow(member.guild.id, member.id, channel.id, date)
                if dateval is not None:
                    if after.channel is None:
                        time = (datetime.datetime.now() - dateval[5]).total_seconds()
                        if type(channel) is discord.VoiceChannel:
                            await cursor.execute("UPDATE voice SET voice = $1 WHERE day = $2 and "
                                                 "guild = $3 and member = $4 and channel = $5", time + dateval[0],
                                                 date, member.guild.id, member.id, channel.id)
                        else:
                            await cursor.execute("UPDATE voice SET voice2 = $1 WHERE day = $2 and "
                                                 "guild = $3 and member = $4 and channel = $5", time + dateval[1],
                                                 date, member.guild.id, member.id, channel.id)
                    elif before.channel is None:
                        await cursor.execute("UPDATE voice SET created = $1 WHERE day = $2 and guild = $3 and "
                                             "member = $4 and channel = $5", datetime.datetime.now(), date,
                                             member.guild.id, member.id, channel.id)
                elif dateval is None:
                    await cursor.execute("INSERT INTO voice(voice, voice2, day, channel, member, guild, created) "
                                         "VALUES($1, $2, $3, $4, $5, $6, $7)" "on conflict do nothing", 0, 0, date,
                                         after.channel.id, member.id, channel.guild.id, datetime.datetime.now())

                voice = await cursor.prepare("SELECT role, date::int8 FROM boost WHERE guild = $1 and type = $2")
                for channel in await voice.fetch(member.guild.id, 'voice'):
                    role = guild.get_role(role_id=channel[0])
                    # if enabled gives the set role if the member joined the corresponding vc
                    if channel[1] != after.channel.id:
                        await member.remove_roles(role, reason='User left VC')
                    # if enabled removes the set role if the member left the corresponding vc
                    elif channel[1] == after.channel.id:
                        await member.add_roles(role, reason='User joined VC')

                # FOR LEVELING
                # an handler for vc rankings
                difficulty = await cursor.prepare(
                    "SELECT difficulty FROM leveling WHERE guild = $1 and system = $2 LIMIT 1")
                if await difficulty.fetchval(member.guild.id, 'difficulty') is not None:
                    # checks if the guild has enabled rankings and if the member not in blacklist
                    vcchannel = 0 if after.channel is None else after.channel.id
                    blacklist = await cursor.prepare("SELECT role FROM leveling WHERE guild = $1 and system = $2")
                    blacklist = await blacklist.fetch(member.guild.id, 'blacklist')
                    if [no[0] for no in blacklist] != vcchannel or [no[0] for no in blacklist] \
                            not in [role.id for role in member.author.roles]:
                        # starts the task if there is a member in the vc channel, add them to loop through;
                        # and is not afk, deafened, or muted
                        if after.deaf or after.mute or after.self_mute or after.self_deaf or after.afk is True or None \
                                or after.channel is None:
                            self.bot.active.remove([member, after])
                            if not self.bot.active:
                                self.vc.cancel()
                        elif member not in self.bot.active:
                            self.bot.active.append([member, after])
                            if self.bot.active and len(self.bot.active) == 1:
                                self.vc.start()

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        async with self.bot.db.acquire() as cursor:
            async with cursor.transaction():
                guild = after.guild

                # for custom roles / text channels / voice channels
                if before.roles != after.roles:
                    roleauth = await cursor.prepare(
                        "SELECT custom.role, remove, roles.role, type FROM custom INNER JOIN roles USING(guild) WHERE "
                        "roles.guild = $1 and member = $2 and not type = $3")

                    # if enabled deletes the created custom role/text channel/voice channel once the set required
                    # role gets removed
                    for roleauth in await roleauth.fetch(guild.id, after.id, 'sticky'):
                        if roleauth[0] not in [role.id for role in after.roles] and roleauth[1] is True:
                            custom = guild.get_role(roleauth[2]) if roleauth[3] == 'role' else guild.get_channel(
                                roleauth[2])
                            if custom is not None:
                                await cursor.execute(
                                    "DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4",
                                    guild.id, custom.id, after.id, roleauth[3])
                                await custom.delete(reason='Required Role/Channel Was Removed From Member')

                    # for sticky roles
                    master = await cursor.prepare(
                        "SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3")
                    # if enabled gives back the set role(s) if an member left with said role
                    for user in await master.fetch(guild.id, after.id, 'sticky'):
                        if user[0] in [role.id for role in after.roles] and type is None:
                            await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)",
                                                 guild.id, after.id, user[0], 'sticky')
                        if user[0] not in [role.id for role in after.roles] and type is not None:
                            await cursor.execute(
                                "DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4",
                                guild.id, user[0], after.id, 'sticky')

                # detects if an user is streaming and gives them the set role accordingly, else remove it
                if before.activities != after.activities:
                    stream = await cursor.prepare("SELECT live FROM settings WHERE guild = $1 LIMIT 1")
                    role = guild.get_role(await stream.fetchval(guild.id))
                    if role is not None:
                        if discord.Streaming in [type(x) for x in after.activities]:
                            await after.add_roles(role, reason='User Is Streaming')
                        else:
                            await after.remove_roles(role, reason='User is no longer Streaming')

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.TextChannel, after: discord.TextChannel) -> None:
        # OVERWRITES RECOVERY
        if before.overwrites != after.overwrites:
            async with self.bot.db.acquire() as cursor:
                async with cursor.transaction():
                    guild = after.guild
                    channel = after
                    recovery = await cursor.prepare(
                        "SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1")
                    role = guild.get_role(await recovery.fetchval(guild.id, channel.id, 'recover'))
                    users = []
                    # if an user has channel overwrites and they have the correct set role on them, insert or update the
                    # channel overwrites to give back once the user rejoins the guild
                    if role is not None:
                        for perm, value in channel.overwrites.items():
                            if isinstance(perm, discord.Member) and role.id in [role.id for role in perm.roles]:
                                users.append(perm.id)
                                check = await cursor.fetchrow(
                                    "SELECT member FROM recover WHERE guild = $1 and member = $2 and channel = $3 "
                                    "LIMIT 1",
                                    guild.id, perm.id, channel.id)
                                yes = value.pair()[0].value
                                no = value.pair()[1].value
                                if check is None:
                                    await cursor.execute(
                                        "INSERT INTO recover(guild, channel, member, yes, no) VALUES($1, $2, $3, $4, "
                                        "$5) on conflict do nothing",
                                        guild.id, channel.id, perm.id, yes, no)
                                else:
                                    await cursor.execute(
                                        "UPDATE recover SET yes = $1, no = $2 WHERE guild = $3 and channel = $4 and "
                                        "member= $5",
                                        yes, no, guild.id, channel.id, perm.id)

                        # if the user has their channel overwrites removed, delete them from the database
                        member = await cursor.fetch(
                            "SELECT member, channel FROM recover WHERE guild = $1 and channel = $2", guild.id,
                            channel.id)
                        for removed in member:
                            if removed[0] not in users:
                                await cursor.execute(
                                    "DELETE FROM recover WHERE guild = $1 and member = $2 and channel = $3", guild.id,
                                    removed[0], removed[1])

    @commands.Cog.listener()
    async def on_invite_update(self, member, invite):
        async with self.bot.db.acquire() as cursor:
            async with cursor.transaction():
                exists = await cursor.prepare("SELECT invite FROM invite WHERE guild = $1 and invite = $2 LIMIT 1")
                exists = await exists.fetchval(member.guild.id, invite.code)
                if exists is not None:
                    await cursor.execute(
                        "UPDATE invite SET amount = $1 WHERE guild = $2 and invite = $3",
                        invite.uses, member.guild.id,
                        invite.code)
                else:
                    await cursor.execute(
                                "INSERT INTO invite(guild, member, invite, amount, amount2,amount3) "
                                "VALUES($1, $2, $3, $4, $5, $6)", member.guild.id, invite.inviter.id,
                                invite.code, invite.uses, 0, 0)
                await cursor.execute(
                    "INSERT INTO invite2(guild, member, invite) VALUES($1, $2, $3)",
                    member.guild.id, member.id, invite.code)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        async with self.bot.db.acquire() as cursor:
            async with cursor.transaction():
                guild = member.guild

                # code for member join graph
                # increment member joins by 1 else add on a new date
                date = datetime.date.today()
                dateval = await cursor.prepare("SELECT joins FROM member WHERE guild = $1 and day = $2 LIMIT 1")
                dateval = await dateval.fetchval(guild.id, date)

                if dateval is None:
                    await cursor.execute("DELETE FROM member WHERE day < $1", (date - datetime.timedelta(days=120)))
                    await cursor.execute(
                        "INSERT INTO member(guild, joins, leaves, day) VALUES($1, $2, $3, $4) on conflict do nothing",
                        guild.id, 1, 0, date)
                else:
                    await cursor.execute("UPDATE member SET joins = $1 WHERE day = $2 and guild = $3", dateval + 1,
                                         date, guild.id)

                # code for autoroles
                # gets autroles to add/remove
                auto = await cursor.prepare("SELECT role, member, type FROM roles WHERE guild = $1 and type = $2 or "
                                            "type = $3")
                execute = await auto.fetch(guild.id, "add", "remove")
                for auto in execute:
                    role = guild.get_role(role_id=auto[0])
                    if role is not None:
                        if auto[2] == "add":
                            if auto[1] > 0:
                                # if we are waiting a certain amount of time to add the role, create a timer
                                await self.create_timer([member, auto[0], True, auto[1]], cursor)
                            else:
                                await member.add_roles(role, reason='Auto role')
                        elif auto[2] == "remove":
                            if auto[1] > 0:
                                # if we are waiting a certain amount of time to remove the role, create a timer
                                await self.create_timer([member, auto[0], False, auto[1]], cursor)
                            else:
                                await member.remove_roles(role, reason='Auto role')

                # if the user had sticky role(s) when they left, give the role back to them
                # if configured to do so
                master = await cursor.prepare("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3")
                for select in await master.fetch(guild.id, member.id, 'sticky'):
                    if select[0] not in [role.id for role in member.roles] and select[0] is not None:
                        srole = guild.get_role(role_id=int(select[0]))
                        await member.add_roles(srole, reason='User had sticky roles when leaving')

                # code for channel overwrites recovery
                override = await cursor.prepare("SELECT yes, no, channel FROM recover WHERE guild = $1 and member = $2")
                for override in await override.fetch(guild.id, member.id):
                    # gets channel, member's previous channel overwrites for channel, and then set channel permissions
                    # for that member
                    channel = guild.get_channel(override[2])
                    yes = discord.Permissions(permissions=int(override[0]))
                    no = discord.Permissions(permissions=int(override[1]))
                    overrides = discord.PermissionOverwrite().from_pair(yes, no)
                    await channel.set_permissions(member, overwrite=overrides, reason='user joined back with previous '
                                                                                      'channel overwrites')

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        async with self.bot.db.acquire() as cursor:
            async with cursor.transaction():
                await cursor.execute("DELETE FROM autorole WHERE guild = $1 and member = $2", member.guild.id,
                                     member.id)
                if self._current_timer is not None and self._current_timer[1] == member.id:
                    self._task.cancel()
                    self._task = self.bot.loop.create_task(self.dispatch_timers())

                # if enabled deletes the user from leveling if they left the guild
                clear = await cursor.prepare("SELECT type FROM leveling WHERE guild = $1 and system = $2 LIMIT 1")
                if await clear.fetchval(member.guild.id, 'clear') == 1:
                    await cursor.execute("DELETE FROM levels WHERE guild_id = $1 and user_id = $2", member.guild.id,
                                         member.id)

                # code for member join graph
                date = datetime.date.today()
                dateVal = await cursor.prepare("SELECT leaves FROM member WHERE guild = $1 and day = $2 LIMIT 1")
                dateVal = await dateVal.fetchval(member.guild.id, date)

                if dateVal is None:
                    await cursor.execute("DELETE FROM member WHERE day < $1", (date - datetime.timedelta(days=120)))
                    await cursor.execute("INSERT INTO member(guild, joins, leaves, day) VALUES($1, $2, $3, $4)",
                                         member.guild.id, 0, 1, date)
                else:
                    await cursor.execute("UPDATE member SET leaves = $1 WHERE day = $2 and guild = $3", dateVal + 1,
                                         date, member.guild.id)

                # updates the inviters invite leaves if the user left the guild
                amount = await cursor.prepare("SELECT invite FROM invite2 WHERE guild = $1 and member = $2 LIMIT 1")
                amount = await amount.fetchval(member.guild.id, member.id)
                check = await cursor.prepare("SELECT amount2, amount3 FROM invite WHERE guild = $1 and invite = $2 "
                                             "LIMIT 1")
                check = await check.fetchrow(member.guild.id, amount)

                # detects if the leave was a fake join
                await cursor.execute("DELETE FROM invite2 WHERE member = $1 and guild = $2", member.id, member.guild.id)
                if check:
                    var = list(check)
                    if (datetime.datetime.now() - member.joined_at).total_seconds() < 90:
                        var[1] += 1
                    else:
                        var[0] += 1
                    await cursor.execute("UPDATE invite SET amount2 = $1, amount3 = $2 WHERE guild = $3 and invite = $4",
                                         var[0], var[1], member.guild.id, amount)

                # removes the member custom channels / roles if they had them when leaving
                roleauth = await cursor.prepare(
                    "SELECT role, type FROM roles WHERE guild = $1 and member = $2 and not type = $3")
                for roleauth in await roleauth.fetch(member.guild.id, member.id, 'sticky'):
                    custom = member.guild.get_role(roleauth[0]) if roleauth[1] == 'role' else member.guild.get_channel(
                        roleauth[0])
                    if custom is not None:
                        await cursor.execute(
                            "DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4",
                            member.guild.id, custom.id, member.id, roleauth[1])
                        await custom.delete(reason='Required Role/Channel Was Removed From Member')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        async with self.bot.db.acquire() as cursor:
            async with cursor.transaction():
                # for reaction roles
                guild_id = payload.guild_id
                message_id = payload.message_id
                channel_id = payload.channel_id
                user_id = payload.user_id
                emoji = str(payload.emoji)
                main = message_id + channel_id

                # gives roles to an member once they react to an set emoji
                # adds support for custom emojis
                emote = re.findall(r'(\d+)\s*', emoji)
                if emote:
                    emoji = emote[0]

                # if enabled check if we are in the blacklist and continue
                whitelist = await cursor.fetch("SELECT role, blacklist FROM reaction WHERE master = $1 and guild = $2 "
                                               "and type = $3", main, guild_id, emoji)
                if whitelist:
                    role = random.choice(whitelist)
                    guild = self.bot.get_guild(guild_id)
                    member = await guild.fetch_member(user_id)
                    if role[1] not in [role.id for role in member.roles] and role[1] != 0:
                        await member.send("You do not have the required role to get this role from reaction roles!")
                    else:
                        roles = await cursor.fetch("SELECT role FROM reaction WHERE master = $1 and guild = $2",
                                                   main, guild_id)
                        channel = guild.get_channel(channel_id)
                        message = await channel.fetch_message(message_id)
                        # splits reaction role types into code readable format and checks if we can add role
                        # depending on the type
                        if "o" in role[0]:
                            role = role[0].replace("o", "")
                            mroles = guild.get_role(role_id=int(role))
                            for role in roles:
                                role = int(role[0].replace("o", ""))
                                if role in [role.id for role in member.roles]:
                                    await message.remove_reaction(payload.emoji, payload.member)
                                    await member.send("You cannot change your roles after reacting from this reaction "
                                                      "role category!")
                                    break
                                else:
                                    await member.add_roles(mroles, reason='User reacted to reaction role')

                        elif "n" in role[0]:
                            role = role[0].replace("n", "")
                            mroles = guild.get_role(role_id=int(role))
                            for role in roles:
                                role = int(role[0].replace("n", ""))
                                if role in [role.id for role in member.roles]:
                                    nroles = guild.get_role(role)
                                    await member.remove_roles(nroles, reason='User unreacted to reaction role')
                                    await message.remove_reaction(payload.emoji, payload.member)
                            await member.add_roles(mroles, reason='User reacted to reaction role')

                        elif "r" in role[0]:
                            role = role[0].replace("r", "")
                            mroles = guild.get_role(role_id=int(role))
                            await member.add_roles(mroles, reason='User reacted to reaction role')

                        # support for the clubs system
                        elif "c" in role[0]:
                            role = role[0].replace("c", "")
                            mroles = guild.get_role(role_id=int(role))
                            cblacklist = await cursor.fetchval("SELECT message FROM owner WHERE guild = $1 and member "
                                                               "= $2 and message = $3 and type = $4 LIMIT 1",
                                                               guild_id, user_id, message_id, 'club')
                            if cblacklist is not None:
                                await message.remove_reaction(payload.emoji, payload.member)
                            else:
                                await member.add_roles(mroles, reason='User reacted to reaction role')

                # for polls if set to single voting automatically removes the voters reaction role if they try to
                # vote for more than one thing
                multi = await cursor.prepare("SELECT win FROM vote WHERE guild = $1 and message = $2 and type = $3 "
                                             "LIMIT 1")
                multi = await multi.fetchval(guild_id, message_id, 'poll')
                if multi == 0:
                    emoji = self.bot.emoji[1648:1668][::-1]
                    count = 0
                    for reaction in message.reactions:
                        users = await reaction.users().flatten()
                        if payload.member in users and reaction.emoji in emoji:
                            count += 1
                            if count > 1:
                                await message.remove_reaction(payload.emoji, payload.member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload) -> None:
        # removes roles to an member once they unreact to an set emoji
        async with self.bot.db.acquire() as cursor:
            async with cursor.transaction():
                guild_id = payload.guild_id
                message_id = payload.message_id
                channel_id = payload.channel_id
                user_id = payload.user_id
                emoji = str(payload.emoji)
                main = message_id + channel_id

                # adds support for custom emojis
                emote = re.findall(r'(\d+)\s*', emoji)
                if emote:
                    emoji = emote[0]

                role = await cursor.fetchval("SELECT role FROM reaction WHERE master = $1 and type = $2 and guild = "
                                             "$3 LIMIT 1", main, emoji, guild_id)
                if role is not None:
                    # splits reaction role types into code readable format and checks if we can remove role
                    guild = self.bot.get_guild(guild_id)
                    member = await guild.fetch_member(user_id)
                    if 'r' in role or 'n' in role or 'c' in role:
                        role = re.findall(r'\d*', role)[1]
                        mrole = guild.get_role(role_id=int(role))
                        await member.remove_roles(mrole, reason='User unreacted to reaction role')

    @tasks.loop()
    async def vc(self):
        try:
            async with self.bot.db.acquire() as cursor:
                async with cursor.transaction():
                    # I'm too lazy to go into details with this
                    # all this does is do the same thing for chat leveling but for voice channels
                    # see on_message() event
                    for server in self.bot.active:
                        user = server[0]
                        voice = server[1]
                        retry_after = self.__cd.update_rate_limit(user)
                        if not retry_after:
                            difficulty = await cursor.prepare("SELECT difficulty FROM leveling WHERE guild = $1 and "
                                                              "system = $2 LIMIT 1")
                            difficulty = await difficulty.fetchval(user.guild.id, 'difficulty')
                            result1 = await cursor.prepare("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 "
                                                           "and user_id = $2 LIMIT 1")
                            result1 = await result1.fetchrow(user.guild.id, user.id)
                            if result1 is None:
                                await cursor.execute("INSERT INTO levels(guild_id, user_id, exp, lvl) VALUES($1,$2,"
                                                     "$3,$4)", user.guild.id, user.id, 0, 1)
                                result1 = [user.id, 0, 1]
                            if int(100 * result1[2] * difficulty / 3) < result1[1]:
                                lvl_start = result1[2] + 1
                                announcement = await cursor.fetchrow("SELECT channel_id FROM levels WHERE guild_id = "
                                                                     "$1 and user_id = $2 LIMIT 1", user.guild.id,
                                                                     user.id)
                                channel = user.guild.get_channel(announcement[0])
                                if channel is not None:
                                    embed = discord.Embed(title='Congratulations!', description=f'{user.mention} has '
                                                                                                f'leveled up to level'
                                                                                                f' {lvl_start}',
                                                          colour=discord.Colour.blue())
                                    embed.set_thumbnail(url=user.avatar_url)
                                    await channel.send(embed=embed)
                                await cursor.execute("UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and "
                                                     "user_id = $4", lvl_start, 0, user.guild.id, user.id)
                                levels = await cursor.fetchrow("SELECT level FROM leveling WHERE guild = $1 and "
                                                               "system = $2 LIMIT 1", user.guild.id, 'levels')
                                check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system "
                                                              "= $2 LIMIT 1", user.guild.id, 'keep') or 1
                                for level in levels:
                                    if lvl_start >= level[0] and check == 1:
                                        await cursor.execute("SELECT role FROM leveling WHERE guild = $1 and level = "
                                                             "$2 and system = $3", user.guild.id, lvl_start, 'levels')
                                        lvl_roles = cursor.fetchone()
                                        lvl_role = user.guild.get_role(lvl_roles)
                                        await user.add_roles(lvl_role, reason='User leveled up')
                                    elif lvl_start >= level[0] and check == 0:
                                        lvl_roles = await cursor.fetchrow("SELECT role FROM leveling WHERE guild = $1 "
                                                                          "and level = $2 and system = $3 LIMIT 1",
                                                                          user.guild.id, lvl_start, 'levels')
                                        lvl_role = user.guild.get_role(lvl_roles[0])
                                        await user.add_roles(lvl_role, reason='User leveled up')
                                        roles = await cursor.fetch("SELECT role FROM leveling WHERE guild = $1 and "
                                                                   "system = $2", user.guild.id, 'levels')

                                        for role in roles:
                                            if role[0] in [role.id for role in user.author.roles] \
                                                    and role[0] != lvl_role.id:
                                                roles = user.guild.get_role(role_id=role[0])
                                                await user.remove_roles(roles)
                            else:
                                weight = await cursor.fetch("SELECT role, difficulty, system FROM leveling WHERE "
                                                            "guild = $1 and system = $2 or system = $3",
                                                            user.guild.id, 'multiplier', 'voice')
                                if weight:
                                    value = 0
                                    for multi in weight:
                                        if multi[2] == 'voice' or multi[0] == voice.id or \
                                                multi[0] in [role.id for role in user.roles]:
                                            value += multi[1]
                                else:
                                    value = 12
                                await cursor.execute('UPDATE levels SET exp = $1 WHERE guild_id = $2 and user_id = $3',
                                                     result1[1] + random.randint(1, value), user.guild.id, user.id)
        except Exception:
            traceback.print_exc()

def setup(bot):
    bot.add_cog(Events(bot))
