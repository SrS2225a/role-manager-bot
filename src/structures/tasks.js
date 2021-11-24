const {Util, MessageEmbed, Formatters} = require("discord.js");
const {pool} = require("../database");

class Reminder {
    // prevent more than one instance
    constructor(task) {
        this.task = task;
    }
    static getInstance() {
        if (!Reminder.instance) {
            Reminder.instance = new Reminder();
        }
        return Reminder.instance;
    }

    async get_active_reminders(db) {
        const timer = await db.query("SELECT * FROM remind WHERE date < (current_date + $1::interval) ORDER BY date LIMIT 1", ['48 days']);
        if (timer.rowCount > 0) {
            return timer.rows[0]
        }
        return false
    }

    async finish_reminder(db, timer) {
        if (!timer.repeat) {
            await db.query("DELETE FROM remind WHERE id = $1 and member = $2", [timer.id, timer.member])
        } else {
            const time = (timer.date + timer.assigned)
            await db.query("UPDATE remind SET date = $1, assigned = $2 WHERE id = $3 and member = $4", [timer.date + time, timer.assigned + time, timer.id, timer.member])
        }
        await db.release()
    }

    async call_reminder(client, timer, db) {
        try {
            const msg = `<@${timer.member}> <t:${Math.round(timer.assigned.valueOf() / 1000)}:R> you asked me to remind you about: **${Util.removeMentions(timer.message)}**`
            if (timer.member === timer.destination) {
                const user = client.users.cache.get(timer.member) || await client.users.fetch(timer.member)
                await user.send(msg)
            } else {
                const channel = client.channels.cache.get(timer.destination) || await client.channels.fetch(timer.destination)
                await channel.send(msg)
            }
            await this.finish_reminder(db, timer)
        } catch (e) {
            await this.dispatch_reminder(client)
            console.log(e)
        }
        await this.dispatch_reminder(client)
    }

    async dispatch_reminder(client) {
        const db = await pool.connect()
        const timer = await this.get_active_reminders(db)
        if (timer) {
            clearTimeout(client?.reminder_timer)
            const now = new Date()
            if (timer.date >= now) {
                client.reminder_timer = setTimeout(async () => await this.call_reminder(client, timer, db), timer.date.getTime() - now.getTime())
            } else {
                await this.call_reminder(client, timer, db)
            }

        }
    }
}
class Poll {
    constructor(task) {
        this.task = task;
    }

    async get_active_polls(db) {
        const poll = await db.query("SELECT * FROM vote WHERE date < (current_date + $1::interval) and type = $2 ORDER BY date LIMIT 1", ['48 days', 'poll']);
        if (poll.rowCount > 0) {
            return poll.rows[0]
        }
        return false
    }

    async finish_poll(db, poll) {
        await db.query("DELETE FROM vote WHERE guild = $1 and message = $2 and type = $3", [poll.guild, poll.message, 'poll'])
        await db.release()
    }

    async call_poll(client, poll, db) {
        try {
            const channel = client.channels.cache.get(poll.channel) || await client.channels.fetch(poll.channel)
            const msg = await channel.messages.fetch(poll.message)
            const reactions = msg.reactions.cache
            const indicators = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸", "🇹"]
            const embed_content = msg.embeds[0]
            const votes = reactions.reduce((acc, reaction) => {
                if (indicators.includes(reaction.emoji.name)) {
                    return acc + reaction.count - 1
                }
                return acc
            }, 0)
            const embed = new MessageEmbed()
                .setTitle("Poll Results")
                .setDescription(`${embed_content.title} \n\nEnded <t:${Math.round(poll.date / 1000)}:R>`)

            for (const reaction of reactions) {
                const react = reaction[1]
                if (indicators.includes(react.emoji.name)) {
                    const emoji = react.emoji.name
                    const count = react.count - 1
                    const percentage = Math.round((count / votes) * 100)
                    embed.addField(emoji, `${count} (${percentage}%)`, true)
                }
            }

            await msg.edit({embeds: [embed]})
            await this.finish_poll(db, poll)
        } catch (e) {
            await this.dispatch_poll(client)
            console.log(e)
        }
        await this.dispatch_poll(client)
    }

