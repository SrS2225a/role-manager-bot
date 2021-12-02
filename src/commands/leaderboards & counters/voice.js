const {SlashCommandBuilder, ContextMenuCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {MessageEmbed} = require("discord.js");
const {display_time} = require("../../structures/converters");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("voice")
        .setDescription("View the amount of voice time you have acquired")
        .addUserOption(option => option
            .setName("user")
            .setDescription("The user to view voice time for")
            .setRequired(false)),
    context: new ContextMenuCommandBuilder()
        .setName("Voice")
        .setType(2),
    async execute(message) {
        const db = await pool.connect()
        const user = message.options.getUser("user") || message.user
        const voice = await db.query("SELECT channel, SUM(voice)::integer AS a, SUM(voice2)::integer AS b FROM voice WHERE guild = $1 and member = $2 GROUP BY channel ORDER BY sum(voice) DESC, sum(voice2) DESC", [message.guild.id, user.id])
        const place = await db.query("SELECT COUNT(*) FROM (SELECT member, SUM(voice)::integer AS a, SUM(voice2)::integer AS b FROM voice WHERE guild = $1 GROUP BY member ORDER BY sum(voice) DESC, sum(voice2) DESC) AS t WHERE a >= $2 AND b >= $3", [message.guild.id, voice.rows[0].a, voice.rows[0].b])
        if (voice.rowCount === 0) return message.channel.send("You have not yet recorded any voice time")
        const embed = new MessageEmbed()
            .setTitle(`${user.username}'s Voice Time`)
            .setDescription(`${voice.rows.map(row => `**<#${row.channel}>**: ${display_time(row.a + row.b, 6)}`).join("\n")}`)
            .addField("Total Voice Time", display_time(voice.rows.map(row => row.a + row.b).reduce((acc, val) => acc + val, 0), 6))
            .setFooter(`You are in place #${place.rows[0].count} with your voice time`)
        message.reply({embeds: [embed]})
        await db.release()
    }
}