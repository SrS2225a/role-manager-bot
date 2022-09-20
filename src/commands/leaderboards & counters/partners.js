const {SlashCommandBuilder, ContextMenuCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {Colors, EmbedBuilder} = require("discord.js");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("partners")
        .setDescription("Shows info about how many partnerships you completed or someone else's")
        .addUserOption(option => option
            .setName("user")
            .setDescription("The user to check the partners of.")
            .setRequired(false)),
    context: new ContextMenuCommandBuilder()
        .setName("Partners")
        .setType(2),
    async execute(message) {
        const db = await pool.connect()
        const user = message.options.getUser("user") || message.user
        const check = await db.query("SELECT system FROM leveling WHERE guild = $1 and system= $2", [message.guild.id, "partners"])
        if (check.rowCount === 0) return message.reply("This server has not enabled partners")
        const result = await db.query("SELECT number FROM partner WHERE guild = $1 and member = $2", [message.guild.id, user.id])
        if (result.rowCount === 0) return message.reply(`${user.username} has not completed any partnerships`)
        const place = await db.query("SELECT COUNT(*)::integer FROM (SELECT member, sum(number)::integer AS a FROM partner WHERE guild = $1 GROUP BY member ORDER BY sum(number) DESC) AS t WHERE a >= $2", [message.guild.id, result.rows[0].number])
        const embed = new EmbedBuilder()
            .setTitle(`${user.username}'s partnerships`)
            .setColor(Colors.White)
            .setDescription(`${user.username} has completed ${result.rows[0].number} partnerships`)
            .addFields({name: "Place", value: place.rows[0].count.toString()})
        await message.reply({embeds: [embed]})
        await db.release()
    }
}