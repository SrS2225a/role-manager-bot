from datetime import datetime

from discord.ext import tasks, commands


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boosters.start()
        self.flags.start()

    @tasks.loop(hours=16.0)
    async def boosters(self):
        # task for booster reward system
        try:
            cursor = await self.bot.db.acquire()
            # gets settings per guild
            for guild in self.bot.guilds:
                announcement = await cursor.prepare(f"SELECT announce FROM settings WHERE guild = $1")
                boosting = await cursor.prepare(f"SELECT date, role FROM boost WHERE guild = $1 and type = $2")
                channel = guild.get_channel(await announcement.fetchval(guild.id))
                booster = guild.premium_subscribers

                # checks how long someone has been boosting for and gives the booster an reward accordingly
                for boost in booster:
                    member = await cursor.prepare(f"SELECT member FROM owner WHERE guild = $1 and member = $2 and type = $3")
                    if await member.fetchval(guild.id, boost.id, 'boost') is None:
                        await cursor.execute(f"INSERT INTO owner(guild, member, type)VALUES($1, $2, $3)", guild.id,  boost.id, 'boost')
                    for day in await boosting.fetch(guild.id, 'boost'):
                        role = guild.get_role(role_id=day[1])
                        if (datetime.now()-boost.premium_since).days >= int(day[0]):
                            if channel is not None and role.id not in [role.id for role in boost.roles]:
                                await channel.send(f"Congrats to {boost.mention} for boosting {guild} for {(datetime.now()-boost.premium_since).days} Days!")
                            await boost.add_roles(role)

                # checks if the booster has stopped boosting at all and remove all of their rewards
                member = await cursor.prepare(f"SELECT member FROM owner WHERE guild = $1")
                roles = await cursor.prepare(f"SELECT role FROM boost WHERE type = $1 and guild = $2")
                roles = await roles.fetch('boost', guild.id)
                for user in await member.fetch(guild.id):
                    member = guild.get_member(int(user[0]))
                    if member is not None and member.premium_since is None:
                        await cursor.execute(f"DELETE FROM owner WHERE guild = $1 and member = $2 and type = $3", guild.id, member.id, 'boost')
                        for role in roles:
                            role = guild.get_role(role_id=role[0])
                            await member.remove_roles(role)
            await self.bot.db.release(cursor)

        except Exception:
            import traceback
            traceback.print_exc()

    @boosters.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=16.0)
    async def flags(self):
        try:
            cursor = await self.bot.db.acquire()
            # gets all members in all guilds
            for member in self.bot.get_all_members():
                # matches the users flags against the settings the server set and if we have it, give us the set role 
                for flag, value in member.public_flags:
                    stmt = await cursor.prepare("SELECT role FROM boost WHERE guild = $1 and type = $2 and date = $3")
                    public = await stmt.fetchval(member.guild.id, 'flag', flag)
                    role = member.guild.get_role(public)
                    if value is True and public not in [role.id for role in member.roles] and public is not None:
                        await member.add_roles(role, reason='User has Public_Flags')
                    elif value is False and public in [role.id for role in member.roles] and public is not None:
                        await member.remove_roles(role, reason='User no longer has Public_Flags')
            await self.bot.db.release(cursor)

        except Exception:
            import traceback
            traceback.print_exc()

    @flags.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Tasks(bot))
