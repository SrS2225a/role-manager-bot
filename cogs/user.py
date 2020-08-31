import asyncio
import datetime
import random
import re
import typing

import discord
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands, menus
from tabulate import tabulate
from tqdm import tqdm

client = discord.Client()


# user commands
def rccustom():
    async def predicate(ctx):
        guild = ctx.guild.id
        cursor = await ctx.bot.db.acquire()
        roleauth = await cursor.fetchval("SELECT role FROM custom WHERE guild = $1 and system = $2", guild, 'role')
        print(roleauth)
        missing = ctx.guild.get_role(roleauth)
        await ctx.bot.db.release(cursor)
        if roleauth in [role.id for role in ctx.author.roles]:
            return True
        else:
            raise commands.MissingRole(missing.name) if missing is not None else commands.CommandError(
                'Creating custom roles are currently disabled for this bot!')

    return commands.check(predicate)


def ccustom(type):
    async def predicate(ctx):
        guild = ctx.guild.id
        cursor = await ctx.bot.db.acquire()
        roleauth = await cursor.fetchrow("SELECT role FROM custom WHERE guild = $1 and not system = $2", guild, type)
        missing = ctx.guild.get_channel(roleauth)
        await ctx.bot.db.release(cursor)
        if roleauth in [role.id for role in ctx.author.roles]:
            return True
        else:
            raise commands.MissingRole(missing.name) if missing is not None else commands.CommandError(
                'Creating custom roles are currently disabled for this bot!')

    return commands.check(predicate)


