import os
import math

import platform
import time

import discord
import psutil
from discord.ext import commands

uses = 0

# help commands
class Help(commands.Cog, name='Help Commands'):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        global uses
        uses += 1

    @commands.command()
    async def help(self, ctx, *, command=None):
        """Shows the help menu"""

        cog_names = []

        for filename in os.listdir('./cogs'):
            if filename not in "events.py" and filename.endswith('.py'):
                cog_names.append(filename[:-3])
        if command is None:
            cog_list = ''
            cogs = ''
            for cog in self.bot.cogs:
                if cog not in "Events" and cog not in "Jishaku" and cog not in "Tasks":
                    commands_list = ''
                    for command in self.bot.get_cog(cog).get_commands():
                        commands_list += f'`{command.name}` '

                    cog_list += f'**{cog}**\n{commands_list}\n\n'

                    cogs += ' <{}>'.format(self.bot.get_cog(cog).qualified_name)

            embed = discord.Embed(title='Dionysus Help', color=0x95a5a6,
                                  description=f'{cog_list}`help` shows this message. Use `{ctx.prefix}help{cogs}` to get info about all the commands from a category, and use `{ctx.prefix}help <command name>` to get more info on a command.')

        elif command in self.bot.cogs:

            cog = self.bot.get_cog(command)
            commands_list = ''

            for command in self.bot.get_cog(command).get_commands():
                aliases = ''
                for alias in command.aliases:
                    aliases += '|{}'.format(alias)
                commands_list += f'**{command.name}**\n{command.help}\n`{ctx.prefix}[{command.name}{"".join(aliases)}]`\n\n'

            embed = discord.Embed(title=f'Dionysus {cog.qualified_name}', color=0x95a5a6,
                                  description=f'{commands_list}Use `{ctx.prefix}help <command name>` to get more info on a command.')

        else:
            comm = self.bot.get_command(command)

            aliases = ''
            if comm is None:
                raise commands.CommandNotFound("No results found!")
            for alias in comm.aliases:
                aliases += '|{}'.format(alias)

            embed = discord.Embed(title=f'Dionysus {comm.name}', color=0x95a5a6,
                                  description=f'{comm.description}\n\n`{ctx.prefix}[{comm.name}{"".join(aliases)}] {comm.signature}`\n\n{comm.help}')

        sent = await ctx.send(embed=embed)

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
        embed = discord.Embed(title="About Dionysus", color=0x0001fe)
        embed.add_field(name='By', value='Created By Nyx#8614\nSpecial Thanks to Nik#9393 For Help With Databases')
        embed.add_field(name='Version', value=self.bot.version)
        embed.add_field(name='Running On', value=ver)
        embed.add_field(name='Host', value=os)
        embed.add_field(name='Uptime', value="Since " + str(up))
        embed.add_field(name="What's New", value="rewrote bot to start using postgres sql")
        embed.add_field(name='Usage', value=usage)
        embed.add_field(name='Stats', value=stats)
        embed.add_field(name="Url's", value="Bot Invite: [Click Here](https://discord.com/api/oauth2/authorize?client_id=437447118127366154&permissions=268484848&scope=bot)")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
