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
        team = await self.bot.application_info()
        teams = team.team.members
        error_return = f"Error: {error} (Command: {ctx.command})"
        etype = type(error)
        trace = error.__traceback__
        verbosity = 2
        exception = traceback.format_exception(etype, error, trace, verbosity)
        traceback_text = ''.join(exception)
        if isinstance(error, commands.CommandInvokeError) and not isinstance(error, discord.Forbidden):
            embed = discord.Embed(title="An Exception Occurred", description=f"Durning handling of this command, an unexpected error has occured\n This error has been sent to the bot dev and will get to it ASAP \n\n `{error}`")
            await ctx.send(embed=embed)
            for me in teams:
                try: 
                    user = self.bot.get_user(me.id)
                    await user.send(f"`New exception occurred in guild {ctx.guild} for command {ctx.command}`\n```py\n{traceback_text}```")
                except discord.Forbidden:
                    pass
            return
        elif not isinstance(error, commands.CommandNotFound):
            await ctx.send(error_return)
            return


    # ERROR HANDLER
    @commands.Cog.listener()
    async def on_error(self, event, error):
        # finds who is is in the team and send all an error report when it happens upon a general error
        team = await self.bot.application_info()
        teams = team.team.members
        etype = type(error)
        trace = error.__traceback__
        verbosity = 2
        exception = traceback.format_exception(etype, error, trace, verbosity)
        traceback_text = ''.join(exception)
        if not isinstance(error, discord.Forbidden):
            for me in teams:
                try: 
                    me = self.bot.get_user(me)
                    await me.send(f"New exception occurred for event listener {event}")
                    await me.send(f"```py\n{traceback_text}```")
                except discord.Forbidden:
                    pass

def setup(bot):
    bot.add_cog(Handler(bot))
