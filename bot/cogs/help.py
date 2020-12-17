import os
import math

import platform
import time

import discord
import psutil
from discord.ext import commands

uses = 0

class EmbedHelpCommand(commands.HelpCommand):
    COLOUR = 0x95a5a6
    def get_ending_note(self):
        return f"Use {self.clean_prefix}help<cog name> to get info about all the commands from a category, and use {self.clean_prefix}help <command name> to get more info on a command."

    def get_command_signature(self, command):
        aliases = ''
        for alias in command.aliases:
            aliases += '({})'.format(alias)
        return f'{self.clean_prefix}{command.qualified_name} {aliases}'

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Dionysus Help', colour=self.COLOUR)

        description = self.context.bot.description
        if description:
            embed.description = description

        for cog, commands in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            if commands and name != 'Jishaku':
                value = '\u2002'.join(f"`{c.name}`" for c in commands)
                embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f'Dionysus Help - {cog.qualified_name}', colour=self.COLOUR)
        if cog.description:
            embed.description = cog.description

        filtered = cog.get_commands()
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.help or '...', inline=False)

        embed.set_footer(text=self.get_ending_note())
        if command.qualified_name != 'jishaku':
            await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        aliases = ''
        for alias in command.aliases:
            aliases += '({})'.format(alias)
        if command.name != 'jishaku':
            embed = discord.Embed(title=f'Dionysus Help - {command.name}', color=self.COLOUR, description=f'{command.description}\n\n')
            embed.add_field(name=f'{self.clean_prefix}{command.qualified_name} {command.signature}', value=command.help or '...')
            embed.set_footer(text="Aliases: " + aliases)

        await self.get_destination().send(embed=embed)

# help commands
class Help(commands.Cog, name='Help Commands'):
    """Commands that give you info about the bot"""
    def __init__(self, bot):
        self.bot = bot
        self.bot._original_help_command = bot.help_command
        bot.help_command = EmbedHelpCommand()
        bot.help_command.cog = self

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        global uses
        uses += 1

    @commands.command(aliases=["status", "info"])
    async def about(self, ctx):
        """Shows info about the bot"""
        global uses
        ver = "Python " + platform.python_version()
        os = str(platform.system() + " " + platform.release() + " " + platform.version())
        p = psutil.Process()
        up = time.strftime("%Y-%m-%d %H:%M " + "UTC", time.gmtime(p.create_time()))
        number = 0
        for members in self.bot.get_all_members():
            number += 1
        usage = f"CPU: {[x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]} \nRAM: {str(psutil.virtual_memory()[2])}% \nNetwork: Recived {round(math.floor(psutil.net_io_counters().bytes_recv / 1073742000), 2)} GB, Sent {round(math.floor(psutil.net_io_counters().bytes_sent / 1073742000), 2)}GB"
        stats = f"Visable Guilds: {len(self.bot.guilds)} \nVisable Members: {number} \nShards: 0 \nCommands Ran: {uses}"
        embed = discord.Embed(title="About Dionysus", description="`Note: This public bot is part of the private bot Derivi built for the server known as New Line and affiliates`", color=0x0001fe)
        embed.add_field(name='Credits', value='Created By Nyx#8614\nSpecial Thanks to Nik#9393 For Help With Databases and Sugden#0562 for the extra help with code')
        embed.add_field(name="What's New", value="improved help, added a member club blacklist command, and some other small things")
        embed.add_field(name="Url's", value="Bot Invite: [Click Here](https://discord.com/api/oauth2/authorize?client_id=437447118127366154&permissions=8&scope=bot)\nOpen Source: [Click Here](https://github.com/SrS2225a/role-manager-bot)\nSupport: [Click Here](https://discord.gg/Ax2upvf) (Part Of Derivi Development)")
        embed.add_field(name='Version', value=self.bot.version)
        embed.add_field(name='Running On', value=ver)
        embed.add_field(name='Host', value=os)
        embed.add_field(name='Uptime', value="Since " + up)
        embed.add_field(name='Usage', value=usage)
        embed.add_field(name='Stats', value=stats)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))

