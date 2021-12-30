const {pool} = require("../database");
module.exports = {
    name: 'inviteUpdate',
    once: false,
    async execute(member, invite) {
        const db = await pool.connect()
        try {
            const res = await db.query("SELECT invite FROM invite WHERE guild = $1 and invite.invite = $2 and member = $3", [member.guild.id, invite.code, invite.inviter.id])
            if (res.rowCount > 0) {
                await db.query("UPDATE invite SET amount = $1 WHERE guild = $2 and invite.invite = $3 and member = $4", [invite.uses, member.guild.id, invite.code, invite.inviter.id])
                const inviteReward = await db.query("SELECT * FROM boost WHERE guild = $1 and type = $2", [member.guild.id, 'inviter'])
                if (inviteReward.rowCount > 0) {
                    for (let i = 0; i < inviteReward.rowCount; i++) {
                        if (inviteReward.rows[i].invite === invite.code) {
                            const announce = await db.query("SELECT announce FROM settings WHERE guild = $1", [member.guild.id])
                            const role = await member.guild.roles.cache.get(inviteReward.rows[i].role)
                            await member.roles.add(role)
                            const channel = await member.guild.channels.cache.get(announce.rows[0].announce)
                            if (channel) {
                                await channel.send(`Congratulations ${member.user.tag}! You have been given the role ${role.name} for inviting ${invite.inviter.tag}`)
                            }
                            break
                        }
                    }
                }
            } else {
                await db.query("INSERT INTO invite VALUES($1, $2, $3, $4, 0, 0, $5)", [member.guild.id, invite.inviter.id, invite.code, invite.uses, invite.channel.id])
            }
            await db.query("INSERT INTO invite2 VALUES($1, $2, $3)", [member.guild.id, member.id, invite.code])
        } catch (err) {
            console.log(err)
        } finally {
            db.release()
        }
    }
}
