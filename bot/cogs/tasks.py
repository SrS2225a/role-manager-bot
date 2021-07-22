import asyncpg
import traceback
from datetime import datetime
from discord.ext import tasks, commands


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.boosters.add_exception_type(asyncpg.PostgresConnectionError)
        self.flags.add_exception_type(asyncpg.PostgresConnectionError)
        self.position.add_exception_type(asyncpg.PostgresConnectionError)
        self.leveling.add_exception_type(asyncpg.PostgresConnectionError)
        self.invite.add_exception_type(asyncpg.PostgresConnectionError)

        self.boosters.start()
        self.flags.start()
        self.position.start()
        self.leveling.start()
        self.invite.start()

    @tasks.loop(hours=24.0)
    async def boosters(self):
        # task for booster reward system
        try:
            async with self.bot.db.acquire() as cursor:
                async with cursor.transaction():
                    # gets settings per guild
                    for guild in self.bot.guilds:
                        announcement = await cursor.prepare(f"SELECT announce FROM settings WHERE guild = $1")
                        boosting = await cursor.prepare(
                            f"SELECT date, role FROM boost WHERE guild = $1 and type = $2")
                        boosting = await boosting.fetch(guild.id, 'boost')
                        channel = guild.get_channel(await announcement.fetchval(guild.id))
                        boosters = guild.premium_subscribers

                        # checks how long someone has been boosting for and gives the booster an reward accordingly
                        if boosting:
                            for boost in boosters:
                                await cursor.execute(f"INSERT INTO owner VALUES($1, $2, $3) on conflict do nothing",
                                                     guild.id, boost.id, 'boost')
                                for day in boosting:
                                    role = guild.get_role(role_id=day[1])
                                    if (datetime.now() - boost.premium_since).days >= int(day[0]):
                                        if channel is not None and role.id not in [role.id for role in boost.roles]:
                                            await channel.send(
                                                f"Congrats to {boost.mention} for boosting {guild} for {(datetime.now() - boost.premium_since).days} Days!")
                                        await boost.add_roles(role)

                            # checks if the booster has stopped boosting at all and remove all of their rewards
                            roles = await cursor.prepare("select member, role from owner inner join boost using ("
                                                         "guild) where boost.type = $1 and boost.guild = $2")
                            for user in await roles.fetch('boost', guild.id):
                                member = guild.get_member(int(user[0]))
                                role = guild.get_role(role_id=user[1])
                                if member is not None and member.premium_since is None:
                                    await member.remove_roles(role)
                                    await cursor.execute(
                                        f"DELETE FROM owner WHERE guild = $1 and member = $2 and type = $3",
                                        guild.id, member.id, 'boost')
        except Exception:
            traceback.print_exc()

    @boosters.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24.0)
    async def invite(self):
        try:
            async with self.bot.db.acquire() as cursor:
                async with cursor.transaction:
                    for guild in self.bot.guilds:
                        # if enabled congratulates the inviter if they complete a number of invites
                        check = await cursor.fetch(
                            "SELECT date::int, role FROM boost WHERE guild = $1 and type = $2 ORDER BY "
                            "date", guild.id, 'invite')
                        announcement = await cursor.fetchval(
                            "SELECT announce FROM settings WHERE guild = $1 LIMIT 1", guild.id)
                        if check:
                            totals = await cursor.fetch(
                                "SELECT SUM(amount), member FROM invite WHERE guild = $1 ORDER BY member", guild.id)
                            for total in totals:
                                for day in check:
                                    if total[0] >= day[0]:
                                        channel = guild.get_channel(announcement)
                                        user = guild.get_member(total[1])
                                        role = guild.get_role(day[1])
                                        if (channel, user) is not None and role.id not in [role.id for role in
                                                                                           user.roles]:
                                            await user.add_roles(role)
                                            await channel.send(f"Congrats to {user.mention} for inviting {total}"
                                                               f" users to {guild}!")
        except Exception:
            traceback.print_exc()

    @invite.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24.0)
    async def flags(self):
        try:
            async with self.bot.db.acquire() as cursor:
                async with cursor.transaction():
                    # gets all members in all guilds
                    for guild in self.bot.guilds:
                        stmt = await cursor.prepare("SELECT role, date FROM boost WHERE guild = $1 and type = $2")
                        public = await stmt.fetch(guild.id, 'flag')
                        if public:
                            for member in guild.members:
                                badges = [public_flags for public_flags in member.public_flags]
                                for flags in public:
                                    role = member.guild.get_role(flags[0])
                                    if role is not None:
                                        if (flags[1], True) in badges and role.id not in [role.id for role in
                                                                                          member.roles]:
                                            await member.add_roles(role, reason='User has Public_Flags')
                                        elif (flags[1], False) in badges and role.id in [role.id for role in
                                                                                         member.roles]:
                                            await member.remove_roles(role, reason='User no longer has Public_Flags')

        except Exception:
            traceback.print_exc()

    @flags.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24.0)
    async def position(self):
        try:
            async with self.bot.db.acquire() as cursor:
                async with cursor.transaction():
                    for guild in self.bot.guilds:
                        position = await cursor.prepare(
                            "SELECT role, member, type FROM roles WHERE guild = $1 and type = $2 or type = $3")
                        position = await position.fetch(guild.id, 'create', 'join')
                        if position:
                            for member in guild.members:
                                for position in position:
                                    if position[2] == "create":
                                        if (datetime.now() - member.created_at).total_seconds() > position[1]:
                                            role = member.guild.get_role(role_id=int(position[0]))
                                            await member.add_roles(role, reason="Auto position creation date")
                                    else:
                                        if (datetime.now() - member.joined_at).total_seconds() > position[1]:
                                            role = member.guild.get_role(role_id=int(position[0]))
                                            await member.add_roles(role, reason="Auto position join date")

        except Exception:
            traceback.print_exc()

    @position.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24.0)
    async def leveling(self):
        try:
            async with self.bot.db.acquire() as cursor:
                async with cursor.transaction():
                    for guild in self.bot.guilds:
                        top = await cursor.prepare(
                            "SELECT role, type, level, user_id FROM leveling left join levels ON "
                            "leveling.guild=levels.guild_id WHERE guild = $1 and system = $2 ORDER BY lvl DESC, "
                            "exp DESC")
                        top = await top.fetch(guild.id, 'top')
                        for top in top:
                            if top[1] == 'day' and top[2] == 1:
                                member = guild.get_member(top[3])
                                role = guild.get_role(top[0])
                                member.add_roles(role)
                            elif top[1] == 'week' and top[2] == 7:
                                member = guild.get_member(top[3])
                                role = guild.get_role(top[0])
                                member.add_roles(role)
                            elif top[1] == 'month' and top[2] == 30:
                                member = guild.get_member(top[3])
                                role = guild.get_role(top[0])
                                member.add_roles(role)
                            await cursor.execute(
                                "UPDATE leveling SET level = $1 < 30 OR 0 WHERE guild = $1 and system = $2", top[2] + 1,
                                guild.id, 'top')

        except Exception:
            traceback.print_exc()

    @leveling.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Tasks(bot))
