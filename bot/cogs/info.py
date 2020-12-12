import discord
import typing
from discord.ext import commands, menus


class Info(commands.Cog, name='Information Commands'):
    """Show Information Related Info About The Server"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="You can supply arg with 'None' to list members without a specified role")
    async def listmembers(self, ctx, *, role):
        """List members by a role or no role"""
        if role in "no-roles":
            members = []
            for member in ctx.guild.members:
                if len(member.roles) == 1:
                    members.append(member.name + "#" + member.discriminator)
        elif role in ("--none",):
            role = await commands.RoleConverter().convert(ctx, role.split("--none")[1])
            members = []
            for member in ctx.guild.members:
                if role.id not in [role.id for role in member.roles]:
                    members.append(member.name + "#" + member.discriminator + " " + str(member.id))
        else:
            role = await commands.RoleConverter().convert(ctx, role)
            members = []
            for member in ctx.guild.members:
                if role.id in [role.id for role in member.roles]:
                    members.append(member.name + "#" + member.discriminator + " " + str(member.id))

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
        roles = []
        for role in ctx.guild.roles[::-1]:
            roles.append(role.name + " " + str(role.id))

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
            embed.add_field(name='Created At', value=f"```{guild.created_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```",
                            inline=False)
            embed.add_field(name='Boosts',
                            value=f"```Level {guild.premium_tier} With {guild.premium_subscription_count} Boosts And {len(guild.premium_subscribers)} Actual```",
                            inline=False)
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
        embed.add_field(name='Created At', value=f"```{member.created_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```",
                        inline=False)
        embed.add_field(name='Joined At', value=f"```{member.joined_at.__format__('%a %b %d %Y %I:%M:%S %p UTC')}```",
                        inline=False)
        embed.add_field(name='Public Flags', value=f"```{flags}```", inline=False)
        embed.add_field(name="Join Position", value=f"```{join_position}```")
        embed.add_field(name='Color', value=f"```{member.color}```")
        embed.add_field(name='Bot', value=f"```{member.bot}```")
        embed.add_field(name='Key Permissions', value=f"```{array}```", inline=False)
        if roles:
            embed.add_field(name=f'Roles [{amount}]', value=" ".join([role.mention for role in roles if role.name != "@everyone"]), inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=['av'])
    async def avatar(self, ctx, *, member: discord.User = None):
        """Enlarges a members avatar"""
        member = ctx.author if not member else member
        embed = discord.Embed(title=f"{member} Avatar")
        embed.set_image(url=member.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
