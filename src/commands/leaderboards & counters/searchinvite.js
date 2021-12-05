const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {MessageEmbed} = require("discord.js");
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
        const total = await db.query("SELECT amount, amount2, amount3, member FROM invite WHERE guild = $1 and invite = $2 LIMIT 1", [message.guild.id, message.options.getString("invite")])
        if (total.rowCount === 0) {
            message.reply("Invite not found")
            return
        }
        const row = total.rows[0]
        const embed = new MessageEmbed()
            .setTitle(`Invite: ${message.options.getString("invite")}`)
            .setDescription(`${row.amount} joins, ${row.amount2 ? `${row.amount2} ` : "0"} leaves, ${row.amount3 ? `${row.amount3} ` : "0"} fakes. (${(total.rows[0].amount - total.rows[0].amount2 + total.rows[0].amount3) || 0})`)
            .setColor('WHITE')
        await message.reply({embeds: [embed]})
        await db.release()
    }
}