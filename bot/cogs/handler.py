import traceback
import discord
from discord.ext import commands


class Handler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ERROR HANDLER
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # finds who is is in the team and send all an error report when it happens upon a command error
        guild = self.bot.get_guild(531247629649182750)
        channel = guild.get_channel(840276875301224479)
        error_return = f"Error: {error}"
        etype = type(error)
        trace = error.__traceback__
        verbosity = 2
        exception = traceback.format_exception(etype, error, trace, verbosity)
        traceback_text = ''.join(exception)
        print(trace)
        print(error.__)
        if isinstance(error, commands.CommandInvokeError):
            embed = discord.Embed(title="An Exception Occurred", description=f"Durning handling of this command, an unexpected error has occured\n This error has been sent to the bot dev and will get to it ASAP \n\n `{error}`")
            await ctx.send(embed=embed)
            await channel.send(f"`New exception occurred in guild {ctx.guild} for command {ctx.command}`\n```py\n{traceback_text}```")
        elif not isinstance(error, commands.CommandNotFound):
            await ctx.send(error_return)
        return


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
