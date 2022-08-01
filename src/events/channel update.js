const {pool} = require("../database");
module.exports = {
    name: 'channelUpdate',
    once: false,
    async execute(before, after) {
        if (before.members !== after.members) {
            const db = await pool.connect()
            try {
                const recovery = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [after.guild.id, after.id, "overwrite"])
                if (recovery.rowCount > 0) {
                    const role = before.guild.roles.cache.find(r => r.id === recovery.rows[0].role)
                    if (role) {
                        for (const overwrites of after.permissionOverwrites.cache.values()) {
                            const member = await after.guild.members.fetch(overwrites.id).catch(() => null)
                            if (overwrites.type === "member" && member.roles.cache.has(role.id)) {
                                const check = await db.query("SELECT member FROM recover WHERE guild = $1 and member = $2 and channel = $3 LIMIT 1", [before.guild.id, overwrites.id, after.id])
                                if (check.rowCount === 0) {
                                    await db.query("INSERT INTO recover (guild, member, channel, yes, no) VALUES ($1, $2, $3, $4, $5)", [before.guild.id, overwrites.id, after.id, overwrites.allow.bitfield, overwrites.deny.bitfield])
                                } else {
                                    await db.query("UPDATE recover SET yes = $1, no = $2 WHERE guild = $3 and member = $4 and channel = $5", [overwrites.allow.bitfield, overwrites.deny.bitfield, before.guild.id, overwrites.id, after.id])
                                }
                            }
                        }
                    }
                }
            } catch (e) {
                console.log(e)
            } finally {
                await db.release()
            }
        }
    }
}