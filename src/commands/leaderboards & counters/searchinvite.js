const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {EmbedBuilder} = require("discord.js");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("searchinvite")
        .setDescription("Search for an invite")
        .addStringOption(option => option
            .setName("invite")
            .setRequired(true)
            .setDescription("The invite to search for")),
    async execute(message) {
        const db = await pool.connect()
        const total = await db.query("SELECT SUM(amount)::integer AS amount, SUM(amount2)::integer AS amount2, SUM(amount3)::integer AS amount3, member FROM invite WHERE guild = $1 and invite.invite = $2 GROUP BY member", [message.guild.id, message.options.getString("invite")])
        if (total.rowCount === 0) {
            message.reply("Invite not found")
            return
        }
        const row = total.rows[0]
        const embed = new EmbedBuilder()
            .setTitle(`Invite: ${message.options.getString("invite")}`)
            .setDescription(`${row.amount} joins, ${row.amount2 ? `${row.amount2} ` : "0"} leaves, ${row.amount3 ? `${row.amount3} ` : "0"} fakes. (${(total.rows[0].amount - total.rows[0].amount2 + total.rows[0].amount3) || 0})`)
            .setColor('WHITE')
        await message.reply({embeds: [embed]})
        await db.release()
    }
}