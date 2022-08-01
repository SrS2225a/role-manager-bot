const {pool} = require("../database");
const {resolveAsChannel_Role} = require("../structures/resolvers");
const {AutoRole} = require("../structures/tasks");
module.exports = {
    name: 'guildMemberRemove',
    once: false,
    async execute(member) {
        const db = await pool.connect()
        try {
            // for autoroles
            await db.query("DELETE FROM autorole WHERE guild = $1 and member = $2", [member.guild.id, member.id])
            if (member.client.current_timer[1] === member.id) {
                const autorole = new AutoRole()
                await autorole.dispatch_autorole()
            }
            // end autoroles

            // for member leave graph
            await db.query("UPDATE member SET leaves = member.leaves + 1 WHERE guild = $1 and day = current_date", [member.guild.id])
            // end member leave graph

            // for invite leaves
            const invite = await db.query("SELECT invite FROM invite2 WHERE guild = $1 and member = $2 LIMIT 1", [member.guild.id, member.id])
            if (invite.rowCount > 0) {
                await db.query("DELETE FROM invite2 WHERE member = $1 and guild = $2", [member.id, member.guild.id])
                // do not forget: in the main projection branch, create and set the invite day column to the current date before the changes go live
                // for the new changes can work properly
                if (new Date(Date.now() - member.joinedAt) < 120000) {
                    await db.query("UPDATE invite SET amount3 = amount3 + 1 WHERE guild = $1 and invite.invite = $2 and day = (SELECT MAX(day) FROM invite)", [member.guild.id, invite.rows[0].invite])
                } else {
                    await db.query("UPDATE invite SET amount2 = amount2 + 1 WHERE guild = $1 and invite.invite = $2 and day = (SELECT MAX(day) FROM invite)", [member.guild.id, invite.rows[0].invite])
                }
            }
            // end invite leaves

            // for custom channels / roles
            const custom = await db.query("SELECT role, type FROM roles WHERE guild = $1 and member = $2 and not type = 'sticky'", [member.guild.id, member.id])
            for (const row of custom.rows) {
                const role = resolveAsChannel_Role(member, row.role)
                if (role) {
                    await db.query("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", [member.guild.id, row.role, member.id, row.type])
                    await role.delete()
                }
            }
            // end custom channels / roles

            // for leveling
            const clear = await db.query("SELECT type FROM leveling WHERE guild = $1 and system = $2 LIMIT 1", [member.guild.id, 'clear'])
            if (clear.rowCount > 0) {
                await db.query("DELETE FROM levels WHERE guild_id = $1 and user_id = $2", [member.guild.id, member.id])
            }
        } catch (e) {
            console.log(e)
        } finally {
            await db.release()
        }
    }
}