class User(commands.Cog, name='User Commands'):
    def __init__(self, bot):
        self.bot = bot

    # checks if the member has the required role to run custom role commands

    @commands.command()
    async def ping(self, ctx):
        """Responds with the bots ping between the client and discord"""
        await ctx.send(f"The ping is: {round(self.bot.latency * 1000)} ms!")
        return

    @commands.command(description="You can supply arg with 'None' to list members without a specified role")
    async def listmembers(self, ctx, role, arg=None):
        """List members by a role or no role"""
        if role in "no-roles":
            members = []
            for member in ctx.guild.members:
                if len(member.roles) == 1:
                    members.append(member.name + "#" + member.discriminator)
        elif arg in ("None",):
            role = await commands.RoleConverter().convert(ctx, role)
            members = []
            for member in ctx.guild.members:
                if role.id not in [role.id for role in member.roles]:
                    members.append(member.name + "#" + member.discriminator)
        else:
            role = await commands.RoleConverter().convert(ctx, role)
            members = []
            for member in ctx.guild.members:
                if role.id in [role.id for role in member.roles]:
                    members.append(member.name + "#" + member.discriminator)

        class Source(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=20)

            async def format_page(self, menu, entry):
                offset = menu.current_page * self.per_page
                joined = '\n'.join(f'{i}. {v}' for i, v in enumerate(entry, start=1 + offset))
                return f'```{joined}```\nPage {menu.current_page + 1}/{self.get_max_pages()}'
        if not members:
            await ctx.send('No members')
        else:
            pages = menus.MenuPages(source=Source(members), clear_reactions_after=True)
            await pages.start(ctx)

    @commands.command()
    async def roles(self, ctx):
        """Shows a list of all roles in the server"""
        roles = []
        for role in ctx.guild.roles[::-1]:
            roles.append(role.name + ' | ' + str(role.id))

        class Source(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=20)

            async def format_page(self, menu, entry):
                offset = menu.current_page * self.per_page
                joined = '\n'.join(f'{i}. {v}' for i, v in enumerate(entry, start=1 + offset))
                return f'```{joined}```\nPage {menu.current_page + 1}/{self.get_max_pages()}'

        pages = menus.MenuPages(source=Source(roles), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command(aliases=['top'], description='Supply type with rankings/invites/partnerships to view that particular leaderboard')
    async def leaderboard(self, ctx, type, rank: int = None):
        """Shows top rankings"""
        global result, check, user
        cursor = await self.bot.db.acquire()
        if rank is None:
            rank = 10
        elif rank > 100:
            await ctx.send("Top Rankings Cannot Be Above 100!")
            return
        if type == 'rankings':
            diff1 = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.author.guild.id, 'difficulty')
            if diff1 is not None:
                result = await cursor.fetch("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, exp DESC LIMIT $2", ctx.guild.id, rank)
                table = []
                for row in result:
                    user = self.bot.get_user(id=int(row[0]))
                    if user is not None:
                        table.append([row[1], row[2], user.name + "#" + user.discriminator])

                await ctx.send(f"``` Ranking - {rank} \n\n{tabulate(table, headers=['XP', 'LV', 'USER'], tablefmt='github')}```")
            elif diff1 is None:
                await ctx.send("Rankings is currently disabled for this bot!")
                return
        elif type == 'invites':
            result = await cursor.fetch("SELECT member, SUM(amount), SUM(amount2) FROM invite WHERE guild = $1 GROUP BY member ORDER BY SUM(amount) DESC, SUM(amount2) DESC LIMIT $2", ctx.guild.id, rank)
            table = []
            for row in result:
                user = self.bot.get_user(id=int(row[0]))
                if user is not None:
                    table.append([row[1], row[2], user.name + "#" + user.discriminator])

            await ctx.send(f"``` Invites - {rank} \n\n{tabulate(table, headers=['JOINS', 'LEAVES', 'USER'], tablefmt='github')}```")
        elif type == 'partnerships':
            diff1 = await cursor.fetchval(f"SELECT system FROM leveling WHERE guild = $1 and system = $2", ctx.author.guild.id, 'partners')
            if diff1 is not None:
                result = await cursor.fetch("SELECT member, number FROM partner WHERE guild = $1 ORDER BY number DESC LIMIT $2", ctx.guild.id, rank)
                table = []
                for row in result:
                    user = self.bot.get_user(id=int(row[0]))
                    if user is not None:
                        table.append([row[1], user.name + "#" + user.discriminator])

                await ctx.send(f"``` Partnerships - {rank} \n\n{tabulate(table, headers=['PARTNERS', 'USER'], tablefmt='github')}```")
            elif diff1 is None:
                await ctx.send("Partnerships is currently disabled for this bot!")
        await self.bot.db.release(cursor)

    @commands.command(aliases=['level'])
    async def rank(self, ctx, *, user: discord.Member = None):
        """Shows your ranking status or someone else's"""
        global channel
        cursor = await self.bot.db.acquire()
        member = ctx.author if not user else user
        difficulty = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'difficulty')
        if difficulty is not None:
            result = await cursor.fetchrow("SELECT exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2", ctx.guild.id, member.id)
            ranking = await cursor.fetch("SELECT user_id FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, exp DESC", ctx.guild.id)
            print(difficulty)
            print(result)

            i = 0
            for row in ranking:
                i += 1
                if row[0] == member.id:
                    break

            if result is None:
                embed = discord.Embed(
                    title='Level Ranking - Undefined Rank',
                    description='The user you have mentioned is not yet ranked.',
                    colour=discord.Colour.red()
                )

                await ctx.send(embed=embed)
            else:
                xp_end = round(difficulty * result[1] / 2 + difficulty * result[1])
                bar = tqdm(total=xp_end, ncols=24, miniters=1, ascii='□◧■', bar_format='{l_bar}{bar}')
                bar.update(result[0])

                embed = discord.Embed(
                    title=f'Level Ranking - {member.name}',
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

    @commands.command(description='Supply type with list to list your reminders, delete to delete and reminder, or me/here to set the destination of the reminder')
    async def remind(self, ctx, type, duration=None, *, description=None):
        """Sets a reminder with an given time"""
        cursor = await self.bot.db.acquire()
        if type == 'list':
            reminders = await cursor.fetch("SELECT * FROM remind WHERE guild = $1", ctx.author.id)
            embed = discord.Embed(title=f"{ctx.author} Reminders")
            if reminders is None:
                embed.description = 'You Have No Reminders!'
            elif reminders is not None:
                for remind in reminders:
                    chan = self.bot.get_channel(remind[4]) if self.bot.get_channel(remind[4]) is not None else 'dm'
                    date = datetime.datetime.utcfromtimestamp(remind[2]).strftime('%A %d %B %Y @ %H:%M:%S UTC')
                    embed.add_field(name=f"Reminder [`{remind[1]}`]", value=f"```Time: {date}\nWhere: {chan}\nReason: {remind[3]}```", inline=False)
            await ctx.send(embed=embed)
            return

        elif type == 'delete':
            await cursor.execute('DELETE FROM remind WHERE guild = $1 and message = $2', ctx.author.id, duration)
            await ctx.send(f"Reminder Deleted Successfully!")
            return

        else:
            if type == 'me':
                user = ctx.author
            elif type == 'here':
                user = ctx.channel
            else:
                await ctx.send('Argument 1 should be me or here')
                return

            units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}

            def convert_to_seconds(s):
                return int(datetime.timedelta(**{
                    units.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
                    for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smhdw]?)', s, flags=re.I)
                }).total_seconds())

            def display_time(duration):
                intervals = (('years', 31556952), ('months', 2592000), ('weeks', 604800), ('days', 86400), ('hours', 3600), ('minutes', 60), ('seconds', 1))

                result = []

                for name, count in intervals:
                    value = duration // count

                    if value:
                        duration -= value * count

                        result.append(f'{round(value)} {name}')

                return ' '.join(result)

            time = convert_to_seconds(duration)
            if time is None:
                await ctx.send("I do not recognise that time!")
                return
            delta = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
            stamp = delta.timestamp()
            rand = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
            remind_id = random.choices(rand, k=7)
            await cursor.execute("INSERT INTO remind(guild, message, date, win, type) VALUES($1, $2, $3, $4, $5)", ctx.author.id, ''.join(remind_id), stamp, description, user.id)
            await ctx.send(f"Reminding you in {display_time(time)} about {description}")
            await asyncio.sleep(time)
            reminders = await cursor.fetchrow("SELECT * FROM remind WHERE guild = $1 and message = $2", ctx.author.id, ''.join(remind_id))
            if reminders is not None:
                await user.send(f"{ctx.author.mention} {display_time(time)} ago you asked me to remind you about {description}")
                await cursor.execute("DELETE FROM remind WHERE guild = $1 and message = $2", ctx.author.id, ''.join(remind_id))
            await self.bot.db.release(cursor)

    @commands.command()
    async def afk(self, ctx, *, reason = None):
        """Marks you as AFK"""
        cursor = await self.bot.db.acquire()
        cursor.row_factory = lambda cursor, row: row[0]
        reason = 'AFK' if not reason else reason
        member = ctx.author
        afk = await cursor.fetchval("SELECT member FROM afk WHERE guild = $1 and member = $2", ctx.guild.id, member.id)
        if afk is not None:
            nick = member.nick.replace('[AFK]', '')
            await member.edit(nick=nick)
            await cursor.execute("DELETE FROM afk WHERE guild = $1 and member = $2", ctx.guild.id, member.id)
            await ctx.send(f"{member.mention} I marked you as no longer AFK!")
        else:
            nick = member.display_name + ' [AFK]'
            await member.edit(nick=nick)
            await cursor.execute("INSERT INTO afk(guild, member, message) VALUES($1, $2, $3)", ctx.guild.id, member.id, reason)
            await ctx.send(f"{member.mention} I marked you as AFK!")
        await self.bot.db.release(cursor)

    @commands.command()
    async def invites(self, ctx, *, member: discord.Member = None):
        """Shows info about how many members you invited, or someone else"""
        global total, total2, deficit, percent
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        invite = await guild.invites()
        member = ctx.author if not member else member
        full = await cursor.fetch("SELECT amount, amount2 FROM invite WHERE guild = $1 and member = $2", guild.id, member.id)
        url = " "
        uses = " "
        max_uses = " "
        channel = " "
        created_at = " "
        temporary = " "
        if not invite:
            await ctx.send("There are no invites currently active in this guild. For this command to work correctly, create an invite.")
            return
        for invites in invite:
            total = 0
            total2 = 0
            for i in full:
                if i[0] is None:
                    total += invites.uses + i[0]
                else:
                    total += i[0]
                if i[1] is None:
                    total2 += 0
                else:
                    total2 += i[1]
            deficit = total - total2
            percent = round(total2 * 100 / total, 2) if total != 0 else 0
            if invites.inviter.id == member.id:
                if invites.max_uses == 0:
                    max_uses += 'Unlimited' + "\n"
                else:
                    max_uses += str(invites.max_uses) + "\n"
                uses += str(invites.uses) + "\n"
                url += invites.url + "\n"
                channel += str(invites.channel) + "\n"
                created_at += invites.created_at.__format__('%A %d %B %Y @ %H:%M:%S UTC') + "\n"
                temporary += str(invites.temporary) + "\n"
        if created_at != " ":
            embed = discord.Embed(title=f"{member} Invites", color=member.color)
            embed.add_field(name="Invite Code", value=url)
            embed.add_field(name="Uses", value=uses)
            embed.add_field(name="Max Uses", value=max_uses)
            embed.add_field(name="Invite Channel", value=channel)
            embed.add_field(name="Created At", value=created_at)
            embed.add_field(name="Temporary", value=temporary)
            embed.add_field(name="All Time Invites", value=f"{total} joins with {total2} leaves and a deficit of {deficit} ({percent}%)")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=f"{member} Invites", color=member.color, description=f"{member} currently has no active invites!")
            embed.add_field(name="All Time Invites", value=f"{total} joins with {total2} leaves and a deficit of {deficit} ({percent}%)")
            await ctx.send(embed=embed)
        await self.bot.db.release(cursor)

    @commands.command()
    async def roleinfo(self, ctx, *, role: discord.Role):
        """Shows info about a role"""
        has = len(role.members)
        dont = ["speak", "stream", "connect", "read_messages", "send_messages", "embed_links", "attach_files",
                "use_voice_activation", "read_message_history", "external_emojis", "add_reactions", "priority_speaker",
                "send_tts_messages", "view_guild_insights", "change_nickname"]
        array = " "
        for perm, value in role.permissions:
            if perm not in dont and value is True:
                array += perm + ", "
            elif array == " ":
                array = "None"
        embed = discord.Embed(title='Role Info', color=role.color)
        embed.add_field(name="Role Name", value=f"```{role}```")
        embed.add_field(name="Role ID", value=f"```{role.id}```")
        embed.add_field(name="Created At", value=f"```{role.created_at.__format__('%A %d %B %Y @ %H:%M:%S UTC')}```", inline=False)
        embed.add_field(name="Color", value=f"```{role.color}```")
        embed.add_field(name="Position", value=f"```{role.position}```")
        embed.add_field(name="Has Role", value=f"```{has}```")
        embed.add_field(name="Hoisted", value=f"```{role.hoist}```")
        embed.add_field(name="Integrated", value=f"```{role.managed}```")
        embed.add_field(name="Mentionable", value=f"```{role.mentionable}```")
        embed.add_field(name='Key Permissions', value=f"```{array}```")
        await ctx.send(embed=embed)

    @commands.command()
    async def channelinfo(self, ctx, *, channel: typing.Union[discord.TextChannel, discord.VoiceChannel] = None):
        """Shows info about a channel"""
        channel = ctx.channel if not channel else channel
        yes = " "
        no = " "
        for perm, value in channel.overwrites.items():
            if isinstance(perm, discord.Role):
                if channel.overwrites_for(perm).read_messages:
                    yes += perm.mention
                else:
                    no += perm.mention
        if isinstance(channel, discord.TextChannel):
            pins = await channel.pins()
            invites = await channel.invites()
            webhooks = await channel.webhooks()
            overwrites = f"**Permitted**\n{yes}\n**Denied**\n{no}"
            embed = discord.Embed(title='Channel Info', color=ctx.author.color)
            embed.add_field(name="Channel Name", value=f"```{channel}```")
            embed.add_field(name="Category", value=f"```{channel.category}```")
            embed.add_field(name="Channel ID", value=f"```{channel.id}```")
            embed.add_field(name="Created At", value=f"```{channel.created_at.__format__('%A %d %B %Y @ %H:%M:%S UTC')}```", inline=False)
            embed.add_field(name="Topic", value=f"```{channel.topic}```", inline=False)
            embed.add_field(name="Overwrites", value=overwrites, inline=False)
            embed.add_field(name="Slowmode", value=f"```{channel.slowmode_delay}```")
            embed.add_field(name="Pins", value=f"```{len(pins)}```")
            embed.add_field(name="Invites", value=f"```{len(invites)}```")
            embed.add_field(name="Webhooks", value=f"```{len(webhooks)}```")
            embed.add_field(name="Position", value=f"```{channel.position + 1}```")
            embed.add_field(name="Type", value=f"```{channel.type}```")
            embed.add_field(name="News", value=f"```{channel.is_nsfw()}```")
            embed.add_field(name="NSFW", value=f"```{channel.is_nsfw()}```")
            embed.add_field(name="Permissions Synced", value=f"```{channel.permissions_synced}```")
            await ctx.send(embed=embed)

        elif isinstance(channel, discord.VoiceChannel):
            overwrites = f"**Permitted**\n{yes}\n**Denied**\n{no}"
            invites = await channel.invites()
            embed = discord.Embed(title='Channel Info', value=ctx.author.color)
            embed.add_field(name="Channel Name", value=f"```{channel}```")
            embed.add_field(name="Category", value=f"```{channel.category}```")
            embed.add_field(name="Channel ID", value=f"```{channel.id}```")
            embed.add_field(name="Created At", value=f"```{channel.created_at.__format__('%A %d %B %Y @ %H:%M:%S UTC')}```", inline=False)
            embed.add_field(name="Overwrites", value=overwrites, inline=False)
            embed.add_field(name="Position", value=f"```{channel.position + 1}```")
            embed.add_field(name="Bitrate", value=f"```{channel.bitrate}```")
            embed.add_field(name="User Limit", value=f"```{channel.user_limit}```")
            embed.add_field(name="Invites", value=f"```{len(invites)}```")
            embed.add_field(name="Type", value=f"```{channel.type}```")
            await ctx.send(embed=embed)

    @commands.command(aliases=["serverinfo"])
    async def guildinfo(self, ctx, *, guild=None):
        """Shows info about a guild"""
        guild = ctx.guild if not guild else self.bot.get_guild(guild)
        fa = 'Enabled' if guild.mfa_level == 1 else 'Disabled'
        notifications = 'All Messages' if guild.default_notifications.value == 0 else 'Only @Mentions'
        features = 'None' if not guild.features else ' '.join(guild.features)
        if guild is not None:
            splash = f"[```Click Here```]({str(guild.splash_url)})"
            banner = f"[```Click Here```]({str(guild.banner_url)})"
            if splash == "[```Click Here```]()":
                splash = '```None```'
            if banner == "[```Click Here```]()":
                banner = '```None```'

            channel_count = len([x for x in guild.channels if type(x) == discord.channel.TextChannel])
            voice_count = len([x for x in guild.channels if type(x) == discord.channel.VoiceChannel])
            category_count = len([x for x in guild.channels if type(x) == discord.channel.CategoryChannel])
            role_count = len(guild.roles)
            emoji_count = len(guild.emojis)

            embed = discord.Embed(title='Guild Info', color=ctx.author.color)
            embed.add_field(name='Owner', value=f"```{guild.owner}```")
            embed.add_field(name='Guild Name', value=f"```{guild.name}```")
            embed.add_field(name='Guild ID', value=f"```{guild.id}```", inline=False)
            embed.add_field(name='Created At', value=f"```{guild.created_at.__format__('%A %d %B %Y @ %H:%M:%S UTC')}```", inline=False)
            embed.add_field(name='Boosts', value=f"```Level {guild.premium_tier} With {guild.premium_subscription_count} Boosts And {len(guild.premium_subscribers)} Actual```", inline=False)
            embed.add_field(name='Features', value=f"```{features}```", inline=False)
            embed.add_field(name='Members', value=f"```{guild.member_count}```")
            embed.add_field(name='Text Channels', value=f"```{channel_count}```")
            embed.add_field(name='Voice Channels', value=f"```{voice_count}```")
            embed.add_field(name='Categories', value=f"```{category_count}```")
            embed.add_field(name='Roles', value=f"```{role_count}```")
            embed.add_field(name='Emotes', value=f"```{emoji_count}```")
            embed.add_field(name='Region', value=f"```{guild.region}```")
            embed.add_field(name='Verification', value=f"```{guild.verification_level}```")
            embed.add_field(name='System Channel', value=f"```{guild.system_channel}```")
            embed.add_field(name='2FA', value=f"```{fa}```")
            embed.add_field(name='Explict Content', value=f"```{guild.explicit_content_filter}```")
            embed.add_field(name='Notifications', value=f"```{notifications}```")
            embed.add_field(name='Splash', value=splash)
            embed.add_field(name='Banner', value=banner)
            embed.set_thumbnail(url=guild.icon_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("I cannot find that guild!")

    @commands.command(aliases=["whois"])
    async def userinfo(self, ctx, *, member: discord.Member = None):
        """Shows info about a user"""
        member = ctx.author if not member else member
        guild = ctx.guild
        roles = [role for role in member.roles]
        amount = len(roles) - 1
        join_position = sorted(guild.members, key=lambda m: m.joined_at).index(member) + 1
        booster = member.premium_since.__format__('%A %d %B %Y @ %H:%M:%S UTC') if member.premium_since is not None else 'False'
        status = str(member.status)
        dont = ["speak", "stream", "connect", "read_messages", "send_messages", "embed_links", "attach_files",
                "use_voice_activation", "read_message_history", "external_emojis", "add_reactions", "priority_speaker",
                "send_tts_messages", "view_guild_insights", "change_nickname"]
        array = " "
        for perm, value in member.guild_permissions:
            if perm not in dont and value is True:
                array += perm + " "
            if perm == "administrator" and value is True:
                array = "administrator"
                break
        if array == " ":
            array = "None"

        flags = " "
        for flag, value in member.public_flags:
            if value is True:
                flags += flag + " "
        if flags == " ":
            flags = "None"

        message = '\n'
        if not member.activity or not member.activities:
            message = "None"
        for activity in member.activities:
            if activity.type == discord.ActivityType.custom:
                if activity.emoji is None:
                    emoji = ''
                else:
                    emoji = activity.emoji
                message += f'\n**Custom Status**\n{emoji} {activity.name}\n'
            elif activity.type == discord.ActivityType.playing:
                message += f"\n**Playing a Game**\n{activity.name}"
                if not isinstance(activity, discord.Game):
                    if activity.details:
                        message += f"\n{activity.details}"
                    if activity.state:
                        message += f"\n{activity.state}"
                    message += "\n"
            elif activity.type == discord.ActivityType.streaming:
                message += f"\n**Live on {activity.platform}**\nStreaming [{activity.name}]({activity.url})\n"
            elif activity.type == discord.ActivityType.watching:
                message += f"\n**Watching {activity.name}**\n"
            elif activity.type == discord.ActivityType.listening:
                if isinstance(activity, discord.Spotify):
                    url = f"https://open.spotify.com/track/{activity.track_id}"
                    message += f"\n**Listening to Spotify**\n[{activity.title}]({url})\nby {', '.join(activity.artists)}"
                    if activity.album and not activity.album == activity.title:
                        message += f"\non {activity.album}"
                    message += "\n"
                else:
                    message += f"Listening to **{activity.name}**\n"

        embed = discord.Embed(title='User Info', color=member.color)
        embed.add_field(name='Name', value=f"```{member}```")
        embed.add_field(name='Status', value=f"```{status}```")
        embed.add_field(name='User ID', value=f"```{member.id}```", inline=False)
        embed.add_field(name='Activity', value=message, inline=False)
        embed.add_field(name='Booster', value=f"```{booster}```", inline=False)
        embed.add_field(name='Created At', value=f"```{member.created_at.__format__('%A %d %B %Y @ %H:%M:%S UTC')}```",
                        inline=False)
        embed.add_field(name='Joined At', value=f"```{member.joined_at.__format__('%A %d %B %Y @ %H:%M:%S UTC')}```",
                        inline=False)
        embed.add_field(name='Public Flags', value=f"```{flags}```", inline=False)
        embed.add_field(name="Join Position", value=f"```{join_position}```")
        embed.add_field(name='Color', value=f"```{member.color}```")
        embed.add_field(name='Bot', value=f"```{member.bot}```")
        embed.add_field(name='Key Permissions', value=f"```{array}```", inline=False)
        embed.add_field(name=f'Roles [{amount}]',
                        value=" ".join([role.mention for role in roles if role.name != "@everyone"]), inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def vaporwave(self, ctx):
        """Sends you an random vaporware image"""
        rand = random.randint(1, 100)

        async def fetch(session, url):
            async with session.get(url) as response:
                return await response.text()

        async with aiohttp.ClientSession() as session:
            page_html = await fetch(session,
                "https://stock.adobe.com/search?filters%5Bcontent_type%3Aphoto%5D=1&filters%5Bcontent_type%3Aillustration%5D=1&filters%5Bcontent_type%3Azip_vector%5D=1&filters%5Bcontent_type%3Avideo%5D=1&filters%5Bcontent_type%3Atemplate%5D=1&filters%5Bcontent_type%3A3d%5D=1&filters%5Binclude_stock_enterprise%5D=0&filters%5Bis_editorial%5D=0&filters%5Bcontent_type%3Aimage%5D=1&k=vaporwave&order=relevance&safe_search=1&search_page=" + str(
                    rand) + "&get_facets=0&search_type=pagination")
            soup = BeautifulSoup(page_html, "html.parser")
            data = soup.find(class_='list-thumbs-container')
            img = []
            for i in data.find_all('img'):
                if i['src'] in "https://as.ftcdn.net/r/v1/pics/95353de2e4b764e140295fca0dc63f617bae76c1/placeholders/spacer.gif":
                    img.append(i['data-lazy'])
                else:
                    img.append(i['src'])
            img = random.choice(img)
            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=img)
            embed.set_footer(text="All Images Provided By Adobe Stock - stock.adobe.com")
            await ctx.send(embed=embed)

    @commands.command()
    async def monkey(self, ctx):
        """Sends you an random monkey image"""
        rand = random.randint(1, 100)

        async def fetch(session, url):
            async with session.get(url) as response:
                return await response.text()

        async with aiohttp.ClientSession() as session:
            page_html = await fetch(session, "https://stock.adobe.com/search?filters[content_type%3Aphoto]=1&filters[content_type%3Aillustration]=0&filters[content_type%3Azip_vector]=0&filters[content_type%3Avideo]=0&filters[content_type%3Atemplate]=0&filters[content_type%3A3d]=0&filters[content_type%3Aimage]=1&k=monkey&order=relevance&safe_search=1&search_page=" + str(
            rand) + "&search_type=filter-select&limit=100&acp=&aco=monkey&get_facets=1")
            soup = BeautifulSoup(page_html, "html.parser")
            data = soup.find(class_='list-thumbs-container')
            img = []
            for i in data.find_all('img'):
                if i['src'] in "https://as.ftcdn.net/r/v1/pics/95353de2e4b764e140295fca0dc63f617bae76c1/placeholders/spacer.gif":
                    img.append(i['data-lazy'])
                else:
                    img.append(i['src'])
            img = random.choice(img)
            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=img)
            embed.set_footer(text="All Images Provided By Adobe Stock - stock.adobe.com")
            await ctx.send(embed=embed)

    @commands.command()
    async def suggest(self, ctx, *, suggestion):
        """Allows you to make an suggestion for the guild"""
        cursor = self.bot.db.acquire
        guild = ctx.guild
        vote = ['✔', '❌']
        cursor.row_factory = lambda cursor, row: row[0]
        result = await cursor.fetchrow("SELECT suggest FROM settings WHERE guild = $1", guild.id)
        channel = guild.get_channel(result)
        if channel is not None:
            embed = discord.Embed(title=f"{ctx.author} Suggestion", description=suggestion)
            sent = await channel.send(embed=embed)
            for reaction in vote:
                await sent.add_reaction(reaction)
        self.bot.db.release(cursor)

    @commands.command()
    @rccustom()
    async def createcustom(self, ctx, color, *, name):
        """Allows you to create your own custom role with an color and name"""
        cursor = await self.bot.db.acquire()
        author = ctx.message.author
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'custom')
        if result is None:
            default = await cursor.fetchrow("SELECT position, tag FROM custom WHERE guild = $1 and system = $2", guildid, 'role')
            custom = f"{name} ({default[1]})" if default[1] is not None else name
            if not re.search("#([0-9a-fA-F]{6})", color):
                await ctx.send(f"Role Color Must Be A Hex")
                return
            elif len(custom) > 50:
                await ctx.send(f"Role Name Is Over 50 Characters!")
                return
            else:
                role = await guild.create_role(reason='User created an custom role', name=custom, color=discord.Colour(int(color[1:], 16)))
                pos = guild.get_role(role_id=default[0])
                await role.edit(position=pos.position)
                await author.add_roles(role)
                await cursor.execute("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", guildid, memID, role.id, 'custom')
                await ctx.send("Custom Role created successfully!")
        else:
            await ctx.send(f"You already have a custom role!")
        await self.bot.db.release(cursor)

    # @commands.command()
    # @rcustom()
    # async def customchannel(self, ctx, type, name, topic=None):
    #     """Allows you to create your own custom channel with an name and optional topic"""
    #     cursor = await self.bot.db.acquire()
    #     if type in ('text', 'voice'):
    #         author = ctx.message.author
    #         memID = ctx.message.author.id
    #         guild = ctx.guild
    #         guildid = ctx.guild.id
    #         result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'custom')
    #         if result is not None:
    #             default = await cursor.fetchrow("SELECT position, tag FROM custom WHERE guild = $1 and system = $2", guildid, type)
    #             channel = await guild.cre

    @commands.command()
    async def editcustom(self, ctx, color, *, name):
        """Allows you to edit the color and name of your custom role"""
        cursor = await self.bot.db.acquire()
        memID = ctx.message.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'custom')
        if result is not None:
            role = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'custom')
            default = await cursor.fetchval("SELECT tag FROM custom WHERE guild = $1", guildid)
            custom = f"{name} ({default})" if default is not None else name
            crole = guild.get_role(role_id=role)
            if not re.search(r"#([0-9a-fA-F]{6})", color):
                await ctx.send(f"Role Color Must Be A Hex")
                return
            elif len(custom) > 50:
                await ctx.send(f"Role Name Is Over 50 Characters!")
                return
            else:
                await crole.edit(reason=None, name=custom, color=discord.Colour(int(color[1:], 16)))
                await ctx.send("Custom Role Edited Successfully!")

        else:
            await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createrole` to create one!")
        await self.bot.db.release(cursor)

    @commands.command()
    async def deletecustom(self, ctx):
        """Deletes your custom role that you have created"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        result = await cursor.fetchval("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'custom')
        if result is not None:
            role = await cursor.fetchval("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'custom')
            crole = guild.get_role(role_id=role)
            await crole.delete()
            await cursor.execute("DELETE FROM roles WHERE guild = ? and role = $1 and member = $2 and type = $3", guildid, role, memID, 'custom')
            await ctx.send(f"Custom Role Deleted Successfully!")
        else:
            await ctx.send(f"You need to have a custom role first! Use `{ctx.prefix}createrole` to create one!")
        await self.bot.db.release(cursor)

    @commands.command(description='Supply type with add/remove to add or remove an custom role')
    async def givecustom(self, ctx, type, member: discord.Member):
        """Allows you to add or remove your custom role to someone"""
        cursor = await self.bot.db.acquire()
        memID = ctx.author.id
        guild = ctx.guild
        guildid = ctx.guild.id
        number = await cursor.fetchval("SELECT amount FROM settings WHERE guild = $1", guildid)
        result = await cursor.fetchrow("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3", guildid, memID, 'custom')
        if result is not None:
            role = await cursor.fetchrow("SELECT role FROM roles WHERE member = $1 and guild = $2 and type = $3", memID, guildid, 'custom')
            crole = guild.get_role(role_id=role)
            if type not in ("add", "remove"):
                await ctx.send("The 'type' argument must be defined as add or remove")
                return
            if memID == member.id:
                await ctx.send("You cannot Add or Remove custom roles you already own to yourself")
                return
            if not member.bot and crole.id not in [role.id for role in member.roles] and type in "add":
                if len(crole.members) > number:
                    await ctx.send(f"You can only give this custom role to an max of {number} members")
                    await ctx.send(f"You can only give this custom role to an max of {number} members")
                    return
                await member.add_roles(crole)
            elif not member.bot and crole.id in [role.id for role in member.roles] and type in "remove":
                await member.remove_roles(crole)
            await ctx.send(content=f"Successfully {type}ed custom role to {member.name}")
        else:
            await ctx.send(f"You need to have a custom role! Use `{ctx.prefix}createrole` to create one!")
        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(User(bot))
