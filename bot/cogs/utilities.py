import asyncio
import datetime
import random
import re

import discord
import typing

from parsedatetime import Calendar
from discord.ext import commands


class Utilities(commands.Cog, name='Utilities Commands'):
    """Useful Commands Found In The Bot"""
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(description='Supply type with list to list your reminders, delete to delete and reminder, or me/dm/here to set the destination of the reminder')
    async def remind(self, ctx, type: typing.Union[discord.TextChannel, str], duration=None, *, description=None):
        """Sets a reminder with an given time"""
        cursor = await self.bot.db.acquire()
        if type == 'list':
            reminders = await cursor.fetch("SELECT * FROM remind WHERE account = $1", ctx.author.id)
            embed = discord.Embed(title=f"{ctx.author} Reminders")
            if not reminders:
                embed.description = 'You Have No Reminders!'
            else:
                for remind in reminders:
                    chan = f"{self.bot.get_guild(remind[5])} — #{self.bot.get_channel(remind[4])}" if self.bot.get_channel(remind[4]) is not None else 'dm'
                    date = datetime.datetime.utcfromtimestamp(remind[2]).strftime('%a %b %d %Y %I:%M:%S %p UTC')
                    embed.add_field(name=f"Reminder [`{remind[1]}`]", value=f"```Time: {date}\nWhere: {chan}\nReason: {remind[3]}```", inline=False)
            await ctx.send(embed=embed)

        elif type == 'delete':
            await cursor.execute('DELETE FROM remind WHERE account = $1 and message = $2', ctx.author.id, duration)
            await ctx.send(f"Reminder Deleted Successfully!")
        else:
            if type == 'dm' or type == 'here' or isinstance(type, discord.TextChannel):
                user = ctx.author if type == 'dm' else ctx.channel if type == 'here' else type

                def date_convert_seconds(s):
                    current, result = Calendar().parse(s)
                    t = datetime.datetime(*current[:6])
                    futureDate = int((t-datetime.datetime.now()).total_seconds())
                    return futureDate+1, result

                def display_time(duration):
                    intervals = (('years', 31556952), ('months', 2592000), ('weeks', 604800), ('days', 86400), ('hours', 3600), ('minutes', 60), ('seconds', 1))

                    result = []

                    for name, count in intervals:
                        value = duration // count
                        if value:
                            duration -= value * count
                            result.append(f'{round(value)} {name}')

                    return ' '.join(result)

                time = date_convert_seconds(duration)
                if time[1] < 1:
                    await ctx.send("I do not recognise that time!")
                else:
                    time = time[0]
                    delta = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
                    stamp = delta.timestamp()
                    rand = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
                    remind_id = random.choices(rand, k=6)
                    escaped = discord.utils.escape_mentions(description)
                    await cursor.execute("INSERT INTO remind(guild, message, date, win, type, account) VALUES($1, $2, $3, $4, $5, $6)", ctx.guild.id, ''.join(remind_id), stamp, description, user.id, ctx.author.id)
                    await ctx.send(f"Reminding you in {display_time(time)} about: {escaped}")
                    await asyncio.sleep(time)
                    reminders = await cursor.fetchrow("SELECT * FROM remind WHERE account = $1 and message = $2", ctx.author.id, ''.join(remind_id))
                    if reminders is not None:
                        await user.send(f"{ctx.author.mention} {display_time(time)} ago you asked me to remind you about: {escaped}")
                        await cursor.execute("DELETE FROM remind WHERE account = $1 and message = $2", ctx.author.id, ''.join(remind_id))
            else:
                await ctx.send('Argument 1 should be dm, here or a channel')
            await self.bot.db.release(cursor)

    @commands.command(aliases=["makevote"])
    @commands.has_permissions(manage_messages=True)
    async def createpoll(self, ctx, multiple: bool, topic, duration, *questions):
        """Allows you to create a poll"""
        cursor = await self.bot.db.acquire()
        await ctx.message.delete()
        if len(questions) > 20:
            await ctx.send("You can only have a maximum of 20 questions!")
        else:
            def convert_to_seconds(s):
                current, result = Calendar().parse(s)
                t = datetime.datetime(*current[:6])
                futureDate = int((t - datetime.datetime.now()).total_seconds())
                return futureDate + 1, result

            time = convert_to_seconds(duration)
            if time[1] < 1:
                await ctx.send("I do not recognise that time!")
            else:
                time = time[0]
                delta = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
                ends = datetime.datetime.strftime(delta, '%a %b %d %Y %I:%M:%S %p UTC')
                type = "Multiple Options" if multiple is True else "Single Option"
                embed = discord.Embed(title=topic)
                embed.set_footer(text=f"Ends At {ends} - {type}")
                indicators = self.bot.emoji[1648:1668][::-1]
                for item, feilds in enumerate(questions):
                    embed.add_field(name=indicators[item], value=feilds)
                sent = await ctx.send(embed=embed)
                for button in range(len(questions)):
                    await sent.add_reaction(indicators[button])
                voting = sent.id + sent.channel.id
                await cursor.execute("INSERT INTO vote(guild, message, win, date, type) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, voting, multiple, time, "poll")
                await asyncio.sleep(time)
                execute = await cursor.fetchval("SELECT message FROM vote WHERE guild = $1 and message = $2 and win = $3 and type = $4", ctx.guild.id, voting, multiple, "poll")
                if execute is not None:
                    sent = await ctx.channel.fetch_message(sent.id)
                    data = sent.embeds[0]
                    name = [value.name for value in data.fields]
                    questions = [value.value for value in data.fields]
                    votes = sum([reaction.count - 1 for reaction in sent.reactions if reaction.emoji in name])
                    embed = discord.Embed(title="Poll Results", description=topic)
                    result = 0
                    for reaction in sent.reactions:
                        if reaction.emoji in name:
                            embed.add_field(name=questions[result], value=f"{reaction.count - 1} - {round((reaction.count - 1) * 100 / votes, 2) if votes != 0 else 0.0}%")
                            result += 1
                    await sent.edit(embed=embed)
                    await sent.clear_reactions()
                await cursor.execute("DELETE FROM vote WHERE guild = $1 and message = $2 and win = $3 and type = $4", ctx.guild.id, voting, multiple, "poll")
                await self.bot.db.release(cursor)

    @commands.command(aliases=["endvote"])
    @commands.has_permissions(manage_messages=True)
    async def endpoll(self, ctx, message: int):
        """Allows you to end a running poll"""
        cursor = await self.bot.db.acquire()
        await ctx.message.delete()
        sent = await ctx.channel.fetch_message(message)
        voting = sent.id + sent.channel.id
        execute = await cursor.fetchval("SELECT message FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, voting, "poll")
        if execute is not None:
            data = sent.embeds[0]
            title = data.title
            name = [value.name for value in data.fields]
            questions = [value.value for value in data.fields]
            votes = sum([reaction.count - 1 for reaction in sent.reactions if reaction.emoji in name])
            embed = discord.Embed(title="Poll Results", description=title)
            result = 0
            for reaction in sent.reactions:
                if reaction.emoji in name:
                    embed.add_field(name=questions[result], value=f"{reaction.count - 1} - {round((reaction.count - 1) * 100 / votes, 2) if votes != 0 else 0}%")
                    result += 1
            await sent.edit(embed=embed)
            await sent.clear_reactions()
            await cursor.execute("DELETE FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, voting, "poll")
        else:
            await ctx.send("This Poll Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

    @commands.command(aliases=["makegiveaway", "giveaway"])
    @commands.has_permissions(manage_messages=True)
    async def creategiveaway(self, ctx, name: str, winners: int, duration, requirement=None):
        """Allows you to create and host your own giveaway"""
        cursor = await self.bot.db.acquire()

        def convert_to_seconds(s):
            current, result = Calendar().parse(s)
            t = datetime.datetime(*current[:6])
            futureDate = int((t - datetime.datetime.now()).total_seconds())
            return futureDate + 1, result

        time = convert_to_seconds(duration)
        if time[1] < 1:
            await ctx.send("I do not recognise that time!")
        else:
            time = time[0]
            now = datetime.datetime.utcnow()
            delta = now + datetime.timedelta(seconds=time)
            ends = datetime.datetime.strftime(delta, '%a %b %d %Y %I:%M:%S %p UTC')
            embed = discord.Embed(title=name, description=f"**React With 🎉 To Enter** \n Host: {ctx.author.mention} \nRequirement: {requirement} \n Winners: {winners}")
            embed.set_footer(text=f"Ends At: {ends}")
            sent = await ctx.send(embed=embed)
            await sent.add_reaction('🎉')
            await cursor.execute("INSERT INTO vote(guild, message, date, win, type) VALUES($1, $2, $3, $4, $5)", ctx.guild.id, sent.id, delta.timestamp(), winners, "giveaway")
            await asyncio.sleep(time)

            sent = await ctx.channel.fetch_message(sent.id)
            vote = sent.reactions
            for reaction in vote:
                if reaction.emoji == '🎉':
                    users = await reaction.users().flatten()
                    winner = random.choices([winner.mention for winner in users if not winner.bot], k=winners)
                    winner = "\n".join(winner)
                    embed = discord.Embed(title=name, description=f"**Giveaway Ended** \n Host: {ctx.author.mention} \nRequirement: {requirement} \n Winners: {winner}")
                    embed.set_footer(text=f"Ended At: {ends}")
                    await cursor.execute("UPDATE vote SET type = $1 WHERE guild = $2 and message = $3 and type = $4", "giveaway end", ctx.guild.id, sent.id, "giveaway")
                    await sent.edit(embed=embed)
                    break

            await self.bot.db.release(cursor)

    @commands.command(aliases=["cancelgiveaway"])
    @commands.has_permissions(manage_messages=True)
    async def endgiveaway(self, ctx, message: discord.Message):
        """Allows you to end a running giveaway"""
        cursor = await self.bot.db.acquire()
        sent = await ctx.channel.fetch_message(message.id)
        execute = await cursor.fetchrow("SELECT date, win FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, sent.id, "giveaway")
        if execute is not None:
            vote = sent.reactions
            for reaction in vote:
                if reaction.emoji == '🎉':
                    data = sent.embeds[0]
                    stamp = datetime.datetime.fromtimestamp(execute[0])
                    time = datetime.datetime.utcnow().timestamp()
                    if datetime.datetime.utcnow() < stamp:
                        now = datetime.datetime.utcnow()
                        ends = datetime.datetime.strftime(now, '%a %b %d %Y %I:%M:%S %p UTC')
                        users = await reaction.users().flatten()
                        winner = random.choices([winner.mention for winner in users if not winner.bot], k=execute[1])
                        winner = "\n".join(winner)
                        embed = discord.Embed(title=data.title, description=f"**Giveaway Ended** \nHost: {re.search(r'<@(!?)([0-9]*)>', data.description)[0]}\nWinners:{winners}")
                        embed.set_footer(text=f"Ended At: {ends}")
                        await sent.edit(embed=embed)
                        await cursor.execute("UPDATE vote SET date = $1, type = $2 WHERE guild = $3 and message = $4 and type = $5", time, "giveaway end", ctx.guild.id, sent.id, "giveaway")
                        await ctx.send("Ended Giveaway", delete_after=2.8)
                        break
                    else:
                        await ctx.send("That Giveaway Has Already Ended!")
        else:
            await ctx.send("This Giveaway Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def rerollgiveaway(self, ctx, message: int):
        """Allows you to reroll the winners selected for the giveaway"""
        cursor = await self.bot.db.acquire()
        sent = await ctx.channel.fetch_message(message)
        execute = await cursor.fetchval("SELECT win FROM vote WHERE guild = $1 and message = $2 and type = $3", ctx.guild.id, sent.id, "giveaway end")
        if execute is not None:
            vote = sent.reactions
            for reaction in vote:
                if reaction.emoji == '🎉':
                    data = sent.embeds[0]
                    users = await reaction.users().flatten()
                    winner = random.choices([winner.mention for winner in users if not winner.bot], k=execute)
                    winners = "\n".join(winner)
                    embed = discord.Embed(name=data.title, description=f"**Giveaway Ended** \nHost: {re.search(r'<@(!?)([0-9]*)>', data.description)[0]}\nWinners:{winners}")
                    embed.set_footer(text=f"Ended At: {data.footer.text}")
                    await sent.edit(embed=embed)
                    await ctx.send("Giveaway rerolled", delete_after=2.8)
                    break
        else:
            await ctx.send("This Giveaway Does Not Exist Or In The Current Channel")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def updaterank(self, ctx, member: discord.Member, rank: int):
        """Updates someones rank for the leveling system"""
        cursor = await self.bot.db.acquire()
        guild = ctx.guild.id
        if rank < 0:
            await ctx.send("Integer Cannot Be Less Than 0!")
        elif member is not None:
            mem = member.id
            check = await cursor.fetchval("SELECT guild_id FROM levels WHERE guild_id = $1 and user_id = $2", ctx.guild.id, mem)
            if check is not None:
                await cursor.execute("UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and user_id = $4", rank, 0, guild, mem)
                await ctx.send(f"All levels updated successfully for {member.name}!")
            else:
                await cursor.execute("INSERT INTO levels(lvl, exp, guild_id, user_id) VALUES(?, ? ,?, ?)", rank, 0, guild, mem)
                await ctx.send(f"All levles updated successfully for {member.name}!")
        await self.bot.db.release(cursor)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def say(self, ctx, channel: discord.TextChannel, *, message):
        """Sends a message to an defined channel, as though it was sent by the bot"""
        channel = ctx.channel if not channel else channel
        escaped = discord.utils.escape_mentions(message)
        await ctx.message.delete()
        await channel.send(escaped)


def setup(bot):
    bot.add_cog(Utilities(bot))
