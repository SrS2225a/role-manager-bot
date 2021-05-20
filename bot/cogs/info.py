import discord
import typing
import tabulate
import re

from discord.ext import commands, menus


class Info(commands.Cog, name='Information Commands'):
    """Show Information Related Info About The Server"""

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

    @commands.command()
    async def roleinfo(self, ctx, *, role: discord.Role):
        """Shows info about a role"""
        # gets various information about a role
        has = len(role.members)
        dont = ["speak", "stream", "connect", "read_messages", "send_messages", "embed_links", "attach_files",
                "use_voice_activation", "read_message_history", "external_emojis", "add_reactions", "priority_speaker",
                "change_nickname"]
        array = " "
        for perm, value in role.permissions:
            if perm not in dont and value is True:
                array += perm + " "
            if perm == "administrator" and value is True:
                array = "administrator"
                break
        if array == " ":
            array = "None"
        embed = discord.Embed(title='Role Info', color=role.color)
        embed.add_field(name="Role Name", value=f"```{role}```")
        embed.add_field(name="Role ID", value=f"```{role.id}```")
        embed.add_field(name="Created At", value=f"```{role.created_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```", inline=False)
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
        # gets various information about a channel
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
            embed.add_field(name="Channel ID", value=f"```{channel.id}```", inline=False)
            embed.add_field(name="Created At", value=f"```{channel.created_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```", inline=False)
            embed.add_field(name="Topic", value=f"```{channel.topic}```", inline=False)
            embed.add_field(name="Overwrites", value=overwrites, inline=False)
            embed.add_field(name="Slowmode", value=f"```{channel.slowmode_delay}```")
            embed.add_field(name="Pins", value=f"```{len(pins)}```")
            embed.add_field(name="Invites", value=f"```{len(invites)}```")
            embed.add_field(name="Webhooks", value=f"```{len(webhooks)}```")
            embed.add_field(name="Position", value=f"```{channel.position + 1}```")
            embed.add_field(name="Permissions Synced", value=f"```{channel.permissions_synced}```")
            embed.add_field(name="News", value=f"```{channel.is_nsfw()}```")
            embed.add_field(name="NSFW", value=f"```{channel.is_nsfw()}```")
            embed.add_field(name="Type", value=f"```{channel.type}```")
            await ctx.send(embed=embed)

        elif isinstance(channel, discord.VoiceChannel):
            overwrites = f"**Permitted**\n{yes}\n**Denied**\n{no}"
            invites = await channel.invites()
            embed = discord.Embed(title='Channel Info', value=ctx.author.color)
            embed.add_field(name="Channel Name", value=f"```{channel}```")
            embed.add_field(name="Category", value=f"```{channel.category}```")
            embed.add_field(name="Channel ID", value=f"```{channel.id}```", inline=False)
            embed.add_field(name="Created At", value=f"```{channel.created_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```", inline=False)
            embed.add_field(name="Overwrites", value=overwrites, inline=False)
            embed.add_field(name="Position", value=f"```{channel.position}```")
            embed.add_field(name="User Limit", value=f"```{channel.user_limit}```")
            embed.add_field(name="Invites", value=f"```{len(invites)}```")
            embed.add_field(name="Bitrate", value=f"```{channel.bitrate}```")
            embed.add_field(name="Permissions Synced", value=f"```{channel.permissions_synced}```")
            embed.add_field(name="Type", value=f"```{channel.type}```")
            await ctx.send(embed=embed)


    @commands.command(aliases=["serverinfo"])
    async def guildinfo(self, ctx, *, guild=None):
        """Shows info about a guild"""
        # gets various information about a server (has to be in it)
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
            embed.add_field(name='Created At', value=f"```{guild.created_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```", inline=False)
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
        # gets various information about a server member
        member = ctx.author if not member else member
        guild = ctx.guild
        roles = [role for role in member.roles]
        amount = len(roles) - 1
        join_position = sorted(guild.members, key=lambda m: m.joined_at).index(member) + 1
        booster = member.premium_since.__format__(
            '%a %b %d %Y %I:%M:%S %p UTC') if member.premium_since is not None else 'False'
        status = str(member.status)
        dont = ["speak", "stream", "connect", "read_messages", "send_messages", "embed_links", "attach_files",
                "use_voice_activation", "read_message_history", "external_emojis", "add_reactions", "priority_speaker",
                "change_nickname"]
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
                message += f'\n**Custom Status**\n{emoji} {"" if activity.name is None else activity.name}\n'
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
        embed.add_field(name='Created At', value=f"```{member.created_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```",
                        inline=False)
        embed.add_field(name='Joined At', value=f"```{member.joined_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```",
                        inline=False)
        embed.add_field(name='Public Flags', value=f"```{flags}```", inline=False)
        embed.add_field(name="Join Position", value=f"```{join_position}```")
        embed.add_field(name='Color', value=f"```{member.color}```")
        embed.add_field(name='Bot', value=f"```{member.bot}```")
        embed.add_field(name='Key Permissions', value=f"```{array}```", inline=False)
        if amount > 0:
            embed.add_field(name=f'Roles [{amount}]', value=" ".join([role.mention for role in roles if role.name != "@everyone"]), inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=['av'])
    async def avatar(self, ctx, *, member: discord.User = None):
        """Enlarges a members avatar"""
        # enhances a users avatar
        member = ctx.author if not member else member
        embed = discord.Embed(title=f"{member} Avatar")
        embed.set_image(url=member.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
