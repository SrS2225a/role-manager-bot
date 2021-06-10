import discord
from discord.ext import commands, menus
import tabulate
from tqdm import tqdm


import matplotlib
import matplotlib.pyplot as plt
import datetime

import io

# help commands
class Leaderboard(commands.Cog, name='Leaderboards & Counters'):
    """[These Commands Lets You View Dionysus's Various Leaderboards And Counters](https://github.com/SrS2225a/role-manager-bot/wiki/Leaderboards-&-Counters)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def members(self, ctx):
        """Displays Joins and Leaves over a 1 month period"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        month = [0, 0]
        week = [0, 0]
        day = [0, 0]

        plt.style.use('dark_background')
        matplotlib.rcParams['figure.figsize'] = (10, 5)

        fig, ax = plt.subplots()
    
        plt.grid()
        ax.xaxis.set_major_locator(plt.MaxNLocator(20))
        ax.tick_params(axis='x', labelrotation=45)

        members = await cursor.fetch("SELECT member, leave, day FROM member WHERE guild = $1 ORDER BY day ASC", guild.id)

        if members:
            max = members[-1][2]
            x1 = []
            y1 = []
            x2 = []
            y2 = []
            for member in members:
                month[0] += member[0]
                month[1] += member[1]

                if max == member[2]:
                    day[0] += member[0]
                    day[1] += member[1]
                if max-datetime.timedelta(days=7) <= member[2]:
                    week[0] += member[0]
                    week[1] += member[1]

                x1.append(member[2].strftime('%d %m'))
                y1.append(member[0])

                x2.append(member[2].strftime('%d %m'))
                y2.append(member[1])

            embed = discord.Embed(title=f"{ctx.guild}'s Member Overview")
            embed.add_field(name="Total Members", value=f"`{guild.member_count}`")
            embed.add_field(name="Member Retention", value=f"`{round((month[1] - day[0]) / month[0] * 100, 2)}%`")
            embed.add_field(name="Net Change", value=f"`{round(month[0] / (month[0] + month[1]) * 100, 2)}%`")

            plt.plot(x1, y1, marker="o", ls="", ms=3)
            plt.plot(x2, y2, marker="o", ls="", ms=3)
            plt.plot(x1, y1, label="Joins", color='#21BBFF')
            plt.plot(x2, y2, label="Leaves", color='#4e42ff')
            if y1 < y2:
                plt.fill_between(x1, y2, y1, color='#4e42ff', alpha=0.3)
                plt.fill_between(x2, y1, color='#21BBFF', alpha=0.3)
            else:
                plt.fill_between(x1, y1, y2, color='#21BBFF', alpha=0.3)
                plt.fill_between(x2, y2, color='#4e42ff', alpha=0.3)
            plt.legend()
            embed.add_field(name="Last 24 Hours", value=f'Joins: `{day[0]}`\nLeaves: `{day[1]}`')
            embed.add_field(name="Last 7 Days", value=f'Joins: `{week[0]}`\nLeaves: `{week[1]}`')
            embed.add_field(name="Last 30 Days", value=f'Joins: `{month[0]}`\nLeaves: `{month[1]}`')

            data_stream = io.BytesIO()
            plt.savefig(data_stream, format='png', bbox_inches="tight", transparent=True)
            data_stream.seek(0)
            plt.close()

            graph = discord.File(data_stream, filename='graph.png')
            embed.set_image(url='attachment://graph.png')
                    
        if members:
            await ctx.send(embed=embed, file=graph)
        else:
            await ctx.send("Data not popluated yet!")

        await self.bot.db.release(cursor)

    @members.command()
    async def joins(self, ctx):
        """Displays Joins over a 1 month peroid"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        month = [0, 0]
        week = [0, 0]
        day = [0, 0]

        plt.style.use('dark_background')
        matplotlib.rcParams['figure.figsize'] = (10, 5)

        fig, ax = plt.subplots()
    
        plt.grid()
        ax.xaxis.set_major_locator(plt.MaxNLocator(20))
        ax.tick_params(axis='x', labelrotation=45)

        members = await cursor.fetch("SELECT member, leave, day FROM member WHERE guild = $1 ORDER BY day ASC", guild.id)

        if members:
            max = members[-1][2]
            x1 = []
            y1 = []
            for member in members:
                month[0] += member[0]
                month[1] += member[1]

                if max == member[2]:
                    day[0] += member[0]
                    day[1] += member[1]
                if max-datetime.timedelta(days=7) <= member[2]:
                    week[0] += member[0]
                    week[1] += member[1]

                x1.append(member[2].strftime('%d %m'))
                y1.append(member[0])

            embed = discord.Embed(title=f"{ctx.guild}'s Member Overview")
            embed.add_field(name="Total Members", value=f"`{guild.member_count}`")
            embed.add_field(name="Member Retention", value=f"`{round((month[1] - day[0]) / month[0] * 100, 2)}%`")
            embed.add_field(name="Net Change", value=f"`{round(month[0] / (month[0] + month[1]) * 100, 2)}%`")

            plt.plot(x1, y1, label="Joins", color='#21BBFF')
            plt.plot(x1, y1, marker="o", ls="", ms=3)
            plt.fill_between(x1, y1, color='#21BBFF', alpha=0.3)
            embed.add_field(name="Last 24 Hours", value=f'Joins: `{day[0]}`')
            embed.add_field(name="Last 7 Days", value=f'Joins: `{week[0]}`')
            embed.add_field(name="Last 30 Days", value=f'Joins: `{month[0]}`')
            
            data_stream = io.BytesIO()
            plt.savefig(data_stream, format='png', bbox_inches="tight", transparent=True)
            data_stream.seek(0)
            plt.close()

            graph = discord.File(data_stream, filename='graph.png')
            embed.set_image(url='attachment://graph.png')

        if members:
            await ctx.send(embed=embed, file=graph)
        else:
            await ctx.send("Data not popluated yet!")
            
        await self.bot.db.release(cursor)

    @members.command()
    async def leaves(self, ctx):
        """Displays Leaves over a 1 month peroid"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        month = [0, 0]
        week = [0, 0]
        day = [0, 0]

        plt.style.use('dark_background')
        matplotlib.rcParams['figure.figsize'] = (10, 5)

        fig, ax = plt.subplots()
    
        plt.grid()
        ax.xaxis.set_major_locator(plt.MaxNLocator(20))
        ax.tick_params(axis='x', labelrotation=45)

        members = await cursor.fetch("SELECT member, leave, day FROM member WHERE guild = $1 ORDER BY day ASC", guild.id)

        if members:
            max = members[-1][2]
            x1 = []
            y1 = []

            for member in members:
                month[0] += member[0]
                month[1] += member[1]

                if max == member[2]:
                    day[0] += member[0]
                    day[1] += member[1]
                if max-datetime.timedelta(days=7) <= member[2]:
                    week[0] += member[0]
                    week[1] += member[1]

                x1.append(member[2].strftime('%d %m'))
                y1.append(member[0])

            embed = discord.Embed(title=f"{ctx.guild}'s Member Overview")
            embed.add_field(name="Total Members", value=f"`{guild.member_count}`")
            embed.add_field(name="Member Retention", value=f"`{round((month[1] - day[0]) / month[0] * 100, 2)}%`")
            embed.add_field(name="Net Change", value=f"`{round(month[0] / (month[0] + month[1]) * 100, 2)}%`")

            plt.plot(x1, y1, marker="o", ls="", ms=3)
            plt.plot(x1, y1, color='#4e42ff')
            plt.fill_between(x1, y1, color='#4e42ff', alpha=0.3)
            embed.add_field(name="Last 24 Hours", value=f'Leaves: `{day[1]}`')
            embed.add_field(name="Last 7 Days", value=f'Leaves: `{week[1]}`')
            embed.add_field(name="Last 30 Days", value=f'Leaves: `{month[1]}`')

            data_stream = io.BytesIO()
            plt.savefig(data_stream, format='png', bbox_inches="tight", transparent=True)
            data_stream.seek(0)
            plt.close()

            graph = discord.File(data_stream, filename='graph.png')
            embed.set_image(url='attachment://graph.png')

        if members:
            await ctx.send(embed=embed, file=graph)
        else:
            await ctx.send("Data not popluated yet!")

        await self.bot.db.release(cursor)


    @commands.group(aliases=['top', 'lb'], hidden=True, invoke_without_command=True, description='Supply type with rankings/invites/partnerships to view that particular leaderboard')
    async def leaderboard(self, ctx):
        """Shows the leaderboard"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @leaderboard.command()
    async def ranks(self, ctx):
        """Shows top leveling rankings"""
        cursor = await self.bot.db.acquire()
        # shows the leaderboard for leveling
        tabulate.MIN_PADDING = 0
        # checks if the sever has leveling enabled for Dionysus
        diff1 = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.author.guild.id, 'difficulty')
        if diff1 is not None:
            # gets our leaderboard results
            result = await cursor.fetch("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, exp DESC", ctx.guild.id)
            table = []
            for row in result:
                user = self.bot.get_user(id=int(row[0]))
                if user is not None:
                    table.append([row[1], row[2], user.name + "#" + user.discriminator])

            # puts results in a navigatable page interface and formats our data into a text table
            class Source(menus.ListPageSource):
                def __init__(self, data):
                    super().__init__(data, per_page=20)

                async def format_page(self, menu, entry):
                    offset = menu.current_page * self.per_page
                    embed = discord.Embed(title=f"Dionysus Rankings (Showing Entries {1 + offset} - {len(entry) + offset})",
                                            description=f"```{tabulate.tabulate(entry, headers=['XP', 'LV', 'USER'], tablefmt='presto')}```")
                    embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                    return embed

            pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
            await pages.start(ctx)
        elif diff1 is None:
            await ctx.send("Rankings is currently disabled for this server!")
        await self.bot.db.release(cursor)

    @leaderboard.command()
    async def invites(self, ctx):
        """Shows top member invites"""
        cursor = await self.bot.db.acquire()
        # gets our leaderboard results
        tabulate.MIN_PADDING = 0
        result = await cursor.fetch(f"SELECT member, SUM(amount), SUM(amount2), SUM(amount3) FROM invite WHERE guild = $1 GROUP BY member ORDER BY SUM(amount) DESC, SUM(amount2) DESC, SUM(amount3) DESC", ctx.guild.id)
        table = []
        for row in result:
            user = self.bot.get_user(id=int(row[0]))
            if user is not None:
                table.append([row[1], row[2], row[3], user.name + "#" + user.discriminator])

        # puts results in a navigatable page interface and formats our data into a text table
        class Source(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=20)

            async def format_page(self, menu, entry):
                offset = menu.current_page * self.per_page
                embed = discord.Embed(
                    title=f"Dionysus Invites (Showing Entries {1 + offset} - {len(entry) + offset})",
                    description=f"```{tabulate.tabulate(entry, headers=['JOINS', 'LEAVES', 'FAKES', 'USER'], tablefmt='presto')}```")
                embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                return embed

        pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
        await pages.start(ctx)
    
    @leaderboard.command()
    async def partners(self, ctx):
        """Shows top completed partnerships"""
        # shows the leaderboard for invites
        cursor = await self.bot.db.acquire()      
        # checks if the sever has partnerships enabled for Dionysus
        tabulate.MIN_PADDING = 0
        diff1 = await cursor.fetchval(f"SELECT system FROM leveling WHERE guild = $1 and system = $2", ctx.author.guild.id, 'partners')
        if diff1 is not None:
            result = await cursor.fetch("SELECT member, number FROM partner WHERE guild = $1 ORDER BY number DESC", ctx.guild.id)
            table = []
            for row in result:
                user = self.bot.get_user(id=int(row[0]))
                if user is not None:
                    table.append([row[1], user.name + "#" + user.discriminator])

            # puts results in a navigatable page interface and formats our data into a text table
            class Source(menus.ListPageSource):
                def __init__(self, data):
                    super().__init__(data, per_page=20)

                async def format_page(self, menu, entry):
                    offset = menu.current_page * self.per_page
                    embed = discord.Embed(
                        title=f"Dionysus Partners (Showing Entries {1 + offset} - {len(entry) + offset})",
                        description=f"```{tabulate.tabulate(entry, headers=['PARTNERS', 'USER'], tablefmt='presto')}```")
                    embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                    return embed

            pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
            await pages.start(ctx)
        elif diff1 is None:
            await ctx.send("Partnerships is currently disabled for this server!")
        await self.bot.db.release(cursor)
        

    @commands.command(aliases=['level'])
    async def rank(self, ctx, *, member: discord.User = None):
        """Shows your ranking status or someone else's"""
        cursor = await self.bot.db.acquire()
        member = ctx.author if not member else member
        # checks if the sever has leveling enabled for Dionysus
        difficulty = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'difficulty')
        if difficulty is not None:
            # gets our rank results from a user or ours
            result = await cursor.fetchrow("SELECT exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2", ctx.guild.id, member.id)
            ranking = await cursor.fetch("SELECT user_id FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, exp DESC", ctx.guild.id)

            # detects if we have been ranked yet
            if result is None:
                embed = discord.Embed(
                    title='Undefined Rank',
                    description='The user is not yet ranked.',
                    colour=discord.Colour.red()
                )

                await ctx.send(embed=embed)
            else:
                # shows various information about our rank
                i = 0
                for row in ranking:
                    i += 1
                    if row[0] == member.id:
                        break
                xp_end = round(result[1] * difficulty + result[1] * difficulty)
                bar = tqdm(total=xp_end, ncols=20, miniters=1, ascii='□◧■', bar_format='{l_bar}{bar}')
                bar.update(result[0])

                embed = discord.Embed(
                    title=f'{member} Rank',
                    colour=discord.Colour.blue()
                )

                embed.add_field(name='XP', value=str(result[0]) + " / " + str(xp_end))
                embed.add_field(name='Level', value=str(result[1]))
                embed.add_field(name='Ranking', value=str(i))
                embed.add_field(name='Progress', value=str(bar))

                await ctx.send(embed=embed)

        else:
            await ctx.send("This leveling feature is currently disabled for this bot!")
        await self.bot.db.release(cursor)

    @commands.command(brief="invites @Vendron#2001")
    async def invites(self, ctx, *, member: discord.User = None):
        """Shows info about how many members you invited, or someone else"""
        cursor = await self.bot.db.acquire()
        # shows various information about how many members we invited, or someone elses
        guild = ctx.guild
        member = ctx.author if not member else member
        full = await cursor.fetchrow("SELECT SUM(amount), SUM(amount2), SUM(amount3) FROM invite WHERE guild = $1 and member = $2", guild.id, member.id)
        full = full if full[0] is not None else [0, 0, 0]
        leave = full[1] + full[2]
        server = round((full[0] - leave) * 100 / len(guild.members), 2) if full[0] != 0 else 0.0
        deficit = round(leave * 100 / full[0], 2) if full[0] != 0 else 0.0
        embed = discord.Embed(title=f"{member} Invites", description=f"{full[0]} joins, {full[1]} leaves, {full[2]} fakes \nYou currently have a deficit of {deficit}% and invited {server}% of server", color=member.color)
        await ctx.send(embed=embed)
        await self.bot.db.release(cursor)

    @commands.command(aliases=['invitecodes'])
    async def inviteinfo(self, ctx, *, member: discord.User = None):
        """Shows info about your invites, or someone elses"""
        cursor = await self.bot.db.acquire()
        # shows various information about how many members we invited, or someone elses
        guild = ctx.guild
        member = ctx.author if not member else member
        full = await cursor.fetch("SELECT amount, amount2, amount3, invite FROM invite WHERE guild = $1 and member = $2", guild.id, member.id)
        embed = discord.Embed(title=f"Invite Info For {member}", color=member.color)
        for invite in full:
            embed.add_field(name=invite[3], value=f"{invite[0]} joins, {invite[1]} leaves, {invite[2]} fakes", inline=False)

        await ctx.send(embed=embed)
        await self.bot.db.release(cursor)

    @commands.command()
    async def partners(self, ctx, member: discord.Member = None):
        """Shows info about how many partners you completed or someone elses"""
        cursor = await self.bot.db.acquire()
        diff1 = await cursor.fetchval(f"SELECT system FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id, 'partners')
        if diff1 is None:
            await ctx.send("Partnerships is currently disabled for this server!")
        else:
            member = ctx.author if not member else member
            result = await cursor.fetchval("SELECT number FROM partner WHERE guild = $1 and member = $2", ctx.guild.id, member.id)
            partner = result if result is not None else 0
            embed = discord.Embed(title=f"{member} Partners", description=f"{partner} Completed")
            await ctx.send(embed=embed)
            await self.bot.db.release(cursor)


def setup(bot):
    bot.add_cog(Leaderboard(bot))