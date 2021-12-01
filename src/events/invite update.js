const {pool} = require("../database");
module.exports = {
    name: 'inviteUpdate',
    once: false,
    async execute(member, invite) {
        const db = await pool.connect()
        console.log(invite)
        try {
            const res = await db.query("SELECT invite FROM invite WHERE guild = $1 and invite.invite = $2 and member = $3", [member.guild.id, invite.code, invite.inviter.id])
            if (res.rowCount > 0) {
                await db.query("UPDATE invite SET amount = $1 WHERE guild = $2 and invite.invite = $3 and member = $4", [invite.uses, member.guild.id, invite.code, invite.inviter.id])
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
