import traceback
from datetime import datetime
from discord.ext import tasks, commands


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boosters.start()
        self.flags.start()
        self.position.start()

    @tasks.loop(hours=24.0)
    async def boosters(self):
        # task for booster reward system
        try:
            async with self.bot.db.acquire() as connection:
                async with connection.transaction():
                    # gets settings per guild
                    for guild in self.bot.guilds:
                        announcement = await connection.prepare(f"SELECT announce FROM settings WHERE guild = $1")
                        boosting = await connection.prepare(f"SELECT date, role FROM boost WHERE guild = $1 and type = $2")
                        boosting = await boosting.fetch(guild.id, 'boost')
                        channel = guild.get_channel(await announcement.fetchval(guild.id))
                        boosters = guild.premium_subscribers

                        # checks how long someone has been boosting for and gives the booster an reward accordingly
                        if boosting:
                            for boost in boosters:
                                await connection.execute(f"INSERT INTO owner VALUES($1, $2, $3) on conflict do nothing", guild.id,  boost.id, 'boost')
                                for day in boosting:
                                    role = guild.get_role(role_id=day[1])
                                    if (datetime.now()-boost.premium_since).days >= int(day[0]):
                                        if channel is not None and role.id not in [role.id for role in boost.roles]:
                                            await channel.send(f"Congrats to {boost.mention} for boosting {guild} for {(datetime.now()-boost.premium_since).days} Days!")
                                        # await boost.add_roles(role)

                            # checks if the booster has stopped boosting at all and remove all of their rewards
                            roles = await connection.prepare("select member, role from owner inner join boost using (guild) where boost.type = $1 and boost.guild = $2")
                            for user in await roles.fetch('boost', guild.id):
                                member = guild.get_member(int(user[0]))
                                role = guild.get_role(role_id=user[1])
                                if member is not None and member.premium_since is None:
                                    await member.remove_roles(role)
                                    await connection.execute(f"DELETE FROM owner WHERE guild = $1 and member = $2 and type = $3", guild.id, member.id, 'boost')


        except Exception:
            traceback.print_exc()

    @boosters.before_loop
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
                                    if (flags[1], True) in badges and flags[0] not in [role.id for role in member.roles]:
                                        await member.add_roles(role, reason='User has Public_Flags')
                                    elif (flags[1], False) in badges and flags[0] in [role.id for role in member.roles]:
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
                        position = await cursor.prepare("SELECT role, member, type FROM roles WHERE guild = $1 and type = $2 or type = $3")
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


def setup(bot):
    bot.add_cog(Tasks(bot))
