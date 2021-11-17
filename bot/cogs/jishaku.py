import discord
from discord.ext import commands
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from jishaku.features.baseclass import Feature


class CustomDebugCog(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    @Feature.Command(parent="jsk", name="block", aliases=['blacklist'], hidden=True)
    async def jsk_block(self, ctx: commands.Context, user: discord.User, *, reason = None):
        """Blocks a user from using the bot"""
        cursor = await self.bot.db.acquire()
        reason = reason or 'abuse'
        result = await cursor.fetchval("SELECT message FROM blacklist WHERE member = $1", user.id)
        if result:
            await cursor.execute("DELETE FROM blacklist WHERE member = $1", user.id)
            await ctx.send(f"Successfully unblocked {user} from Dionysus with the reason {reason}")
        else:
            server = self.bot.get_guild(531247629649182750)
            channel = server.get_channel(841455998542938143)
            await cursor.execute("INSERT INTO blacklist(member, message) VALUES($1, $2)", user.id, reason)
            await ctx.send(f"Successfully blocked **{user}** from Dionysus with the reason **{reason}**")
            await channel.send(f"**{user}** was just blacklisted from using Dionysus for **{reason}**!")


def setup(bot: commands.Bot):
    bot.add_cog(CustomDebugCog(bot=bot))