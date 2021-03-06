from discord.ext import commands


# help commands
class Help(commands.Cog, name='Commands'):
    """[These Commands sets the behavoir of other commands](https://github.com/SrS2225a/role-manager-bot/wiki/Commands)"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def command(self, ctx):
        """Allows you to enable/disable a command or cog"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @command.group()
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx, command):
        """Allows you to enable command or cog"""
        cursor = await self.bot.db.acquire()
        cog = self.bot.get_cog(command)
        command = self.bot.get_command(command)
        guild = ctx.guild
        if command is not None:
            if command.parent is not None:
                command = command.parent
            await cursor.execute("DELETE FROM boost WHERE guild = $1 and date = $2 and type = $3", guild.id,
                                 command.name, 'command')
            await ctx.send(f"Command Enabled Successfully!")
        elif cog is not None:
            for command in cog.get_commands():
                await cursor.execute("DELETE FROM boost WHERE guild = $1 and date = $2 and type = $3", guild.id,
                                     command.name, 'command')
            await ctx.send(f"Cog Enabled Successfully!")
        else:
            await ctx.send("Not a valid command or cog!")
        await self.bot.db.release(cursor)

    @command.group()
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx, command):
        """Allows you to disable a command or cog"""
        cursor = await self.bot.db.acquire()
        cog = self.bot.get_cog(command)
        command = self.bot.get_command(command)
        guild = ctx.guild
        if command is not None:
            if command.parent is not None:
                command = command.parent
            if command.name == "jishaku":
                await ctx.send("Bot owner commands are mandatory and cannot be turned off!")
            elif command.name == "command":
                await ctx.send(
                    "Disabling this command will prevent you from enabling/disabing any more commands, and thus "
                    "cannot be turned off!")
            else:
                await cursor.execute("INSERT INTO boost(guild, date, type) VALUES($1, $2, $3)", guild.id, command.name,
                                     'command')
                await ctx.send(f"Command Disabled Successfully!")
        elif cog is not None:
            for command in cog.get_commands():
                if command.name == "command":
                    await ctx.send(
                        "Disabling this command will prevent you from enabling/disabing any more commands, and thus "
                        "cannot be turned off!")
                else:
                    await cursor.execute("INSERT INTO boost(guild, date, type) VALUES($1, $2, $3)", guild.id,
                                         command.name, 'command')
            await ctx.send(f"Cog Disabled Successfully!")
        else:
            await ctx.send("Not a valid command or cog!")

    @commands.command(brief="prefix &", aliases=['pre'])
    async def prefix(self, ctx, prefix=None):
        """Views or sets a prefix"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        if prefix is not None:
            if ctx.author.guild_permissions.manage_guild:
                result = await cursor.fetchval("SELECT auth FROM settings WHERE auth = $1 and guild = $2", prefix,
                                               guild)
                search = await cursor.fetchval("SELECT guild FROM settings WHERE guild = $1", guild)
                if result is not None:
                    await cursor.execute("UPDATE settings SET auth = NULL and guild = $1", guild)
                    await ctx.send("Custom Prefix Removed Successfully!")
                elif search is None:
                    await cursor.execute("INSERT INTO settings(guild, auth) VALUES($1, $2)", guild, prefix)
                    await ctx.send("Custom Prefix Set Successfully!")
                else:
                    await cursor.execute("UPDATE settings SET auth = $1 WHERE guild = $2", prefix, guild)
                    await ctx.send("Custom Prefix Set Successfully!")
            else:
                await ctx.send("Error: You are missing Manage Server permission(s) to change bot's prefix.")
        else:
            prefix = await cursor.fetchval("SELECT auth FROM settings WHERE guild = $1", guild)
            await ctx.send(f"Your current set prefix is: `{prefix or '*'}`")
        await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Help(bot))