    async dispatch_poll(client) {
        const db = await pool.connect()
        const poll = await this.get_active_polls(db)
        await db.release()
        if (poll) {
            clearTimeout(client?.poll_timer)
            const now = new Date()
            if (poll.date >= now) {
                client.poll_timer = setTimeout(async () => await this.call_poll(client, poll, db), poll.date.getTime() - now.getTime())
            } else {
                await this.call_poll(client, poll, db)
            }

        }
    }
}

class Giveaway {
    constructor(task) {
        this.task = task;
    }

    async dispatch_giveaway(client) {
        const db = await pool.connect()
        const giveaway = await this.get_active_giveaways(db)
        await db.release()
        if (giveaway) {
            clearTimeout(client?.giveaway_timer)
            const now = new Date()
            if (giveaway.date >= now) {
                client.giveaway_timer =  setTimeout(async () => await this.call_giveaway(client, giveaway, db), giveaway.date.getTime() - now.getTime())
            } else {
                await this.call_giveaway(client, giveaway, db)
            }
        }
    }

    async get_active_giveaways(db) {
        const giveaway = await db.query("SELECT * FROM vote WHERE date < (current_date + $1::interval) and type = $2 ORDER BY date LIMIT 1", ['48 days', 'giveaway'])
        if (giveaway.rowCount > 0) {
            return giveaway.rows[0]
        }
        return false
    }

    async call_giveaway(client, giveaway, db) {
        try {
            const channel = client.channels.cache.get(giveaway.channel) || await client.channels.fetch(giveaway.channel)
            const msg = await channel.messages.fetch(giveaway.message)
            const embed_content = msg.embeds[0]
            const ends = new Date(giveaway.date)
            const reactions = await msg.reactions.cache.get('🎉').users.fetch()
            const winner = reactions.filter(x => x.id !== client.user.id).random(giveaway.win)
            const final_winners = (winner.length > 0 ? winner.map(x => Formatters.userMention(x.id)).join(', ') : "No Winners")
            const embed = new MessageEmbed()
                .setTitle(embed_content.title)
                .setDescription(`**Winners:** ${final_winners}\n**Ended:** <t:${Math.round(ends.valueOf() / 1000)}:R>`)
            await msg.edit({embeds: [embed]})
            await this.finish_giveaway(db, giveaway)
            const winner_msg = await channel.send(`Congratulations, ${final_winners}! You won the giveaway!`)
            await winner_msg.delete({timeout: 10000})
        } catch (e) {
            await this.dispatch_giveaway(client)
            console.log(e)
        }
        await this.dispatch_giveaway(client)
    }

    async finish_giveaway(db, giveaway) {
        await db.query("UPDATE vote SET type = $1 WHERE guild = $2 and message = $3 and type = $4", ['finished', giveaway.guild, giveaway.message, 'giveaway'])
        await db.release()
    }
}

class AutoRole {
    constructor(task) {
        this.task = task;
    }

 async wait_for_active_autoroles(db, client) {
     const timer = client.current_timer = await db.query("SELECT * FROM autorole WHERE date < (current_date + $1::interval) ORDER BY date LIMIT 1", ['48 days'])
     // export this.current_timer = timer
     if (timer.rowCount > 0) {
         return timer.rows[0]
     }
     return false
 }
 async dispatch_autorole(client) {
     try {
         const db = await pool.connect()
         const autorole = await this.wait_for_active_autoroles(db, client)
         if (autorole) {
             clearTimeout(client?.autorole_timer)
             const now = new Date()
             if (autorole.date >= now) {
                 client.autorole_timer = setTimeout(() => this.call_autorole(client, autorole, db), autorole.date.getTime() - now.getTime())
             } else {
                 await this.call_autorole(client, autorole, db)
             }
         }
     } catch (e) {
         console.log(e)
     }
 }

