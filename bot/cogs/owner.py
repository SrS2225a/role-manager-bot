import aiohttp
import discord

from discord.ext import commands
from jishaku.cog import JishakuBase, jsk
from jishaku.flags import JISHAKU_HIDE
from jishaku.metacog import GroupCogMeta


class Debugging(JishakuBase, metaclass=GroupCogMeta, command_parent=jsk):
    @commands.group(name="dev", hidden=JISHAKU_HIDE, invoke_without_command=True, ignore_extra=False)
    async def jsk(self, ctx: commands.Context):
        """
        This overwrites the `jsk debug` command!
        """

        await ctx.send(f"Average websocket latency: {round(self.bot.latency * 1000, 2)}ms")

    # Or add other, new commands
    # Every @commands.command() in here will be parented to the command_parent,
    # in this case the default jsk Group.
    # You can also make your own Group and use it as the command_parent instead.
    ...

# owner commands
class Owner(commands.Cog, name="Owner Commands"):
    """Commands for bot owners."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Shuts down the bot"""
        await ctx.send("Shutting down")
        await self.bot.close()

    @commands.command()
    @commands.is_owner()
    async def setname(self, ctx, *, arg):
        """Allows you to edit the name of the bot"""
        await ctx.bot.user.edit(username=arg)
        await ctx.send(f"Successuly changed bot's name to: {arg}")

    @commands.command()
    @commands.is_owner()
    async def setavatar(self, ctx, *, arg):
        """Allows you to edit the profile picture of the bot"""
        async with aiohttp.ClientSession() as session:
            async with session.get(str(arg)) as resp:
                data = await resp.read()

                await ctx.bot.user.edit(avatar=data)
                await ctx.send(f"Successfully changed bot's avatar to: {arg}")


def setup(bot):
    bot.add_cog(Owner(bot))
