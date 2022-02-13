const {pool} = require("../../database");
module.exports = {
    name: 'messageReactionAdd',
    once: false,
    async execute(reaction, mem) {
        try {
            // check if user is bot
            if (reaction.emoji.name === '🎉' && !mem.bot) {
                function removeEntree(error) {
                    reaction.users.remove(user.id)
                    try {
                        mem.send(error)
                    } catch (error) {
                        console.log(error)
                    }
                }

                const user = reaction.message.guild.members.cache.get(mem.id) || await reaction.message.guild.members.fetch(mem.id);
                const db = await pool.connect()
                const result = await db.query("SELECT options FROM vote WHERE guild = $1 and message = $2 and channel = $3 and type = $4 or type = $5", [reaction.message.guild.id, reaction.message.id, reaction.message.channel.id, 0, 1])
                let sendSuccess = true
                if (result.rowCount > 0) {
                    const res = result.rows[0].options
                    if (res?.role_requirement) {
                        const role = reaction.message.guild.roles.cache.get(res.role_requirement)
                        if (!user.roles.cache.has(role.id)) {
                            removeEntree("Failed to enter giveaway. You don't have the required role.")
                            sendSuccess = false
                        }
                    }
                    if (res?.message_requirement) {
                        console.log(res.message_requirement)
                        const messages = await db.query("SELECT member FROM message WHERE guild = $1 GROUP BY member HAVING SUM(messages) >= $2 and member = $3", [reaction.message.guild.id, res.message_requirement, user.id])
                        if (messages.rowCount < 1) {
                            removeEntree("Failed to enter giveaway. You don't have the required messages.")
                            sendSuccess = false
                        }
                    }
                    if (res?.voice_requirement) {
                        // select by voice_requirement
                        const voice = await db.query("SELECT member FROM voice WHERE guild = $1 GROUP BY member HAVING SUM(voice.voice OR voice2) >= $2 and member = $3", [reaction.message.guild.id, res.voice_requirement, user.id])
                        if (voice.rowCount < 1) {
                            removeEntree("Fail to enter giveaway. You don't have the required voice time.")
                            sendSuccess = false
                        }
                    }
                    if (sendSuccess) {
                        // catch error
                        try {
                            mem.send("You have entered the giveaway.")
                        } catch (error) {
                            console.log(error)
                        }
                    }
                }
                await db.release()
            }
        } catch (e) {
            console.log(e);
        }
    }
}