const {pool} = require("../database");
module.exports = {
    name: 'voiceStateUpdate',
    once: false,
    async execute(before, after) {
        if (before.channel !== after.channel) {
            const db = await pool.connect()
            try {
                const channel = after.channel || before.channel
                const member = after.member || before.member
                // for voice roles
                const voice = await db.query("SELECT role FROM reward WHERE guild = $1 and channel = $2 and type = $3 LIMIT 1", [channel.guild.id, channel.id, "voice"])
                if (voice.rowCount > 0) {
                    const role = channel.guild.roles.cache.get(voice.rows[0].role)
                    if (role) {
                        if (after.channel) {
                            after.channel.guild.members.cache.get(after.member.id).roles.add(role)
                        } else {
                            before.channel.guild.members.cache.get(before.member.id).roles.remove(role)
                        }
                    }
                }
                // end of voice roles

                // for voice graph
                const graph = await db.query("SELECT * FROM voice WHERE guild = $1 and member = $2 and channel = $3 and day = $4 LIMIT 1", [channel.guild.id, member.id, channel.id, new Date()])
                if (graph.rowCount === 0) {
                    await db.query("INSERT INTO voice VALUES ($1, $2, $3, $4, 0, 0, $5)", [new Date(), channel.guild.id, member.id, channel.id, new Date()])
                    await db.query("DELETE FROM member WHERE day < $1", [new Date(Date.now() - 8640000000)])
                } else {
                    if (after.channel) {
                        await db.query("UPDATE voice SET created = $1 WHERE guild = $2 and member = $3 and channel = $4 and day = $5", [new Date(), channel.guild.id, after.id, channel.id, new Date()])
                    } else {
                        const time = new Date() - graph.rows[0].created
                        if (before.channel.type === "GUILD_VOICE") {
                            await db.query("UPDATE voice SET voice = voice.voice + $1 WHERE guild = $2 and member = $3 and channel = $4 and day = $5", [Math.floor(time / 1000), channel.guild.id, member.id, channel.id, new Date()])
                        } else {
                            await db.query("UPDATE voice SET voice2 = voice.voice2 + $1 WHERE guild = $2 and member = $3 and channel = $4 and day = $5", [Math.floor(time / 1000), channel.guild.id, member.id, channel.id, new Date()])
                        }
                    }
                }
                // end of voice graph
            } catch (e) {
                console.log(e)
            } finally {
                db.release()
            }
        }
    }
}