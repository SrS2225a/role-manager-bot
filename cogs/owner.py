import aiohttp
import discord
from discord.ext import commands


client = discord.Client()


# owner commands
class Owner(commands.Cog, name="Owner Commands"):
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
