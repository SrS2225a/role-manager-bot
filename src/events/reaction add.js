const {pool} = require("../database");
const {Formatters} = require("discord.js");
module.exports = {
    name: 'messageReactionAdd',
    once: false,
    async execute(reaction, user) {
        // attempt to resolve the user as a member
        const db = await pool.connect()
        try {
            const member = await reaction.message.guild.members.fetch(user.id);
            // change custom emoji to id if needed
            const react = await db.query("SELECT * FROM reaction WHERE guild = $1 and channel = $2 and message = $3 and emote = $4", [reaction.message.guild.id, reaction.message.channel.id, reaction.message.id, reaction.emoji.id ? reaction.emoji.id : reaction.emoji.name])
            if (react.rowCount > 0 && !member.bot) {
                if (!member.roles.cache.has(react.rows[0]?.blacklist)) {
                    if (react.rows[0].type === "once") {
                        const roles = await db.query("SELECT role FROM reaction WHERE guild = $1 and channel = $2 and message = $3", [reaction.message.guild.id, reaction.message.channel.id, reaction.message.id])
                        if (roles.rowCount > 0) {
                            const hasRole = member.roles.cache.filter(role => roles.rows.map(r => r.role).includes(role.id))
                            if (hasRole.size > 0) {
                                await reaction.users.remove(member)
                                const notify = await reaction.message.channel.send(`${Formatters.userMention(member.id)} you cannot change your roles after reacting to this reaction role category!`)
                                setTimeout(async () => {
                                    await notify.delete()
                                }, 4000)
                            } else {
                                await member.roles.add(react.rows[0].role)
                            }
                        }
                        await member.roles.add(react.rows[0].role)
                    } else if (react.rows[0].type === "toggle") {
                        "INSERT INTO reaction VALUES(guild, channel, message, emote, role, type, blacklist)"
                        const roles = await db.query("SELECT role FROM reaction WHERE guild = $1 and channel = $2 and message = $3", [reaction.message.guild.id, reaction.message.channel.id, reaction.message.id])
                        if (roles.rowCount > 0) {
                            // check if the user already has the role in roles and not remove react.rows[0].role
                            const hasRole = member.roles.cache.filter(role => roles.rows.map(r => r.role).includes(role.id))
                            if (hasRole.size > 0) {
                                await member.roles.remove(hasRole)
                            }

                        }
                        await member.roles.add(react.rows[0].role)
                    } else if (react.rows[0].type === "reaction") {
                        member.roles.add(react.rows[0].role)
                    } else if (react.rows[0].type === "club") {
                        const clubBlacklist = await db.query("SELECT message FROM owner WHERE guild = $1 and member = $2 and message = $3 and type = $4", [reaction.message.guild.id, member.id, reaction.message.id, "blacklist"])
                        if (clubBlacklist.rowCount > 0) {
                            await reaction.users.remove(member)
                        } else {
                            await member.roles.add(react.rows[0].role)
                        }
                    }
                } else {
                    const notify = await reaction.message.channel.send(`${Formatters.userMention(member.id)} you do not have the required role to get this role from the reaction role!`)
                    setTimeout(async () => {
                        await notify.delete()
                    }, 4000)
                }
            }
        } catch (e) {
            console.log(e)
        } finally {
            await db.release()
        }
    }
}