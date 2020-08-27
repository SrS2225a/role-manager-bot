from datetime import datetime

from discord.ext import tasks, commands


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boosters.start()
        self.flags.start()

    @tasks.loop(hours=12.0)
    async def boosters(self):
        # task for booster reward system
        try:
            cursor = await self.bot.db.acquire()
            for guild in self.bot.guilds:
                announcement = await cursor.fetchrow(f"SELECT announce FROM settings WHERE guild = $1", guild.id)
                boosting = await cursor.fetch(f"SELECT date, role FROM boost WHERE guild = $1 and type = $2", guild.id, 'boost')
                channel = guild.get_channel(announcement[0])
                booster = guild.premium_subscribers

                # checks how long someone has been boosting for and gives the booster an reward accordingly
                for boost in booster:
                    check = await cursor.fetchrow(f"SELECT member FROM owner WHERE guild = $1 and member = $2", guild.id, boost.id)
                    for day in boosting:
                        if check is None:
                            await cursor.fetchrow(f"INSERT INTO owner(guild, member)VALUES($1, $2)", guild.id, boost.id)
                        role = guild.get_role(role_id=day[1])
                        if (datetime.now()-boost.premium_since).days == int(day[0]):
                            if channel is not None and role.id not in [role.id for role in boost.roles]:
                                await channel.send(f"Congrats to {boost.mention} for boosting {guild} for {(datetime.now()-boost.premium_since).days} Days!")
                            await boost.add_roles(role)

                # checks if the booster has stopped boosting at all and remove all of their rewards
                member = await cursor.fetch(f"SELECT member FROM owner WHERE guild = $1", guild.id)
                for user in member:
                    member = guild.get_member(int(user[0]))
                    if member is not None and member.premium_since is None:
                        roles = await cursor.fetch(f"SELECT role FROM boost WHERE type = $1 and guild = $2 ORDER BY date DESC", 'boost', guild.id)
                        await cursor.execute(f"DELETE FROM owner WHERE guild = $1 and member = $2", guild.id, member.id)
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

    @tasks.loop(hours=18.0)
    async def flags(self):
        try:
            cursor = await self.bot.db.acquire()
            for member in self.bot.get_all_members():
                for flag, value in member.public_flags:
                    stmt = await cursor.prepare("SELECT role FROM boost WHERE guild = $1 and type = $2 and date = $3")
                    public = await stmt.fetchval(member.guild.id, 'flag', flag)
                    role = member.guild.get_role(role_id=public)
                    if value is True and public not in [role.id for role in member.roles] and public is not None:
                        await member.add_roles(role, reason='User has Public_Flags')
                    elif value is False and public in [role.id for role in member.roles] and public is not None:
                        await member.remove_roles(role, reason='User has Public_Flags')
            await self.bot.db.release(cursor)

        except Exception:
            import traceback
            traceback.print_exc()

    @flags.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Tasks(bot))