 async call_autorole(client, autorole, db) {
     await db.query("DELETE FROM autorole WHERE guild = $1 and member = $2 and role = $3 and date = $4", [autorole.guild, autorole.member, autorole.role, autorole.date])
     await db.release()
     try {
         const guild = client.guilds.cache.get(autorole.guild)
         const member = await guild.members.fetch(autorole.member)
         const role = guild.roles.cache.get(autorole.role)
         if (autorole.action) {
             await member.roles.add(role)
         } else {
             await member.roles.remove(role)
         }
     } catch (e) {
         await this.dispatch_autorole(client)
         console.log(e)
     }
     await this.dispatch_autorole(client)
 }
}

class GlobalTasks {
    async dispatch_global_tasks(client) {
        // run then timeout for 12 hours
        this.db = await pool.connect()
        this.client = client
        await this.boosterRewardRunner()
        await setTimeout(() => this.dispatch_global_tasks(), 12 * 60 * 60 * 1000)
    }

    async boosterRewardRunner() {
        const guild = await this.db.query("SELECT guild FROM boost WHERE type = $1 GROUP BY guild", ['boost'])
        if (guild.rowCount > 0) {
            // fetch the member list, then filter for the premiumSince property on the member and insert them into the database
            for (const get of guild.rows) {
                const guild = this.client.guilds.cache.get(get.guild)
                const announce = await this.db.query("SELECT announce FROM settings WHERE guild = $1", [guild.id])
                const boosting = this.db.query("SELECT date, role FROM boost WHERE type = $1 and guild = $2", ['boost', guild.id])
                for (const boost of guild.members.cache.filter(x => x.premiumSince)) {
                    const member = boost[1]
                    await this.db.query("INSERT INTO owner VALUES ($1, $2, $3) on conflict do nothing ", [guild.id, member.id, 'boost'])
                    for (const day of boosting.rows) {
                        const date = new Date(day.date)
                        const now = new Date()
                        if (date <= now) {
                            const role = guild.roles.cache.get(day.role)
                            if (role) {
                                const channel = guild.channels.cache.get(announce.rows[0].announce)
                                if (channel) {
                                    await channel.send(`Congrats to ${Formatters.userMention(member.id)} for boosting ${guild.name} for ${new Date(Date.now - member.premiumSince).getTime() / 1000 * 60 * 60 * 24} days!`)
                                }
                                await member.roles.add(role)
                            }
                        }
                    }
                }
                // do the check if the booster has stopped boosting at all and remove all of their rewards later
                const boosters = await this.db.query("SELECT member, role FROM owner inner join boost using(guild) WHERE boost.guild = $1 and boost.type = $2", [guild.id, 'boost'])
                for (const booster of boosters.rows) {
                    const member = guild.members.cache.get(booster.member)
                    if (!member?.premiumSince) {
                        await this.db.query("DELETE FROM owner WHERE guild = $1 and member = $2 and type = $3", [guild.id, booster.member, 'boost'])
                        const role = guild.roles.cache.get(booster.role)
                        if (role) {
                            await member.roles.remove(role)
                        }
                    }
                }
            }
        }
    await this.inviteRewardChecker()
    }

    async inviteRewardChecker() {
        const guild = await this.db.query("SELECT guild FROM boost WHERE type = $1 GROUP BY guild", ['invite'])
        if (guild.rowCount > 0) {
            for (const get of guild.rows) {
                const guild = this.client.guilds.cache.get(get.guild)
                const announce = await this.db.query("SELECT announce FROM settings WHERE guild = $1", [guild.id])
                const totals = await this.db.query("SELECT SUM(amount), member FROM invite WHERE guild = $1 GROUP BY member", [guild.id])
                const invite = await this.db.query("SELECT date, role FROM boost WHERE guild = $1 and type = $2", [guild.id, 'invite'])
                for (const total of totals.rows) {
                    const date = new Date(invite.rows[0].date)
                    const now = new Date()
                    if (date <= now) {
                        const role = guild.roles.cache.get(invite.rows[0].role)
                        if (role) {
                            const member = guild.members.cache.get(total.member)
                            if (member) {
                                const channel = guild.channels.cache.get(announce.rows[0].announce)
                                if (channel) {
                                    await channel.send(`Congrats to ${Formatters.userMention(total.member)} for inviting ${total.sum} users to ${guild.name}!`)
                                }
                                await member.roles.add(role)
                            }
                        }
                    }
                }
            }
        }
    await this.givePublicFlags()
    }

