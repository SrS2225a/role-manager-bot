import discord
from discord.ext import commands, menus
import tabulate
from tqdm import tqdm

import matplotlib
import matplotlib.pyplot as plt
import datetime
import io


class Leaderboard(commands.Cog, name='Leaderboards & Counters'):
    """[These Commands Lets You View Dionysus's Various Leaderboards And Counters](
    https://github.com/SrS2225a/role-manager-bot/wiki/Leaderboards-&-Counters) """

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, hidden=True)
    async def graph(self, ctx):
        """Allows you to view graphs"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @graph.group(aliases=['mem'])
    async def members(self, ctx):
        """Displays Joins and Leaves over a 1 month period"""
        global embed, graph
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
        date = await cursor.fetchval("SELECT lookback FROM settings WHERE guild = $1", ctx.guild.id)
        members = await cursor.fetch("SELECT joins, leaves, day FROM member WHERE guild = $1 and day > $2 ORDER BY "
                                     "day ASC", guild.id, (datetime.date.today() - datetime.timedelta(days=date or 30)))

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
                if max - datetime.timedelta(days=7) <= member[2]:
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
        global embed, graph
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

        date = await cursor.fetchval("SELECT lookback FROM settings WHERE guild = $1", ctx.guild.id)
        members = await cursor.fetch("SELECT joins, leaves, day FROM member WHERE guild = $1 and day > $2 ORDER BY "
                                     "day ASC", guild.id, (datetime.date.today() - datetime.timedelta(days=date or 30)))

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
                if max - datetime.timedelta(days=7) <= member[2]:
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
        global embed, graph
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

        date = await cursor.fetchval("SELECT lookback FROM settings WHERE guild = $1", ctx.guild.id)
        members = await cursor.fetch("SELECT joins, leaves, day FROM member WHERE guild = $1 and day > $2 ORDER BY "
                                     "day ASC", guild.id, (datetime.date.today() - datetime.timedelta(days=date or 30)))

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
                if max - datetime.timedelta(days=7) <= member[2]:
                    week[0] += member[0]
                    week[1] += member[1]

                x1.append(member[2].strftime('%d %m'))
                y1.append(member[1])

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

    @graph.command(name="messages", aliases=["msgs"])
    async def graph_messages(self, ctx):
        """Displays total messages sent over a 1 month period"""
        global embed, graph
        cursor = await self.bot.db.acquire()
        guild = ctx.guild
        userDay = 0
        userWeek = 0
        userMonth = 0
        plt.style.use('dark_background')
        matplotlib.rcParams['figure.figsize'] = (10, 5)

        fig, ax = plt.subplots()

        plt.grid()
        ax.xaxis.set_major_locator(plt.MaxNLocator(20))
        ax.tick_params(axis='x', labelrotation=45)

        date = await cursor.fetchval("SELECT lookback FROM settings WHERE guild = $1", ctx.guild.id)
        members = await cursor.fetch("SELECT day, SUM(messages) FROM message WHERE guild = $1 and day > $2 GROUP BY "
                                     "day ORDER BY day ASC", guild.id, (datetime.date.today() - datetime.timedelta(
            days=date or 30)))

        if members:
            max = members[-1][0]
            x1 = []
            y1 = []
            for messages in members:
                userMonth += messages[1]

                if max == messages[0]:
                    userDay += messages[1]
                if max - datetime.timedelta(days=7) <= messages[0]:
                    userWeek += messages[1]

                x1.append(messages[0].strftime('%d %m'))
                y1.append(messages[1])

            topUser = ""
            for messages in await cursor.fetch("SELECT member, SUM(messages) FROM message WHERE guild = $1 and day > "
                                               "$2 GROUP BY member ORDER BY SUM(messages) DESC LIMIT 5", guild.id,
                                               (datetime.date.today() - datetime.timedelta(days=date or 30))):
                user = self.bot.get_user(id=int(messages[0]))
                if user:
                    topUser += f"{user.mention} - `{messages[1]}`\n"

            topChannel = ""
            for messages in await cursor.fetch("SELECT channel, SUM(messages) FROM message WHERE guild = $1 and day > "
                                               "$2 GROUP BY channel ORDER BY SUM(messages) DESC LIMIT 5", guild.id,
                                               (datetime.date.today() - datetime.timedelta(days=date or 30))):
                channel = guild.get_channel(messages[0])
                if channel:
                    topChannel += f"{channel.mention} - `{messages[1]}`\n"

            embed = discord.Embed(title=f"{ctx.guild}'s Message Overview")
            embed.add_field(name="Last 24 Hours", value=f"Messages: `{userDay}`")
            embed.add_field(name="Last 7 Days", value=f"Messages: `{userWeek}`")
            embed.add_field(name="Last 30 Days", value=f"Messages: `{userMonth}`")
            embed.add_field(name="Top 5 Channels", value=topChannel)
            embed.add_field(name="Top 5 Users", value=topUser)

            plt.plot(x1, y1, marker="o", ls="", ms=3)
            plt.plot(x1, y1, color='#21BBFF')
            plt.fill_between(x1, y1, color='#21BBFF', alpha=0.3)

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

    @commands.group(aliases=['top', 'lb'], hidden=True, invoke_without_command=True)
    async def leaderboard(self, ctx):
        """Shows the leaderboard"""
        if not ctx.invoked_subcommand:
            await ctx.send(f"Invalid sub-command! Please see `{ctx.prefix}help {ctx.command}`")

    @leaderboard.command(name='ranks')
    async def lb_ranks(self, ctx):
        """Shows top leveling rankings"""
        cursor = await self.bot.db.acquire()
        # shows the leaderboard for leveling
        tabulate.MIN_PADDING = 0
        # checks if the sever has leveling enabled for Dionysus
        diff1 = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2",
                                      ctx.author.guild.id, 'difficulty')
        if diff1 is not None:
            # gets our leaderboard results
            result = await cursor.fetch("SELECT user_id, exp, lvl FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, "
                                        "exp DESC", ctx.guild.id)
            table = []
            total = 0
            for row in result:
                user = self.bot.get_user(id=int(row[0]))
                if user is not None:
                    table.append([row[1], row[2], user.name + "#" + user.discriminator])
                    if user == ctx.member:
                        total += len(table)

            # puts results in a navigable page interface and formats our data into a text table
            class Source(menus.ListPageSource):
                def __init__(self, data):
                    super().__init__(data, per_page=20)

                async def format_page(self, menu, entry):
                    offset = menu.current_page * self.per_page
                    em = discord.Embed(
                        title=f"Dionysus Rankings (Showing Entries {1 + offset} - {len(entry) + offset})",
                        description=f"```{tabulate.tabulate(entry, headers=['XP', 'LV', 'USER'], tablefmt='presto')}```")
                    em.set_footer(
                        text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                    return em

            pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
            await pages.start(ctx)
        elif diff1 is None:
            await ctx.send("Rankings is currently disabled for this server!")
        await self.bot.db.release(cursor)

    @leaderboard.command(name='messages', aliases=["msgs"])
    async def lb_messages(self, ctx):
        """Shows top messages"""
        cursor = await self.bot.db.acquire()
        # gets our leaderboard results
        tabulate.MIN_PADDING = 0
        result = await cursor.fetch(
            f"SELECT member, SUM(messages) FROM message WHERE guild = $1 GROUP BY member ORDER BY SUM(messages) DESC",
            ctx.guild.id)
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
                    title=f"Dionysus Messages (Showing Entries {1 + offset} - {len(entry) + offset})",
                    description=f"```{tabulate.tabulate(entry, headers=['MESSSAGES', 'USER'], tablefmt='presto')}```")
                embed.set_footer(
                    text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                return embed

        pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
        await pages.start(ctx)

    @leaderboard.command(name='invites')
    async def lb_invites(self, ctx):
        """Shows top member invites"""
        cursor = await self.bot.db.acquire()
        # gets our leaderboard results
        tabulate.MIN_PADDING = 0
        result = await cursor.fetch(
            f"SELECT member, SUM(amount), SUM(amount2), SUM(amount3) FROM invite WHERE guild = $1 GROUP BY member "
            f"ORDER BY SUM(amount) DESC, SUM(amount2) DESC, SUM(amount3) DESC", ctx.guild.id)
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
                embed.set_footer(
                    text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                return embed

        pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
        await pages.start(ctx)

    @leaderboard.command(name='partners')
    async def lb_partners(self, ctx):
        """Shows top completed partnerships"""
        # shows the leaderboard for invites
        cursor = await self.bot.db.acquire()
        # checks if the sever has partnerships enabled for Dionysus
        tabulate.MIN_PADDING = 0
        diff1 = await cursor.fetchval(f"SELECT system FROM leveling WHERE guild = $1 and system = $2",
                                      ctx.author.guild.id, 'partners')
        if diff1 is not None:
            result = await cursor.fetch("SELECT member, number FROM partner WHERE guild = $1 ORDER BY number DESC",
                                        ctx.guild.id)
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
                    embed.set_footer(
                        text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total Entries: {len(table)}")
                    return embed

            pages = menus.MenuPages(source=Source(table), clear_reactions_after=True)
            await pages.start(ctx)
        elif diff1 is None:
            await ctx.send("The partnerships feature has not been setup yet by this server!")
        await self.bot.db.release(cursor)

    @commands.command(aliases=['level'], brief="rank @Vendron#2001")
    async def rank(self, ctx, *, member: discord.User = None):
        """Shows your ranking status or someone else's"""
        cursor = await self.bot.db.acquire()
        member = ctx.author or member
        # checks if the sever has leveling enabled for Dionysus
        difficulty = await cursor.fetchval("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2",
                                           ctx.guild.id, 'difficulty')
        if difficulty is not None:
            # gets our rank results from a user or ours
            result = await cursor.fetchrow("SELECT exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2",
                                           ctx.guild.id, member.id)
            ranking = await cursor.fetch("SELECT user_id FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, exp DESC",
                                         ctx.guild.id)

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

                xp_end = int(100 * result[1] * difficulty / 3)
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
            await ctx.send("The leveling feature has not been setup yet by this server!")
        await self.bot.db.release(cursor)

    @commands.command(brief="invites @Vendron#2001")
    async def invites(self, ctx, *, member: discord.User = None):
        """Shows info about how many members you invited, or someone else"""
        cursor = await self.bot.db.acquire()
        # shows various information about how many members we invited, or someone elses
        guild = ctx.guild
        member = member or ctx.author
        full = await cursor.fetchrow(
            "SELECT SUM(amount), SUM(amount2), SUM(amount3) FROM invite WHERE guild = $1 and member = $2 GROUP BY "
            "member",
            guild.id, member.id)
        rank = await cursor.fetch(
            "SELECT member FROM invite WHERE guild = $1 GROUP BY member ORDER BY SUM(amount) DESC, SUM(amount2) DESC, "
            "SUM(amount3) DESC",
            ctx.guild.id)

        full = full if full is not None else [0, 0, 0]
        leave = full[1] + full[2]
        actual = full[0] - leave
        server = round((actual) * 100 / len(guild.members), 2) if full[0] != 0 else 0.0
        deficit = round(leave * 100 / full[0], 2) if full[0] != 0 else 0.0

        i = 0
        for row in rank:
            i += 1
            if row[0] == member.id:
                break

        embed = discord.Embed(title=f"{member} Invites",
                              description=f"**{full[0]}** joins, **{full[1]}** leaves, **{full[2]}** fakes "
                                          f"(**{actual}**). With A Rank Of **{i}** "
                                          f"\nYou currently have a deficit of **{deficit}**% and invited "
                                          f"**{server}**% of server",
                              color=member.color)
        await ctx.send(embed=embed)
        await self.bot.db.release(cursor)

    @commands.command(aliases=['invitecodes'], brief="invites @Vendron#2001")
    async def inviteinfo(self, ctx, *, member: discord.User = None):
        """Shows info about your invites, or someone elses"""
        cursor = await self.bot.db.acquire()
        # shows various information about how many members we invited, or someone elses
        guild = ctx.guild
        member = member or ctx.author
        full = await cursor.fetch(
            "SELECT amount, amount2, amount3, invite FROM invite WHERE guild = $1 and member = $2", guild.id, member.id)
        embed = discord.Embed(title=f"Invite Info For {member}", color=member.color)
        for invite in full:
            embed.add_field(name=invite[3],
                            value=f"**{invite[0]}** joins, **{invite[1]}** leaves, **{invite[2]}** fakes", inline=False)

        await ctx.send(embed=embed)
        await self.bot.db.release(cursor)

    @commands.command(aliases=['getinvite'])
    async def searchinvite(self, ctx, code):
        """Gets information about an invite code"""
        cursor = await self.bot.db.acquire()
        full = await cursor.fetchrow(
            "SELECT amount, amount2, amount3, member FROM invite WHERE guild = $1 and invite = $2", ctx.guild.id, code)
        if full is not None:
            leave = full[1] + full[2]
            actual = full[0] - leave
            embed = discord.Embed(title=f"Invite Code Information For {self.bot.get_user(full[3])} - {code}",
                                  description=f"**{full[0]}** joins, **{full[1]}** leaves, **{full[2]}** (**{actual}**)")
            await ctx.send(embed=embed)
        else:
            await ctx.send("I could not find that invite!")
        await self.bot.db.release(cursor)

    @commands.command(brief="partners @Vendron#2001")
    async def partners(self, ctx, member: discord.Member = None):
        """Shows info about how many partners you completed or someone elses"""
        cursor = await self.bot.db.acquire()
        diff1 = await cursor.fetchval(f"SELECT system FROM leveling WHERE guild = $1 and system = $2", ctx.guild.id,
                                      'partners')
        if diff1 is None:
            await ctx.send("Partnerships is currently disabled for this server!")
        else:
            member = member or ctx.author
            result = await cursor.fetchval("SELECT number FROM partner WHERE guild = $1 and member = $2", ctx.guild.id,
                                           member.id)
            rank = await cursor.fetch("SELECT member FROM partner WHERE guild = $1 ORDER BY number DESC", ctx.guild.id)
            result = result or 0

            i = 0
            for row in rank:
                i += 1
                if row[0] == member.id:
                    break

            embed = discord.Embed(title=f"{member} Partners",
                                  description=f"**{result}** Completed \nWith A Rank Of **{i}**")
            await ctx.send(embed=embed)
            await self.bot.db.release(cursor)

    @commands.command(aliases=["msgs"], brief="messages @Vendron#2001")
    async def messages(self, ctx, member: discord.Member = None):
        """Shows info about how many messages you sent or someone elses"""
        cursor = await self.bot.db.acquire()
        member = member or ctx.author
        # cursor.fetch("SELECT member, SUM(joins) FROM member WHERE guild = $1 and type = $2 and day > $3 GROUP BY
        # member ORDER BY SUM(joins) DESC LIMIT 5", guild.id, 'message', (datetime.date.today()-datetime.timedelta(
        # days=date or 30))):
        messages = await cursor.fetch(
            f"SELECT channel, SUM(messages) FROM message WHERE guild = $1 and member = $2 GROUP BY channel "
            f"ORDER BY SUM(messages) DESC", ctx.guild.id, member.id)
        rank = await cursor.fetch(
            "SELECT member FROM message WHERE guild = $1 GROUP BY member, messages ORDER BY messages DESC",
            ctx.guild.id)
        if messages:
            user1 = []
            i = 0
            for user in messages:
                channel = ctx.guild.get_channel(user[0])
                if channel:
                    user1.append(f"--> {channel.mention}: **{user[1]}** messages")

            for row in rank:
                i += 1
                if row[0] == member.id:
                    break

            newLine = '\n'  # put new line in a variable, otherwise python will complain
            embed = discord.Embed(title=f"Messages Sent By {member}",
                                  description=f"Total: **{sum([user[1] for user in messages])}**. With A Ranking of *"
                                              f"*{i}** \n\n{newLine.join(user1)}")
            await ctx.send(embed=embed)
            await self.bot.db.release(cursor)
        else:
            await ctx.send("User data not populated yet!")


def setup(bot):
    bot.add_cog(Leaderboard(bot))
