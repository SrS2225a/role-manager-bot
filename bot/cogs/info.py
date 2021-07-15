import os
import math
import typing

import platform
import time

import discord
import psutil
from discord.ext import commands


uses = 0

class EmbedHelpCommand(commands.HelpCommand):
    COLOUR = 0x95a5a6
    def get_ending_note(self):
        return "The Greek themed discord bot that makes your experience that much better @ dionysus.gg"

    def get_heading_note(self):
        return f"Type `{self.clean_prefix}help<command>` for specific command help.  e.g. `{self.clean_prefix}help support`"

    # shows the items of all available commands
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Dionysus Help', colour=self.COLOUR)

        embed.description = self.get_heading_note()

        for cog, commands in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            if commands and name != 'Jishaku':
                desc = f"**{cog.description}**\n\n"
                value = '\u2002'.join(f'`{c.name}`' for c in commands)
                val = desc + value
                embed.add_field(name=name, value=val, inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

        # shows all related info about a particuler command
    async def send_command_help(self, command):
        embed = discord.Embed(title=f'Dionysus Help', color=self.COLOUR)
        aliases = ''
        aliases += ', '.join(alias for alias in command.aliases)
        embed.description = command.description
        embed.add_field(name=f'{self.clean_prefix}{command.qualified_name} {command.signature}', value=command.help or '...', inline=False)
        if command.brief:
            embed.add_field(name='Example', value=self.clean_prefix + command.brief)
        if aliases != '':
            embed.set_footer(text="Aliases: " + aliases)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=f"Dionysus Help", color=self.COLOUR)
        aliases = ''
        aliases += ', '.join(alias for alias in group.aliases)
        if aliases != '':
            embed.set_footer(text="Aliases: " + aliases)
        if group.hidden:
            embed.description = f"**{group.help}** \n\n {group.description}"
        else:
            embed.description = group.description
            embed.add_field(name=f'{self.clean_prefix}{group.name} {group.signature}', value=group.help)

        value = '\n'.join(f"`{self.clean_prefix}{command.qualified_name}` - {command.help}" for command in group.commands)
        embed.add_field(name=f'Commands', value=value or '...', inline=False)
        if group.brief:
            embed.add_field(name='Example', value=self.clean_prefix + group.brief)

        await self.get_destination().send(embed=embed)

# help commands
class Help(commands.Cog, name='Information'):
    """[Gets Information About The Bot Or Server](https://github.com/SrS2225a/role-manager-bot/wiki/Information)"""
    # sets up help command from the class EmbedHelpCommand
    def __init__(self, bot):
        self.bot = bot
        self.bot._original_help_command = bot.help_command
        bot.help_command = EmbedHelpCommand()
        bot.help_command.cog = self

    # increments uses when a command is runned
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        global uses
        uses += 1

    @commands.command(aliases=["status", "info"])
    async def about(self, ctx):
        """Shows info about the bot"""
        # basiclly shows related information about the bot such as usage statstics, version, and resources
        global uses
        os = str(platform.system() + " " + platform.release()) + " - " + "Python " + platform.python_version()
        p = psutil.Process()
        up = time.strftime("%Y-%m-%d %H:%M " + "UTC", time.gmtime(p.create_time()))
        # Cannot use len() here, python will complain. Stupid
        number = 0
        for members in self.bot.get_all_members():
            number += 1
        usage = f"CPU: {[round(x / psutil.cpu_count() * 100, 2) for x in psutil.getloadavg()]} \nRAM: {str(psutil.virtual_memory()[2])}% \nNetwork: Download {round(math.floor(psutil.net_io_counters().bytes_recv / 1073742000), 2)} GB, Upload {round(math.floor(psutil.net_io_counters().bytes_sent / 1073742000), 2)}GB"
        stats = f"Visable Guilds: {len(self.bot.guilds)} \nVisable Members: {number} \nShards: 0 \nCommands Ran: {uses}"
        embed = discord.Embed(title="About Dionysus", color=0x0001fe)
        embed.add_field(name='Credits', value='**Main Devs**\n<@!270848136006729728> <@!508455796783317002>\n**Contributors**\n<@!332180997653135383>')
        embed.add_field(name="Url's", value="Bot Invite: [Click Here](https://discord.com/api/oauth2/authorize?client_id=437447118127366154&permissions=8&scope=bot)\nOpen Source: [Click Here](https://github.com/SrS2225a/role-manager-bot)\nSupport: [Click Here](https://discord.gg/JHkhnzDvWG) \nDocumentation: [Click Here](https://github.com/SrS2225a/role-manager-bot/wiki)\nTO-DO: [Click Here](https://trello.com/b/Y86Q7qKA/dionysus-bot)\ntop.gg: [Click Here](https://top.gg/bot/437447118127366154)")
        embed.add_field(name='Stats', value=stats)
        embed.add_field(name='Usage', value=usage)
        embed.add_field(name='Uptime', value="Since " + up)
        embed.add_field(name='Running On', value=os)
        await ctx.send(embed=embed)

    @commands.command()
    async def support(self, ctx):
        """Gives you a link to the Dionysus support server"""
        await ctx.send("https://discord.gg/JHkhnzDvWG")

    @commands.command()
    async def invite(self, ctx):
        """Give you a link to invite the bot"""
        ctx.send("https://discord.com/api/oauth2/authorize?client_id=437447118127366154&permissions=8&scope=bot")

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
        channel = channel or ctx.channel
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
        guild = self.bot.get_guild(guild) or ctx.guild
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
        member = member or ctx.author
        if not member.pending:
            roles = [role for role in member.roles]
            amount = len(roles) - 1
            join_position = sorted(ctx.guild.members, key = lambda m: m.joined_at or m.created_at).index(member) + 1
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

def setup(bot):
    bot.add_cog(Help(bot))

