const {pool} = require("../database");
module.exports = {
    name: 'messageReactionRemove',
    once: false,
    async execute(reaction, user) {
        const db = await pool.connect()
        try {
            const member = await reaction.message.guild.members.fetch(user.id);
            const react = await db.query("SELECT * FROM reaction WHERE guild = $1 and channel = $2 and message = $3 and emote = $4", [reaction.message.guild.id, reaction.message.channel.id, reaction.message.id, reaction.emoji.id ? reaction.emoji.id : reaction.emoji.name])
            if (react.rowCount > 0) {
                if (react.rows[0].type.indexOf("once")) {
                    await member.roles.remove(react.rows[0].role)
                }
            }
        } catch (err) {
            console.log(err)
        } finally {
            db.release()
        }
    }
}