import asyncio
from datetime import datetime
import random
import re

import time

from colorama import Fore, Back

import discord
from discord.ext import commands, tasks


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.member)
        self.__cd = commands.CooldownMapping.from_cooldown(1.0, 80.0, commands.BucketType.default)

    # set the bots custom status
    @commands.Cog.listener()
    async def on_ready(self):
        game = discord.Game(f"*help | Version {self.bot.version}")
        await self.bot.change_presence(activity=game, status=discord.Status.online, afk=None)
        print('#-------------------------------#', Fore.WHITE)
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
            cursor = await self.bot.db.acquire()
            retry_after = self._cd.update_rate_limit(message)
            # ranking cooldown ratelimiter
            if not retry_after:
                global dark
                blacklist = await cursor.prepare("SELECT role FROM leveling WHERE guild = $1 and system = $2")
                blacklist = await blacklist.fetch(message.author.guild.id, 'blacklist')
                # checks if the guild has enabled ranking and user not in blacklist
                for no in blacklist:
                    if no[0] != message.channel.id or no[0] not in [role.id for role in message.author.roles]:
                        result = await cursor.prepare("SELECT user_id FROM levels WHERE guild_id = $1 and user_id = $2")
                        result = await result.fetchval(message.author.guild.id, message.author.id)
                        difficulty = await cursor.prepare("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2")
                        difficulty = await difficulty.fetchval(message.author.guild.id, 'difficulty')

                        # checks if the member sending the message been ranked before, and if they haven't place them into the database
                        if result is None:
                            await cursor.execute("INSERT INTO levels(guild_id, user_id, channel_id, exp, lvl) VALUES($1,$2,$3,$4, $5)", message.author.guild.id, message.author.id, message.channel.id, 0, 0)
                        else:
                            result1 = await cursor.fetchrow("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2", message.author.guild.id, message.author.id)

                            xp_start = result1[1]
                            lvl_start = result1[2]
                            xp_end = round(result1[2] * difficulty + result1[2] * difficulty)
                            # checks if we have leveled up then updates the member level

                            if xp_end < xp_start:
                                lvl_start = lvl_start + 1
                                embed = discord.Embed(title='Congratulations!', description=f'{message.author.mention} has leveled up to level {lvl_start}', colour=discord.Colour.blue())
                                embed.set_thumbnail(url=message.author.avatar_url)
                                await message.channel.send(embed=embed)
                                await cursor.execute("UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and user_id = $4", lvl_start, 0, message.guild.id, message.author.id)
                                levels = await cursor.fetch("SELECT level FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'levels')
                                check = await cursor.fetchval("SELECT COALESCE((SELECT type FROM leveling WHERE guild = $1 and system = $2), 1)", message.author.guild.id, 'keep')
                                for level in levels:
                                    lvl_roles = await cursor.fetchval("SELECT role FROM leveling WHERE guild = $1 and level = $2 and system = $3", message.author.guild.id, lvl_start, 'levels')
                                    if lvl_start >= level[0] and check == 1:
                                        lvl_role = message.guild.get_role(lvl_roles)
                                        await message.author.add_roles(lvl_role, reason='User leveled up')
                                    elif lvl_start >= level[0] and check == 0:
                                        lvl_role = message.guild.get_role(lvl_roles)
                                        await message.author.add_roles(lvl_role, reason='User leveled up')
                                        roles = await cursor.fetch("SELECT role FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'levels')
                                        for role in roles:
                                            if role[0] in [role.id for role in message.author.roles] and role[0] != lvl_role.id:
                                                roles = message.guild.get_role(role_id=role[0])
                                                await message.author.remove_roles(roles, reason='Leveling Role Replace')
                            else:
                                multiply = await cursor.fetch("SELECT role, difficulty FROM leveling WHERE guild = $1 and system = $2", message.author.guild.id, 'multiplier')
                                weight = await cursor.fetchval("SELECT COALESCE((SELECT difficulty FROM leveling WHERE guild = $1 and system = $2), 6)", message.author.guild.id, 'message')
                                for multi in multiply:
                                    if multi[0] == message.channel.id or multi[0] in [role.id for role in message.author.roles]:
                                        weight += multi[1]
                                # if the above condition did not meet, just give the member exp instead
                                await cursor.fetchrow("UPDATE levels SET exp = $1, channel_id = $2 WHERE guild_id = $3 and user_id = $4", result1[1] + random.randint(0, weight), message.channel.id, message.guild.id, message.author.id)

            # COUNTER
            count = await cursor.prepare("SELECT channel, role, member, number, count, delay FROM count WHERE guild = $1")
            current = await count.fetchrow(message.guild.id)
            if current is not None and current[0] == message.channel.id:
                channel = message.guild.get_channel(current[0])
                role = message.guild.get_role(current[1])
                if current[2] != message.author.id:
                    if message.content == str(current[3]):
                        await cursor.execute("UPDATE count SET number = $1, member = $2 WHERE guild = $3", current[3]+1, message.author.id, message.guild.id)
                        if current[4]:
                            level = current[3]+1
                            text = re.match(r"(\D*)\d*", channel.topic).group(1) if channel.topic is not None else 'The next number is: '
                            topic = f"{text}{level}".strip()
                            await channel.edit(topic=topic, reason='New Counter Number')
                    else:
                        await message.delete()
                        await channel.send(f"{message.author.mention} just forgot how to count!", delete_after=4.7)
                        if role is not None and current[5] != 0:
                            await message.author.add_roles(role)
                            await asyncio.sleep(current[5])
                            await message.author.remove_roles(role)
                else:
                    await message.delete()
                    await channel.send(f"{message.author.mention} is lonely and needs someone to count with!", delete_after=4.7)


            # PARTNERS
            allowed = await cursor.prepare("SELECT type, role, level, difficulty FROM leveling WHERE guild = $1 and system = $2")
            partner = await allowed.fetchrow(message.guild.id, 'partners')
            # checks if partnerships tracking been enabled
            if partner is not None:
                role = message.guild.get_role(partner[1])
                if partner[0] == message.channel.id and role.id in [role.id for role in message.author.roles]:
                    # checks if the pm has completed an partnership, then give them one point
                    if re.search(r".*[https://]?discord(.*(gg))\S?\w{6}.*\n?", message.content):
                        amount = await cursor.fetchrow("SELECT number FROM partner WHERE guild = $1 and member = $2", message.guild.id, message.author.id)
                        if amount is None:
                            await cursor.execute("INSERT INTO partner(guild, member, number) VALUES($1, $2, $3)", message.guild.id, message.author.id, 1)
                        else:
                            amount = amount[0] + 1
                            if amount >= partner[2]:
                                reward = message.guild.get_role(partner[3])
                                # if enabled congratulates the pm if they meet the set threshold
                                result = await cursor.fetchval("SELECT announce FROM settings WHERE announce = $1 and guild = $2", message.channel.id, message.guild.id)
                                chan = message.guild.get_channel(result)
                                if chan is not None and reward.id not in [role.id for role in message.author.roles]:
                                    await chan.send(f"Congrats to {message.author.mention} for completing {amount} partnerships for {message.guild}!")
                                await message.author.add_roles(reward)
                            await cursor.execute("UPDATE partner SET number = $1 WHERE guild = $2 and member = $3", amount, message.guild.id, message.author.id)

            # AFK
            afk = await cursor.prepare("SELECT member, message FROM afk WHERE guild = $1")
            channel = message.channel
            member = message.author
            for user in await afk.fetch(message.guild.id):
                # checks the the member marked as AFK talked then removes them as AFK
                if user[0] == member.id:
                    try:
                        nick = member.display_name
                        await member.edit(nick=nick)
                    except discord.Forbidden:
                        pass
                    await cursor.execute("DELETE FROM afk WHERE guild = $1 and member = $2", message.guild.id, message.author.id)
                    await channel.send(f"{message.author.mention} I marked you as no longer AFK!")
                elif user[0] in [msg.id for msg in message.mentions]:
                    him = message.guild.get_member(user[0])
                    await channel.send(f"{message.author.mention} {him} is currently AFK with the reason: {user[1]}!")

            await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, _, after):
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
        blacklist = await cursor.fetch("SELECT role FROM leveling WHERE guild = $1 and system = $2", member.guild.id, 'blacklist')
        # checks if the guild has enabled ranking and user not in blacklist
        vcchannel = 0 if after.channel is None else after.channel.id
        for no in blacklist:
            if no[0] != vcchannel or no[0] not in [role.id for role in member.author.roles] and after.channel.id:
                if after.deaf or after.mute or after.self_mute or after.self_deaf or after.afk is True or None or after.channel is None:
                    self.bot.active.remove([member, after])
                else:
                    self.bot.active.append([member, after])
                if self.bot.active and len(self.bot.active) == 1:
                    self.vc.start()
                elif not self.bot.active:
                    self.vc.cancel()

        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # detects if an user is streaming and gives an role accordingly
        if not before.activity == after.activity:
            cursor = await self.bot.db.acquire()
            guild = after.guild
            stream = await cursor.prepare("SELECT live FROM settings WHERE guild = $1")
            role = guild.get_role(await stream.fetchval(guild.id))
            if role is not None:
                for activity in after.activities:
                    if activity.type == discord.ActivityType.streaming:
                        await after.add_roles(role, reason='User Is Streaming')
                    else:
                        await after.remove_roles(role, reason='User is no longer Streaming')
            await self.bot.db.release(cursor)

        if not before.roles == after.roles:
            # for custom roles / text channels / voice channels
            cursor = await self.bot.db.acquire()
            guild = after.guild
            memberid = after.id
            roleauth = await cursor.prepare("SELECT role, system, remove FROM custom WHERE guild = $1")

            # if enabled deletes the created custom role once the set required role gets removed
            for roleauth in await roleauth.fetch(guild.id):
                if roleauth[0] not in [role.id for role in after.roles] and roleauth[2] is True:
                    role = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memberid, guild.id, roleauth[1])
                    if role is not None:
                        await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", guild.id, role, memberid, roleauth[1])
                        custom = guild.get_role(role) if roleauth[1] == 'role' else guild.get_channel(role)
                        await custom.delete(reason='Required Role/Channel Was Removed From Member')

            # for sticky roles
            guildid = after.guild.id
            master = await cursor.prepare("SELECT role FROM reward WHERE guild = $1 and type = $2")
            for n in await master.fetch(guildid, 'sticky'):
                n = n[0]
                # if enabled gives back an set role if an member left with said role
                type = await cursor.fetchval("SELECT role FROM roles WHERE role = $1 and guild = $2 and member = $3 and type = $4", n, guildid, after.id, 'sticky')
                if n in [role.id for role in after.roles] and type is None:
                    await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guildid, after.id, n, 'sticky')
                if n not in [role.id for role in after.roles] and type is not None:
                    await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", guildid, n, after.id, 'sticky')

            await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        # OVERWRITES RECOVERY
        if before.overwrites != after.overwrites:
            cursor = await self.bot.db.acquire()
            guild = after.guild
            channel = after
            recovery = await cursor.prepare("SELECT recovery FROM settings WHERE guild = $1")
            memovr = await cursor.prepare("SELECT member, channel FROM recover WHERE guild = $1 and channel = $2")
            role = guild.get_role(await recovery.fetchval(guild.id))
            users = []
            for perm, value in channel.overwrites.items():
                # if an user has defined channel overwrites on them and they have the set role on them insert the channel overwrites into the db to give them back if the user rejoins the guild
                if role is not None and isinstance(perm, discord.Member):
                    if role.id in [role.id for role in perm.roles]:
                        users.append((perm.id, channel.id))
                        check = await cursor.fetchrow("SELECT member FROM recover WHERE guild = $1 and member = $2 and channel = $3",guild.id, perm.id, channel.id)
                        yes = value.pair()[0].value
                        no = value.pair()[1].value
                        if check is None:
                            await cursor.execute("INSERT INTO recover(guild, channel, member, yes, no) VALUES($1, $2, $3, $4, $5)",guild.id, channel.id, perm.id, yes, no)
                        else:
                            await cursor.execute("UPDATE recover SET yes = $1, no = $2 WHERE guild = $3 and channel = $4 and member= $5", yes, no, guild.id, channel.id, perm.id)

                for removed in await memovr.fetch(guild.id, channel.id):
                    member = guild.get_member(removed[0])
                    if removed not in users and member is not None:
                        await cursor.execute("DELETE FROM recover WHERE guild = $1 and member = $2 and channel = $3", guild.id, removed[0], removed[1])
            await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        cursor = await self.bot.db.acquire()
        # gives roles to an member once they react to an set emoji
        global word
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
        chanmsg = await cursor.prepare("SELECT master FROM reaction WHERE guild = $1 and type = $2 and master = $3")
        chanmsg = await chanmsg.fetchval(guild_id, emoji, main)
        # checks if we have actually reacted
        if chanmsg == main:
            role = await cursor.fetch("SELECT role FROM reaction WHERE master = $1 and type = $2 and guild = $3", main, emoji, guild_id)
            role = random.choice(role)[0]
            whitelist = await cursor.fetchval("SELECT blacklist FROM reaction WHERE role = $1 and master = $2 and guild = $3 and type = $4", role, main, guild_id, emoji)
            # splits reaction role types into code readable format

            guild = self.bot.get_guild(guild_id)
            member = await guild.fetch_member(user_id)
            # if enabled check if we are in the whitelist and continue
            if whitelist not in [role.id for role in member.roles] and whitelist != 0:
                await member.send("You do not have the required role to get this role from reaction roles!")
            else:
                # splits reaction role types into code readable format and checks if we can receive role
                roles = await cursor.fetch("SELECT role FROM reaction WHERE master = $1 and guild = $2", main, guild_id)
                if "o" in role:
                    role = role.replace("o", "")
                    mroles = guild.get_role(role_id=int(role))
                    for role in roles:
                        role = role[0].replace("o", "")
                        for role2 in [role.id for role in member.roles]:
                            if role == str(role2):
                                await member.send("You cannot change your roles after reacting from this reaction role category!")
                    await member.add_roles(mroles, reason='User reacted to reaction role')

                elif "r" in role:
                    role = role.replace("r", "")
                    mroles = guild.get_role(role_id=int(role))
                    for role in roles:
                        role = role[0].replace("r", "")
                        if int(role) in [role.id for role in member.roles]:
                            roles = guild.get_role(int(role))
                            await member.remove_roles(roles, reason='User unreacted to reaction role')
                        await member.add_roles(mroles, reason='User reacted to reaction role')

                elif "n" in role:
                    role = role.replace("n", "")
                    mroles = guild.get_role(role_id=int(role))
                    await member.add_roles(mroles, reason='User reacted to reaction role')

                elif "c" in role:
                    role = role.replace("c", "")
                    mroles = guild.get_role(role_id=int(role))
                    cblacklist = await cursor.fetchval("SELECT message FROM owner WHERE guild = $1 and member = $2 and message = $3 and type = $4", guild_id, user_id, message_id, 'club')
                    isClub = await cursor.fetchval("SELECT level FROM leveling WHERE guild = $1 and system = $2", guild_id, 'points')
                    if cblacklist is not None and isClub == channel_id:
                        channel = guild.get_channel(channel_id)
                        message = await channel.fetch_message(message_id)
                        await message.remove_reaction(payload.emoji, payload.member)
                    else:
                        await member.add_roles(mroles, reason='User reacted to reaction role')


        # if set to single voting automatically removes the voters reaction role if they try to vote for more than one thing
        multi = await cursor.prepare("SELECT date, win FROM vote WHERE guild = $1 and message = $2 and type = $3")
        multi = await multi.fetchrow(guild_id, main, 'poll')
        if multi is not None and multi[1] == 0:
            emoji = self.bot.emoji[int(1668 - multi[0]):1668]
            guild = self.bot.get_guild(guild_id)
            channel = guild.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            count = 0
            for reaction in message.reactions:
                users = await reaction.users().flatten()
                if payload.member in users and reaction.emoji in emoji:
                    count += 1
                    if count > 1:
                        await message.remove_reaction(payload.emoji, payload.member)

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
        chanmsg = await cursor.prepare("SELECT master FROM reaction WHERE guild = $1 and type = $2 and master = $3")
        chanmsg = await chanmsg.fetchval(guild_id, emoji, main)
        # checks if we have actually removed our reaction
        if main == chanmsg:
            role = await cursor.fetchval("SELECT role FROM reaction WHERE master = $1 and type = $2 and guild = $3", chanmsg, emoji, guild_id)
            # splits reaction role types into code readable format anmd checks if we can remove role
            guild = self.bot.get_guild(guild_id)
            member = await guild.fetch_member(user_id)
            if 'r' in role or 'n' in role or 'c' in role:
                role = re.findall(r'\d*', role)[1]
                mrole = guild.get_role(role_id=int(role))
                await member.remove_roles(mrole, reason='User unreacted to reaction role')
        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        cursor = await self.bot.db.acquire()
        # if enabled deletes the user from leveling if they left the guild
        clear = await cursor.prepare("SELECT type FROM leveling WHERE guild = $1 and system = $2")
        if await clear.fetchval(member.guild.id, 'clear') == 1:
            await cursor.execute("DELETE FROM levels WHERE guild_id = $1 and user_id = $2", member.guild.id, member.id)

        # removes the member custom channels / roles if they had them when leaving
        roleauth = await cursor.prepare("SELECT role, type FROM roles WHERE guild = $1 and member = $2 and not type = $3")
        for roleauth in await roleauth.fetch(member.guild.id, member.id, 'sticky'):
            custom = member.guild.get_role(roleauth[0]) if roleauth[1] == 'role' else member.guild.get_channel(roleauth[0])
            if custom is not None:
                await cursor.execute("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", member.guild.id, custom.id, member.id, roleauth[1])
                await custom.delete(reason='Required Role/Channel Was Removed From Member')

        # updates users invite leaves if the joiner left the guild
        now = member.joined_at.timestamp()
        amount = await cursor.prepare("SELECT invite FROM invite2 WHERE guild = $1 and member = $2 and timestamp = $3")
        amount = await amount.fetchval(member.guild.id, member.id, now)
        check = await cursor.prepare("SELECT amount2, amount3 FROM invite WHERE guild = $1 and invite = $2")
        check = await check.fetchrow(member.guild.id, amount)
        var = list(check) if check is not None else [0, 0]
        if (datetime.now() - member.joined_at).total_seconds() < 120:
            var[1] += 1
        else:
            var[0] += 1
        await cursor.execute("UPDATE invite SET amount2 = $1, amount3 = $2 WHERE guild = $3 and invite = $4", var[0], var[1], member.guild.id, amount)
        await cursor.execute("DELETE FROM invite2 WHERE member = $1 and timestamp = $2", member.id, now)
        await self.bot.db.release(cursor)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        cursor = await self.bot.db.acquire()
        guildid = member.guild.id
        guild = member.guild

        # code for auto roles
        auto = await cursor.prepare("SELECT prefix FROM settings WHERE guild = $1")
        auto = await auto.fetchval(guildid)
        if auto not in [role.id for role in member.roles] and auto is not None:
            role = guild.get_role(role_id=auto)
            await member.add_roles(role, reason='Auto role')

        # code for sticky roles
        master = await cursor.prepare("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3")
        for select in await master.fetch(guildid, member.id, 'sticky'):
            if select[0] not in [role.id for role in member.roles] and select[0] is not None:
                srole = guild.get_role(role_id=int(select[0]))
                await member.add_roles(srole, reason='User had sticky roles when leaving')

        # code for invite rewards
        for invites in await guild.invites():
            if invites.inviter.id != member.id:
                amount = await cursor.prepare("SELECT amount FROM invite WHERE guild = $1 and member = $2 and invite = $3")
                amount = await amount.fetchval(guildid, invites.inviter.id, invites.code)
                if amount is not None and invites.uses > amount:
                    now = member.joined_at.timestamp()
                    await cursor.execute("UPDATE invite SET amount = $1 WHERE guild = $2 and member = $3 and invite = $4", invites.uses, guildid, invites.inviter.id, invites.code)
                    await cursor.execute("INSERT INTO invite2(guild, member, invite, timestamp) VALUES($1, $2, $3, $4)", guildid, member.id, invites.code, now)
                    total = await cursor.fetchval("SELECT SUM(amount) FROM invite WHERE guild = $1 and member = $2", guildid, invites.inviter.id)
                    check = await cursor.fetch("SELECT date::int8, role FROM boost WHERE guild = $1 and type = $2 ORDER BY date DESC", guildid, 'invite')
                    for day in check:
                        role = guild.get_role(day[1])
                        if total >= day[0]:
                            announcement = await cursor.fetchval("SELECT announce FROM settings WHERE guild = $1", guildid)
                            channel = guild.get_channel(announcement)
                            user = guild.get_member(invites.inviter.id)
                            if channel is not None and role.id not in [role.id for role in user.roles]:
                                await channel.send(f"Congrats to {user.mention} for inviting {total} users to {guild}!")
                                await user.add_roles(role)
                elif amount is None and invites.uses > 0:
                    await cursor.execute("INSERT INTO invite(guild, member, invite, amount, amount2, amount3) VALUES($1, $2, $3, $4, $5, $6)", guildid, invites.inviter.id, invites.code, invites.uses, 0, 0)

        # code for channel overwrites recovery
        for channel in guild.channels:
            override = await cursor.prepare("SELECT yes, no FROM recover WHERE guild = $1 and member = $2 and channel = $3")
            override = await override.fetchrow(guild.id, member.id, channel.id)
            if override is not None:
                yes = discord.Permissions(permissions=override[0])
                no = discord.Permissions(permissions=override[1])
                overrides = discord.PermissionOverwrite().from_pair(yes, no)
                await channel.set_permissions(member, overwrite=overrides, reason='user joined back with previous channel overwrites')
        await self.bot.db.release(cursor)

    @tasks.loop()
    async def vc(self):
        try:
            cursor = await self.bot.db.acquire()
            for all in self.bot.active:
                user = all[0]
                voice = all[1]
                retry_after = self.__cd.update_rate_limit(user)
                # rate limited for vc ranking
                if not retry_after:
                    # ranking for vc's
                    result = await cursor.prepare("SELECT user_id FROM levels WHERE guild_id = $1 and user_id = $2")
                    result = await result.fetchval(user.guild.id, user.author.id)
                    difficulty = await cursor.prepare("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2")
                    difficulty = await difficulty.fetchval(user.guild.id, 'difficulty')
                    if result is None:
                        await cursor.execute("INSERT INTO levels(guild_id, user_id, exp, lvl) VALUES($1,$2,$3,$4)",user.guild.id, user.id, 0, 0)
                    else:
                        result1 = await cursor.fetchrow("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2", user.guild.id, user.id)
                        xp_start = int(result1[1])
                        lvl_start = int(result1[2])
                        xp_end = round(difficulty * result1[1] // 2 + difficulty * 8)
                        if xp_end < xp_start:
                            announcement = await cursor.fetchrow("SELECT channel_id FROM levels WHERE guild_id = $1 and user_id = $2", user.guild.id, user.id)
                            channel = user.guild.get_channel(announcement[0])
                            lvl_start += 1
                            if channel is not None:
                                embed = discord.Embed(title='Congratulations!', description=f'{user.mention} has leveled up to level {lvl_start}', colour=discord.Colour.blue())
                                embed.set_thumbnail(url=user.avatar_url)
                                await channel.send(embed=embed)
                            await cursor.execute("UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and user_id = $4",
                                           lvl_start, 0, user.guild.id, user.id)
                            levels = await cursor.fetchrow("SELECT level FROM leveling WHERE guild = $1 and system = $2", user.guild.id, 'levels')
                            check = await cursor.fetchval("SELECT COALESCE((SELECT type FROM leveling WHERE guild = $1 and system = $2), 1)", user.guild.id, 'keep')
                            for level in levels:
                                if lvl_start >= level[0] and check == 1:
                                    await cursor.execute("SELECT role FROM leveling WHERE guild = $1 and level = $2 and system = $3", user.guild.id, lvl_start, 'levels')
                                    lvl_roles = cursor.fetchone()
                                    lvl_role = user.guild.get_role(lvl_roles)
                                    await user.add_roles(lvl_role, reason='User leveled up')
                                elif lvl_start >= level[0] and check == 0:
                                    lvl_roles = await cursor.fetchrow("SELECT role FROM leveling WHERE guild = $1 and level = $2 and system = $3", user.guild.id, lvl_start, 'levels')
                                    lvl_role = user.guild.get_role(lvl_roles[0])
                                    await user.add_roles(lvl_role, reason='User leveled up')
                                    roles = await cursor.fetch("SELECT role FROM leveling WHERE guild = $1 and system = $2", user.guild.id, 'levels')
                                    for role in roles:
                                        if role[0] in [role.id for role in user.author.roles] and role[0] != lvl_role.id:
                                            roles = user.guild.get_role(role_id=role[0])
                                            await user.remove_roles(roles)
                        else:
                            multiply = await cursor.fetch("SELECT role, difficulty FROM leveling WHERE guild = $1 and system = $2", user.guild.id, 'multiplier')
                            weight = await cursor.fetchval("SELECT COALESCE((SELECT difficulty FROM leveling WHERE guild = $1 and system = $2), 6)", user.guild.id, 'voice')
                            for multi in multiply:
                                print(multi[0])
                                if multi[0] == voice.channel.id or multi[0] in [role.id for role in user.roles]:
                                    weight += multi[1]
                            await cursor.execute('UPDATE levels SET exp = $1 WHERE guild_id = $2 and user_id = $3', result1[1] + random.randint(0, weight), user.guild.id, user.id)
                await self.bot.db.release(cursor)
        except Exception:
            import traceback
            traceback.print_exc()

def setup(bot):
    bot.add_cog(Events(bot))