    async givePublicFlags() {
        const guild = await this.db.query("SELECT guild FROM flags GROUP BY guild")
        if (guild.rowCount > 0) {
            for (const get of guild.rows) {
                const guild = this.client.guilds.cache.get(get.guild)
                const flags = await this.db.query("SELECT role, flag FROM flags WHERE guild = $1", [guild.id])
                // if configured automatically gives a role depending on what public flags a member has
                for (const members of guild.members.cache) {
                    const member = members[1]
                    if (!member.user.bot) {
                        const publicFlags = member.user.flags
                        if (publicFlags) {
                            for (const flag of flags.rows) {
                                if (publicFlags.toArray().includes(flag.flag) && !member.roles.cache.has(flag.role)) {
                                    const role = guild.roles.cache.get(flag.role)
                                    if (role) {
                                        await member.roles.add(role)
                                    }
                                } else if (!publicFlags.toArray().includes(flag.flag) && member.roles.cache.has(flag.role)) {
                                    const role = guild.roles.cache.get(flag.role)
                                    if (role) {
                                        await member.roles.remove(role)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        await this.giveOnAccountCreationOrJoin()
    }

    async giveOnAccountCreationOrJoin() {
        const guild = await this.db.query("SELECT guild FROM roles WHERE type = $1 or type = $2 GROUP BY guild", ['create', 'join'])
        if (guild.rowCount > 0) {
            for (const get of guild.rows) {
                const guild = this.client.guilds.cache.get(get.guild)
                const position = await this.db.query("SELECT role, member, type FROM roles WHERE guild = $1 and type = $2 or type = $3", [guild.id, 'create', 'join'])
                if (position.rowCount > 0) {
                    for (const members of guild.members.cache) {
                        const member = members[1]
                        if (!member.user.bot) {
                            for (const pos of position.rows) {
                                if (pos.type === "create") {
                                    if (Date.now() - member.user.createdAt > pos.member) {
                                        const role = guild.roles.cache.get(pos.role)
                                        if (role) {
                                            await member.roles.add(role)
                                        }
                                    }
                                } else {
                                    if (Date.now() - member.user.joinedAt > pos.member) {
                                        const role = guild.roles.cache.get(pos.role)
                                        if (role) {
                                            await member.roles.add(role)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        await this.checkTopRanking()
    }

    async checkTopRanking() {
        const guild = await this.db.query("SELECT guild FROM leveling GROUP BY guild")
        if (guild.rowCount > 0) {
            for (const get of guild.rows) {
                const guild = this.client.guilds.cache.get(get.guild)
                const level = await this.db.query("SELECT level, role, type FROM leveling WHERE guild = $1 and system = $2", [guild.id, 'top'])
                if (level.rowCount > 0) {
                    for (const top of level) {
                        const current = await this.db.query("SELECT user_id FROM levels WHERE guild_id = $1 ORDER BY lvl DESC, exp DESC LIMIT 1", [guild.id])
                        if (current.rowCount > 0) {
                            const member = guild.members.cache.get(current.rows[0].user_id)
                            const role = guild.roles.cache.get(top.role)
                            if (member && role) {
                                for (const mem of role.members.cache) {
                                    if (mem.id !== member.id) {
                                        member.roles.remove(role)
                                    }
                                }
                                if (top.type === "day" && top.level === 1) {
                                    member.roles.add(role)
                                } else if (top.type === "week" && top.level === 7) {
                                    member.roles.add(role)
                                } else if (top.type === "month" && top.level === 30) {
                                    member.roles.add(role)
                                }
                            }
                        }
                    }
                    await this.db.query("UPDATE leveling SET level = level + 1 < 30 OR 0 WHERE guild = $1 and system = $2", [guild.id, 'top'])
                }
            }
        }
        await this.db.release()
    }
}


module.exports = {Reminder, Poll, Giveaway, AutoRole, GlobalTasks}