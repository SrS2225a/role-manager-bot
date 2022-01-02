const {pool} = require("../database");
const {Formatters, Permissions} = require("discord.js");
const {AutoRole} = require("../structures/tasks");

async function create_autorole_timer(client, db, argument) {
    const date = new Date(Date.now() + (argument[3] * 1000));
    await db.query("INSERT INTO autorole (member, role, action, date, guild) VALUES ($1, $2, $3, $4, $5)", [argument[0], argument[1], argument[2], date, argument[4]]);
    if (!client.current_timer || client.current_timer[3] < date) {
        const autorole = new AutoRole()
        await autorole.dispatch_autorole(client)
    }
}

module.exports = {
    name: 'guildMemberAdd',
    once: false,
    async execute(member) {
        const db = await pool.connect()
        try {
            // for member join graph
            // increment member joins by 1 else add on a new date
            const memberJoin = await db.query("SELECT joins FROM member WHERE guild = $1 and day = $2 LIMIT 1", [member.guild.id, new Date()])
            if (memberJoin.rowCount === 0) {
                await db.query("INSERT INTO member (guild, day, joins, leaves) VALUES ($1, $2, 1, 0)", [member.guild.id, new Date()])
            } else {
                await db.query("UPDATE member SET joins = joins + 1 WHERE guild = $1 and day = $2", [member.guild.id, new Date()])
            }
            // end member join graph

            // for sticky roles
            const sticky = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3", [member.guild.id, member.id, "sticky"])
            for (const stickyRole of sticky.rows) {
                const role = member.guild.roles.cache.get(stickyRole.role)
                if (role) {
                    member.roles.add(role)
                }
            }
            // end sticky roles

            // for ping on join
            const ping = await db.query("SELECT role AS channel FROM reward WHERE guild = $1 and type = $2", [member.guild.id, "poj"])
            // can have multiple ping on joins
            for (const pingJoin of ping.rows) {
                const channel = member.guild.channels.cache.get(pingJoin.channel)
                if (channel) {
                    const poj = await channel.send(Formatters.userMention(member.user.id))
                    await poj.delete()
                }
            }
            // end ping on join

            // for member join role
            const auto = await db.query("SELECT role, member AS delay, type FROM roles WHERE guild = $1 and type = $2 or type = $3", [member.guild.id, "add", "remove"])
            for (const autoRole of auto.rows) {
                if (autoRole.type === "add") {
                    const role = member.guild.roles.cache.get(autoRole.role)
                    if (role) {
                        if (autoRole.delay > 0) {
                            await create_autorole_timer(member.client, db, [member.id, role.id, true, autoRole.delay, member.guild.id])
                        } else {
                            member.roles.add(role)
                        }
                    }
                } else if (autoRole.type === "remove") {
                    const role = member.guild.roles.cache.get(autoRole.role)
                    if (role) {
                        if (autoRole.delay > 0) {
                            await create_autorole_timer(member.client, db, [member.id, role.id, true, autoRole.delay, member.guild.id])
                        } else {
                            member.roles.remove(role)
                        }
                    }
                }
            }
            // end member join role

            // for invite update emitter
            await member.guild.invites?.fetch().then(newInvites => {
                const oldInvites = member.client.invites?.get(member.guild.id)
                const invite = newInvites.find(i => i.uses > oldInvites?.get(i.code))
                if (invite) {
                    oldInvites.set(invite.code, invite.uses)
                    member.client.emit("inviteUpdate", member, invite)
                }
            }).catch(err => {
                console.log(err)
            })
            // end invite update emitter

            // for channel overwrites recoverer
            const recover = await db.query("SELECT yes, no, channel FROM recover WHERE guild = $1 and member = $2", [member.guild.id, member.id])
            for (const overwrite of recover.rows) {
                const channel = member.guild.channels.cache.get(overwrite.channel)
                // resolve overwrite bitfield as an object mapping permission flags to true (enabled) or false (disabled)
                const yes = new Permissions(overwrite.yes).toArray().reduce((acc, perm) => {
                    acc[perm] = true
                    return acc
                }, {})
                const no = new Permissions(overwrite.no).toArray().reduce((acc, perm) => {
                    acc[perm] = false
                    return acc
                }, {})
                const permissions = Object.assign(yes, no)
                if (channel) {
                    await channel.permissionOverwrites.create(member, permissions)
                }
            }
            // end channel overwrites recoverer
        } catch (e) {
            console.error(e)
        } finally {
            await db.release()
        }
    }
}