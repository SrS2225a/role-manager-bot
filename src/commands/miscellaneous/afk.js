const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("afk")
        .setDescription("Marks you as AFK")
        .addStringOption(option =>
        option.setName('reason')
            .setDescription("Optional reason for going AFK")
            .setRequired(false)),
    async execute(message) {
        const db = await pool.connect()
        const reason = await message.options.getString('reason') || "AFK"
        const afk = await db.query("SELECT member FROM afk WHERE guild = $1 and member = $2 LIMIT 1", [message.guildId, message.user.id])
        if (afk.rows.length) {
            const nick = message.member.displayName
            await message.member.edit({nick: nick.split('[AFK]')[0]}).catch(() => undefined)
            await db.query("DELETE FROM afk WHERE guild = $1 and member = $2", [message.guildId, message.user.id])
            await message.reply(`<@${message.user.id}> I marked you as no longer AFK!`)
        } else {
            const nick = '[AFK] ' + message.member.displayName
            if (nick.length < 32) {
                await message.member.edit({nick: nick}).catch(() => undefined)
            }
            await db.query("INSERT INTO afk(guild, member, message, count) VALUES($1, $2, $3, $4)", [message.guildId, message.user.id, reason, 0])
            await message.reply(`<@${message.user.id}> I marked you as AFK!`)
        }
        await db.release()
    }
}