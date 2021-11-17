const {pool} = require("../database");
module.exports = {
    name: 'guildMemberUpdate',
    once: false,
    async execute(before, after) {
        if (before.roles !== after.roles) {
            const db = await pool.connect()
            // for custom roles / text channels / voice channels
            const roles = await db.query("SELECT custom.role AS a, roles.role AS b, type FROM custom INNER JOIN roles USING (guild) WHERE guild = $1 and member = $2 and remove = true and not type = 'sticky'", [after.guild.id, after.id])
            for (const role of roles.rows) {
                if (!after.roles.cache.has(role.a)) {
                    const custom = after.guild.roles.cache.get(role.b)
                    await db.query("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", [after.guild.id, role.b, after.id, role.type])
                    if (custom) {
                        await custom.delete()
                    }
                }
            }
            // for sticky roles
            const sticky = await db.query("SELECT role FROM reward WHERE guild = $1 and type = 'sticky'", [after.guild.id])
            for (const role of sticky.rows) {
                if (!after.roles.cache.has(role.role) && Date.now() + after.joinedAt > 4000) {
                    // if the member joins do not delete while giving it to them
                    await db.query("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", [after.guild.id, role.role, after.id, 'sticky'])
                } else {
                    await db.query("INSERT INTO roles (guild, role, member, type) SELECT $1, $2, $3, $4 WHERE NOT EXISTS (SELECT 1 FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4)", [after.guild.id, role.role, after.id, 'sticky'])
                }
            }
        await db.release()
        }
    }
}