import traceback
import discord
from discord.ext import commands


class Handler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # WHO ADDED LOG
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        server = self.bot.get_guild(531247629649182750)
        channel = server.get_channel(844387430743801896)
        await channel.send(f"Dionysus was added into guild **{guild} ({guild.id})**. "
                           f"We now have **{len(self.bot.guilds)}** guilds!")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        server = self.bot.get_guild(531247629649182750)
        channel = server.get_channel(844387430743801896)
        await channel.send(f"Dionysus was removed from guild **{guild} ({guild.id})**. "
                           f"We now have **{len(self.bot.guilds)}** guilds!")

    # COMMAND RAN LOG
    @commands.Cog.listener()
    async def on_command(self, ctx):
        guild = ctx.guild
        server = self.bot.get_guild(531247629649182750)
        channel = server.get_channel(866678659862626355)
        await channel.send(f"A new command was ran **{ctx.command}** in guild **{guild} ({guild.id})**")
        self.bot.uses += 1

    # ERROR HANDLER
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        server = self.bot.get_guild(531247629649182750)
        channel = server.get_channel(840276875301224479)
        etype = type(error)
        trace = error.__traceback__
        verbosity = 2
        exception = traceback.format_exception(etype, error, trace, verbosity)
        traceback_text = ''.join(exception)
        if isinstance(error, commands.CommandInvokeError):
            embed = discord.Embed(title="An Unexpected Error Occurred", description=f"During the handling of this "
                                                                                    f"command and unexpected error "
                                                                                    f"occurred. \nThis error has been "
                                                                                    f"automatically sent to the bot "
                                                                                    f"developers and will get to it "
                                                                                    f"ASAP. \nTry repeating the "
                                                                                    f"command, or if you need faster "
                                                                                    f"attention join the support "
                                                                                    f"server: "
                                                                                    f"https://discord.gg/JHkhnzDvWG "
                                                                                    f"\n\n `{error}`")
            await ctx.send(embed=embed)
            await channel.send(f"`New exception occurred in guild {ctx.guild} for command {ctx.command}`"
                               f"\n```py\n{traceback_text}```")
        elif not isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Error: {error}")

    # ERROR HANDLER
    @commands.Cog.listener()
    async def on_error(self, event, error):
        # finds who is is in the team and send all an error report when it happens upon a general error
        guild = self.bot.get_guild(531247629649182750)
        channel = guild.get_channel(840276875301224479)
        etype = type(error)
        trace = error.__traceback__
        verbosity = 2
        exception = traceback.format_exception(etype, error, trace, verbosity)
        traceback_text = ''.join(exception)
        if not isinstance(error, discord.Forbidden) or not isinstance(error, discord.NotFound):
            await channel.send(f"`New exception occurred for event listener {event}`\n ```py\n{traceback_text}```")


def setup(bot):
    bot.add_cog(Handler(bot))
