import random
import re

import time

from colorama import Fore, Back

import discord
from discord.ext import commands, tasks

client = discord.Client()


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.member)
        self.__cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.default)

    # set the bots custom status
    @commands.Cog.listener()
    async def on_ready(self):
        game = discord.Game(f"*help | Version {self.bot.version}")
        await self.bot.change_presence(activity=game, status=discord.Status.online, afk=None)
        print('#-------------------------------#', Fore.WHITE)
        print('| ', Fore.RED + time.strftime("%#H:%M:%S") + Fore.WHITE + '  |  ', '➤ Dionysus Status -', Fore.GREEN, 'Online', Fore.WHITE)
        print('| ', Fore.RED + time.strftime("%#H:%M:%S") + Fore.WHITE + '  |  ', '➤ Logged in as:', Back.MAGENTA + Fore.BLACK, '[', self.bot.user, ']', Back.RESET + Fore.WHITE)
        print('#-------------------------------#', Fore.WHITE)
        print('| ', Fore.RED + time.strftime("%#H:%M:%S") + Fore.WHITE + '  |  ', '➤ ID:', Fore.CYAN, '[', self.bot.user.id, ']', Fore.WHITE)
        print('| ', Fore.RED + time.strftime("%#H:%M:%S") + Fore.WHITE + '  |  ', '➤ Token:', Back.RED + Fore.RED, '[', self.bot.token, ']', Back.RESET + Fore.WHITE)
        print('| ', Fore.RED + time.strftime("%#H:%M:%S") + Fore.WHITE + '  |  ', '➤ Prefix:', Fore.CYAN, '[', '*', ']', Fore.WHITE)
        print('| ', Fore.RED + time.strftime("%#H:%M:%S") + Fore.WHITE + '  |  ', '➤ Version:', Fore.CYAN, '[', self.bot.version, ']', Fore.WHITE)
        print('#-------------------------------#', Fore.WHITE)
        print('| ', Fore.RED + time.strftime("%#H:%M:%S") + Fore.WHITE + '  |  ', Fore.BLUE, 'Developers:', 'Nyx#8614', Fore.WHITE)
        print('#-------------------------------#', Fore.WHITE)
        print('| ', Fore.RED + time.strftime("%#H:%M:%S") + Fore.WHITE + '  |  ', ' Library Version:', Fore.MAGENTA, '[', discord.__version__, ']', Fore.WHITE)
        print('#-------------------------------#', Fore.WHITE)

    @commands.Cog.listener()
    async def on_message(self, message):
        # RANKING
        if message.guild is not None and not message.author.bot:
            retry_after = self._cd.update_rate_limit(message)
            cursor = await self.bot.db.acquire()
            # ranking cooldown ratelimiter
            if not retry_after:
                global results, channel, level, exp, check, dark
                diff1 = await cursor.fetchval("SELECT system FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'difficulty')
                blacklist = await cursor.fetch("SELECT role FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'blacklist')
                # checks if the guild has enabled ranking and user not in blacklist
                for no in blacklist:
                    if no[0] == message.channel.id or no[0] in [role.id for role in message.author.roles]:
                        dark = True
                else:
                    dark = False
                if diff1 is not None and dark is False:
                    difficulty = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'difficulty')
                    weight = await cursor.fetchval("SELECT COALESCE((SELECT difficulty FROM leveling WHERE guild = $1 and system = $2), 6)", message.author.guild.id, 'message')
                    check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'keep')
                    multiply = await cursor.fetch("SELECT role, difficulty FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'multiplier')
                    result = await cursor.fetchval(f"SELECT user_id FROM levels WHERE guild_id = $1 and user_id = $2", message.author.guild.id, message.author.id)

                    # checks if the member sending the message been ranked before, and if they haven't place them into the database
                    if result is None:
                        await cursor.execute("INSERT INTO levels(guild_id, user_id, channel_id, exp, lvl) VALUES($1,$2,$3,$4)", message.author.guild.id, message.author.id, message.channel.id, 0, 0)
                    else:
                        result1 = await cursor.fetchrow("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2", message.author.guild.id, message.author.id)

                        xp_start = result1[1]
                        lvl_start = result1[2]
                        xp_end = round(difficulty * result1[1] // 2 + difficulty * 8)
                        # checks if we have leveled up then updates the member level
                        if xp_end < xp_start:
                            lvl_start = lvl_start + 1
                            embed = discord.Embed(title='Congratulations!',
                                                  description=f'{message.author.mention} has leveled up to level {lvl_start}.',
                                                  colour=discord.Colour.blue())
                            embed.set_thumbnail(url=message.author.avatar_url)
                            await message.channel.send(embed=embed)
                            levels = await cursor.fetch("SELECT level FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'rank')
                            await cursor.execute("UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and user_id = $4", lvl_start, 0, message.guild.id, message.author.id)
                            for levels in levels:
                                if lvl_start >= levels[0] and check == 1:
                                    lvl_roles = await cursor.fetchrow("SELECT role FROM leveling WHERE guild = $1 and level = $2 and system = $3", message.author.guild.id, lvl_start, 'levels')
                                    lvl_role = message.guild.get_role(lvl_roles[0])
                                    await message.author.add_roles(lvl_role, reason='User leveled up')
                                elif lvl_start >= levels[0] and check == 0:
                                    lvl_roles = await cursor.fetchrow("SELECT role FROM leveling WHERE guild = $1 and level = $2 and system = $3", message.author.guild.id, lvl_start, 'levels')
                                    lvl_role = message.guild.get_role(lvl_roles[0])
                                    await message.author.add_roles(lvl_role, reason='User leveled up')
                                    roles = await cursor.fetch("SELECT role FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'rank')
                                    for role in roles:
                                        if role in [role.id for role in message.author.roles] and role != lvl_role.id:
                                            roles = message.guild.get_role(role_id=int(role))
                                            await message.author.remove_roles(roles, reason='Leveling Role Replace')
                        else:
                            for multi in multiply:
                                if multi[0] == message.channel.id or multi[0] in [role.id for role in message.author.roles]:
                                    weight += multi[1] ^ multi[1]
                            # if the above condition did not meet, just give the member exp instead
                            await cursor.fetchrow("UPDATE levels SET exp = $1, channel_id = $2 WHERE guild_id = $3 and user_id = $4", result1[1] + random.randint(0, weight), message.channel.id, message.guild.id, message.author.id)

            # AFK
            afk = await cursor.fetch("SELECT member, message FROM afk WHERE guild = $1", message.guild.id)
            channel = message.channel
            member = message.author
            for user in afk:
                # checks the the member marked as AFK talked then removes them as AFK
                if user[0] == member.id:
                    nick = member.nick.replace('[AFK]', '')
                    await member.edit(nick=nick)
                    await cursor.execute("DELETE FROM afk WHERE guild = $1 and member = $2", message.guild.id, message.author.id)
                    await channel.send(f"{message.author.mention} I marked you as no longer AFK!")
                elif user[0] in [msg.id for msg in message.mentions]:
                    him = message.guild.get_member(user[0])
                    await channel.send(f"{message.author.mention} {him} is currently AFK with the reason {user[1]}!")

            # PARTNERS
            requirement = await cursor.fetch(
                "SELECT type, role, level, difficulty FROM leveling WHERE guild = $1 and system = $2",
                message.guild.id, 'partners')
            result = await cursor.fetchrow("SELECT announce FROM settings WHERE announce = $1 and guild = $2",
                                           channel.id, message.guild.id)
            # checks if partnerships tracking been enabled
            chan = message.guild.get_channel(result[0]) if result is not None else None
            for partner in requirement:
                # checks if the pm has completed an partnership, then give them one point
                role = message.guild.get_role(partner[1])
                if message.channel.id == partner[0] and role.id in [role.id for role in message.author.roles]:
                    if re.search(r".*[https://]?discord(.*(gg))\S?\w{6}.*\n?", message.content):
                        user = await cursor.fetchrow("SELECT number FROM partner WHERE guild = $1 and member = $2",
                                                     message.guild.id, message.author.id)
                        if user is None:
                            await cursor.execute("INSERT INTO partner(guild, member, number) VALUES($1, $2, $3)",
                                                 message.guild.id, message.author.id, 1)
                        else:
                            # congratulates the pm if they meet the set threshold
                            user = user[0] + 1
                            if user >= partner[2]:
                                reward = message.guild.get_role(partner[3])
                                if chan is not None and reward.id not in [role.id for role in message.author.roles]:
                                    await chan.send(
                                        f"Congrats to {message.author.mention} for completing {user} partnerships for {message.guild}!")
                                await message.author.add_roles(reward)
                            await cursor.execute("UPDATE partner SET number = $1 WHERE guild = $2 and member = $3",
                                                 user, message.guild.id, message.author.id)
            await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # VOICE ROLES
        global dark
        cursor = await self.bot.db.acquire()
        guild = member.guild
        voice = await cursor.fetch("SELECT role, date::int8 FROM boost WHERE guild = $1 and type = $2", member.guild.id, 'voice')
        for channel in voice:
            role = guild.get_role(role_id=channel[0])
            # gives the set role if the member joined the corresponding vc
            if channel[1] != after.channel.id:
                await member.remove_roles(role, reason='User left VC')
            # removes the set role if the member left the corresponding vc
            elif channel[1] == after.channel.id:
                await member.add_roles(role, reason='User joined VC')

        # RANKING
        # an handler for vc rankings
        diff1 = await cursor.fetchval("SELECT system FROM leveling WHERE guild = $1 and system = $2", member.guild.id, 'difficulty')
        blacklist = await cursor.fetch("SELECT role FROM leveling WHERE guild = $1 and system = $2", member.guild.id, 'blacklist')
        # checks if the guild has enabled ranking and user not in blacklist
        for no in blacklist:
            if no[0] == member.channel.id or no[0] in [role.id for role in member.author.roles]:
                dark = True
            else:
                dark = False
        if diff1 is not None and dark is True:
            if after.deaf or after.mute or after.self_mute or after.self_deaf or after.afk is True or None or after.channel is None:
                self.bot.active.remove(member)
            else:
                self.bot.active.append(member)
            if self.bot.active and len(self.bot.active) == 1:
                self.vc.start()
            elif not self.bot.active:
                self.vc.cancel()
        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        cursor = await self.bot.db.acquire()
        global guild, member, role
        guildid = after.guild.id

        # detects if an user is streaming and gives an role accordingly
        if not before.activity == after.activity:
            guild = after.guild
            stream = await cursor.fetchrow("SELECT live FROM settings WHERE guild = $1", guildid)
            role = guild.get_role(role_id=stream)
            if role is not None:
                for activity in after.activities:
                    if activity.type == discord.ActivityType.streaming:
                        await after.add_roles(role, reason='User Is Streaming')
                    else:
                        await after.remove_roles(role, reason='User is no longer Streaming')

        # for public flags roles
        member = after
        for flag, value in member.public_flags:
            if value is True:
                public = await cursor.fetchval("SELECT role FROM boost WHERE guild = $1 and type = $2 and date = $3", member.guild.id, 'flag', flag)
                if public not in [role.id for role in member.roles] and public is not None:
                    role = guild.get_role(role_id=public)
                    await member.add_roles(role, reason='User has Public_Flags')

        # for custom roles
        if not before.roles == after.roles:
            guild = after.guild
            memberid = after.id
            member = after
            roleauth = await cursor.fetchval("SELECT role FROM custom WHERE guild = $1", guildid)
            result = await cursor.fetchval("SELECT remove FROM settings WHERE guild = $1", guildid)

            # if enabled deletes the created custom role once the set required role gets removed
            if roleauth not in [role.id for role in after.roles]:
                role = await cursor.fetchrow("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memberid, guildid, 'custom')
                if role is not None and "customrole" == result:
                    crole = await cursor.fetchrow(
                        "DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4",
                        guildid, role, memberid, 'custom')
                    guild.get_role(role_id=role)
                    await crole.delete(reason='Required Role Was Removed From Member')

        # for sticky roles
        master = await cursor.fetch("SELECT role FROM reward WHERE guild = $1 and type = $2", guildid, 'sticky')
        for n in master:
            n = n[0]
            # if enabled gives back an set role if an member left with said role
            type = await cursor.fetchrow(
                "SELECT role FROM roles WHERE role = $1 and guild = $2 and member = $3 and type = $4",
                n, guildid, after.id, 'sticky')
            if n in [role.id for role in after.roles] and type is None:
                await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)",
                                     guildid, after.id, n, 'sticky')
            if n not in [role.id for role in after.roles] and type is not None:
                await cursor.execute(
                    "DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4",
                    guildid, n, after.id, 'sticky')

        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        # OVERWRITES RECOVERY
        cursor = await self.bot.db.acquire()
        guild = after.guild
        channel = after
        recovery = await cursor.fetchrow("SELECT recovery FROM settings WHERE guild = $1", guild.id)
        memovr = await cursor.fetch("SELECT member, channel FROM recover WHERE guild = $1 and channel = $2",
                                       guild.id, channel.id)
        role = guild.get_role(recovery[0])
        users = []
        for perm, value in channel.overwrites.items():
            # if an user has defined channel overwrites on them and they have the set role on them insert the channel overwrites into the db to give them back if the user rejoins the guild
            if role is not None and isinstance(perm, discord.Member):
                if role.id in [role.id for role in perm.roles]:
                    users.append((perm.id, channel.id))
                    check = await cursor.fetchrow(
                        "SELECT member FROM recover WHERE guild = $1 and member = $2 and channel = $3",
                        guild.id, perm.id, channel.id)
                    yes = value.pair()[0].value
                    no = value.pair()[1].value
                    if check is None:
                        await cursor.execute(
                            "INSERT INTO recover(guild, channel, member, yes, no) VALUES($1, $2, $3, $4, $5)",
                            guild.id, channel.id, perm.id, yes, no)
                    else:
                        await cursor.execute(
                            "UPDATE recover SET yes = $1, no = $2 WHERE guild = $3 and channel = $4 and member= $5",
                            yes, no, guild.id, channel.id, perm.id)

            for removed in memovr:
                member = guild.get_member(removed[0])
                if removed not in users and member is not None:
                    await cursor.execute("DELETE FROM recover WHERE guild = $1 and member = $2 and channel = $3",
                                         guild.id, removed[0], removed[1])
        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        cursor = await self.bot.db.acquire()

        # for custom embeds

        # gives roles to an member once they react to an set emoji
        global word
        guild_id = payload.guild_id
        message_id = payload.message_id
        channel_id = payload.channel_id
        user_id = payload.user_id
        emoji = str(payload.emoji)
        main = message_id + channel_id
        emote = re.findall(r'(\d+)\s*', emoji)
        if emote:
            emoji = emote[0]
        chanmsg = await cursor.fetchval("SELECT master FROM reaction WHERE guild = $1 and type = $2 and master = $3",
                                        guild_id, emoji, main)
        # checks if we have actually reacted
        if chanmsg == main and not payload.member.bot:
            role = await cursor.fetchrow("SELECT role FROM reaction WHERE master = $1 and type = $2 and guild = $3",
                                         main, emoji, guild_id)
            role = random.choice(role)
            whitelist = await cursor.fetchval(
                "SELECT blacklist FROM reaction WHERE role = $1 and master = $2 and guild = $3 and type = $4",
                role, main, guild_id, emoji)
            roles = await cursor.fetch("SELECT role FROM reaction WHERE master = $1 and guild = $2", main, guild_id)
            # splits reaction role types into code readable format
            if "r" in str(role):
                word = "r"
                string = role.replace("r", "")
                role = string
            elif "o" in str(role):
                word = "o"
                string = role.replace("o", "")
                role = string
            elif "n" in str(role):
                word = "n"
                string = role.replace("n", "")
                role = string
            guild = self.bot.get_guild(guild_id)
            member = await guild.fetch_member(user_id)
            roless = guild.get_role(role_id=int(role))
            # if enabled check if we are in the whitelist and continue
            if whitelist not in [role.id for role in member.roles] and whitelist != 0:
                await member.send("You do not have the required role to get this role from reaction roles!")
                return

            # splits reaction role types into code readable format and checks if we can receive role
            elif "o" in word and member is not None:
                for role in roles:
                    string = role[0].replace("o", "")
                    role = string
                    for rolec in [role.id for role in member.roles]:
                        if str(role) == str(rolec):
                            await member.send(
                                "You cannot change your roles after reacting from this reaction role category!")
                            return
                await member.add_roles(roless, reason='User reacted to reaction role')

            elif "r" in word and member is not None:
                for role in roles:
                    string = role[0].replace("r", "")
                    role = string
                    if int(role) in [role.id for role in member.roles]:
                        roles = guild.get_role(role_id=int(role))
                        await member.remove_roles(roles, reason='User unreacted to reaction role')
                    await member.add_roles(roless, reason='User reacted to reaction role')

            elif "n" in word and member is not None:
                await member.add_roles(roless, reason='User reacted to reaction role')
        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        cursor = await self.bot.db.acquire()
        # removes roles to an member once they unreact to an set emoji
        guild_id = payload.guild_id
        message_id = payload.message_id
        channel_id = payload.channel_id
        user_id = payload.user_id
        emoji = str(payload.emoji)
        main = message_id + channel_id
        # support for custom emojis
        emote = re.findall(r'(\d+)\s*', emoji)
        if emote:
            emoji = emote[0]
        chanmsg = await cursor.fetchval("SELECT master FROM reaction WHERE guild = $1 and type = $2", guild_id, emoji)
        # checks if we have actually removed our reaction
        if main == chanmsg:
            role = await cursor.fetchval("SELECT role FROM reaction WHERE master = $1 and type = $2 and guild = $3", chanmsg, emoji, guild_id)
            # splits reaction role types into code readable format anmd checks if we can remove role
            if "r" in str(role):
                string = role.replace("r", "")
                role = string
            elif "n" in str(role):
                string = role.replace("n", "")
                role = string
            elif "o" in str(role):
                return
            guild = self.bot.get_guild(guild_id)
            member = await guild.fetch_member(user_id)
            if member is not None:
                roles = guild.get_role(role_id=int(role))
                await member.remove_roles(roles, reason='User unreacted to reaction role')
        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # updates users invite leaves if the joiner left the guild
        cursor = await self.bot.db.acquire()
        now = member.joined_at.timestamp()
        clear = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2", member.guild.id, 'clear')
        if clear is not None:
            await cursor.execute("DELETE FROM levels WHERE guild_id = $1 and user_id = $2", member.guild.id, member.id)
        amount = await cursor.fetchval(
            "SELECT invite FROM invite2 WHERE guild = $1 and member = $2 and timestamp = $3",
            member.guild.id, member.id, now)
        check = await cursor.fetchval("SELECT amount2 FROM invite WHERE guild = $1 and invite = $2",
                                     member.guild.id, amount)
        if check is None:
            check = 1
        else:
            check = check + 1
        await cursor.execute("UPDATE invite SET amount2 = $1 WHERE guild = $2 and invite = $3", check, member.guild.id, amount)
        await cursor.execute("DELETE FROM invite2 WHERE member = $1 and timestamp = $2", member.id, now)
        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        cursor = await self.bot.db.acquire()
        guildid = member.guild.id
        guild = member.guild
        auto = await cursor.fetchval("SELECT prefix FROM settings WHERE guild = $1", guildid)
        master = await cursor.fetch("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3",
                                    guildid, member.id, 'sticky')
        announcement = await cursor.fetchval("SELECT announce FROM settings WHERE guild = $1", guild.id)
        channel = guild.get_channel(announcement)

        # code for auto roles
        if auto not in [role.id for role in member.roles] and auto is not None:
            role = guild.get_role(role_id=auto)
            await member.add_roles(role, reason='Auto role')

        # code for sticky roles
        for select in master:
            if select[0] not in [role.id for role in member.roles] and select[0] is not None:
                srole = guild.get_role(role_id=int(select[0]))
                await member.add_roles(srole, reason='User had sticky roles when leaving')

        # code for invite rewards
        check = await cursor.fetch("SELECT date::int8, role FROM boost WHERE guild = $1 and type = $2 ORDER BY date DESC", guildid, 'invite')
        invite = await guild.invites()
        for invites in invite:
            amount = await cursor.fetchrow("SELECT amount FROM invite WHERE guild = $1 and member = $2 and invite = $3",
                                           guildid, invites.inviter.id, invites.code)
            if amount is not None and invites.uses > amount[0]:
                now = member.joined_at.timestamp()
                await cursor.execute("UPDATE invite SET amount = $1 WHERE guild = $2 and member = $3 and invite = $4",
                                     invites.uses, guildid, invites.inviter.id, invites.code)
                await cursor.execute("INSERT INTO invite2(guild, member, invite, timestamp) VALUES($1, $2, $3, $4)",
                                     guildid, member.id, invites.code, now)
                sum = await cursor.fetch("SELECT amount FROM invite WHERE guild = $1 and member = $2",
                                         guildid, invites.inviter.id)
                total = 0
                for i in sum:
                    total += i[0]
                for day in check:
                    role = guild.get_role(role_id=day[1])
                    if total == day[0]:
                        user = guild.get_member(invites.inviter.id)
                        if channel is not None and role.id not in [role.id for role in user.roles]:
                            await channel.send(
                                f"Congrats to {user.mention} for inviting {invites.uses} users to {guild}!")
                        await user.add_roles(role)
            elif amount is None:
                await cursor.execute(
                    "INSERT INTO invite(guild, member, invite, amount, amount2) VALUES($1, $2, $3, $4, $5)",
                    guildid, invites.inviter.id, invites.code, invites.uses, 0)

        # code for channel overwrites recovery
        for channel in guild.channels:
            override = await cursor.fetchrow(
                "SELECT yes, no FROM recover WHERE guild = $1 and member = $2 and channel = $3",
                guild.id, member.id, channel.id)
            if override is not None:
                yes = discord.Permissions(permissions=override[0])
                no = discord.Permissions(permissions=override[1])
                overrides = discord.PermissionOverwrite().from_pair(yes, no)
                await channel.set_permissions(member, overwrite=overrides,
                                              reason='user joined back with previous channel overwrites')
        await self.bot.db.release(cursor)

    @tasks.loop()
    async def vc(self):
        try:
            cursor = await self.bot.db.acquire()
            for user in self.bot.active:
                retry_after = self.__cd.update_rate_limit(user)
                # rate limited for vc ranking
                if not retry_after:
                    print(user)
                    # ranking for vc's
                    global check
                    difficulty = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", user.author.guild.id, 'difficulty')
                    weight = await cursor.fetchval("SELECT COALESCE((SELECT difficulty FROM leveling WHERE guild = $1 and system = $2), 6)", user.guild.id, 'voice')
                    check = await cursor.fetchval("SELECT type FROM leveling WHERE guild = $1 and system = $2", user.author.guild.id, 'keep')
                    multiply = await cursor.fetch("SELECT role, difficulty FROM leveling WHERE guild = $1 and system = $2", user.author.guild.id, 'multiplier')
                    result = await cursor.fetchval("SELECT user_id FROM levels WHERE guild_id = $1 and user_id = $2", user.guild.id, user.id)
                    if result is None:
                        await cursor.execute("INSERT INTO levels(guild_id, user_id, exp, lvl) VALUES($1,$2,$3,$4)",
                                       user.guild.id, user.id, 0, 0)
                    else:
                        result1 = await cursor.fetchrow("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2", user.guild.id, user.id)

                        xp_start = int(result1[1])
                        lvl_start = int(result1[2])
                        xp_end = round(difficulty * result1[1] // 2 + difficulty * 8)
                        if xp_end < xp_start:
                            announcement = await cursor.fetchrow("SELECT channel_id FROM levels WHERE guild_id = $1 and user_id = $2",
                                           user.guild.id, user.id)
                            channel = user.guild.get_channel(announcement[0])
                            lvl_start += 1
                            if channel is not None:
                                embed = discord.Embed(title='Congratulations!',
                                                      description=f'{user.mention} has leveled up to level {lvl_start}.',
                                                      colour=discord.Colour.blue())
                                embed.set_thumbnail(url=user.avatar_url)
                                await channel.send(embed=embed)
                            levels = await cursor.fetchrow("SELECT level FROM leveling WHERE guild = $1 and system = $2",
                                           user.guild.id, 'levels')
                            await cursor.execute("UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and user_id = $4",
                                           lvl_start, 0, user.guild.id, user.id)
                            for levels in levels:
                                if lvl_start >= levels[0] and check == 1:
                                    await cursor.execute(
                                        "SELECT role FROM leveling WHERE guild = $1 and level = $2 and system = $3",
                                        user.guild.id, lvl_start, 'levels')
                                    lvl_roles = cursor.fetchone()
                                    lvl_role = user.guild.get_role(lvl_roles)
                                    await user.add_roles(lvl_role, reason='User leveled up')
                                elif lvl_start >= levels[0] and check == 0:
                                    lvl_roles = await cursor.fetchrow("SELECT role FROM leveling WHERE guild = $1 and level = $2 and system = $3", user.guild.id, lvl_start, 'levels')
                                    lvl_role = user.guild.get_role(lvl_roles[0])
                                    await user.add_roles(lvl_role, reason='User leveled up')
                                    roles = await cursor.fetch("SELECT role FROM leveling WHERE guild = $1 and system = $2", user.guild.id, 'levels')
                                    for role in roles:
                                        if int(role) in [role.id for role in user.author.roles] and int(role) != lvl_role.id:
                                            roles = user.guild.get_role(role_id=int(role))
                                            await user.remove_roles(roles)
                        else:
                            for multi in multiply:
                                if multi[0] == user.channel.id or multi[0] in [role.id for role in user.roles]:
                                    weight += multi[1] ^ multi[1]
                            await cursor.execute('UPDATE levels SET exp = $1 WHERE guild_id = $2 and user_id = $3', result1[1] + random.randint(0, weight), user.guild.id, user.id)
                await self.bot.db.release(cursor)
        except Exception:
            import traceback
            traceback.print_exc()


def setup(bot):
    bot.add_cog(Events(bot))
