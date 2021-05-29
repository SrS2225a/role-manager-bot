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

    # gets the command signature (I.E. prefix, name, and aliases)
    def get_command_signature(self, command):
        aliases = ''
        for alias in command.aliases:
            aliases += '({})'.format(alias)
        return f'{self.clean_prefix}{command.qualified_name} {aliases}'

    # shows the items of all available commands per cog
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Dionysus Help', colour=self.COLOUR)

        description = self.context.bot.description
        if description:
            embed.description = description

        for cog, commands in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(commands, sort=True)
            if commands and name != 'Jishaku' and filtered:
                value = '\u2002'.join(f"`{c.name}`" for c in commands)
                embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    # shows the description of all available commands for a cog 
    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f'Dionysus Help - {cog.qualified_name}', colour=self.COLOUR)
        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            var = self.get_command_signature(command)
            if var != '&jishaku':
                embed.add_field(name=var, value=command.help or '...', inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    # shows all related info about a particuler command
    async def send_command_help(self, command):
        embed = discord.Embed(title=f'Dionysus Help - {command.name}', color=self.COLOUR)
        aliases = ''
        filtered = await self.filter_commands([command], sort=True)
        for alias in command.aliases:
            aliases += '({})'.format(alias)
        if command.name != 'jishaku' and filtered:
            embed.description = command.description
            embed.add_field(name=f'{self.clean_prefix}{command.qualified_name} {command.signature}', value=command.help or '...')
            embed.set_footer(text="Aliases: " + aliases)

        await self.get_destination().send(embed=embed)

# help commands
class Help(commands.Cog, name='Help Commands'):
    """Commands that give you info about the bot"""
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
        number = 0
        for members in self.bot.get_all_members():
            number += 1
        usage = f"CPU: {[round(x / psutil.cpu_count() * 100, 2) for x in psutil.getloadavg()]} \nRAM: {str(psutil.virtual_memory()[2])}% \nNetwork: Recived {round(math.floor(psutil.net_io_counters().bytes_recv / 1073742000), 2)} GB, Sent {round(math.floor(psutil.net_io_counters().bytes_sent / 1073742000), 2)}GB"
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
    async def ping(self, ctx):
        """Responds with the bots ping between the client and discord"""
        # gets the bots current ping
        await ctx.send(f"The ping is: {round(self.bot.latency * 1000)} ms!")


def setup(bot):
    bot.add_cog(Help(bot))

