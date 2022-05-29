const {SlashCommandBuilder, ContextMenuCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {MessageEmbed} = require("discord.js");
const {display_time} = require("../../structures/converters");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("messages")
        .setDescription("View the amount of messages you or another user have sent.")
        .addUserOption(option => option
            .setName("user")
            .setDescription("The user to view the amount of messages they have sent.")
            .setRequired(false)),
    context: new ContextMenuCommandBuilder()
        .setName("Messages")
        .setType(2),
    async execute(message) {
        const db = await pool.connect()
        const user = message.options.getUser("user") || message.user
        const messages = await db.query("SELECT channel, SUM(messages)::integer FROM message WHERE guild = $1 and member = $2 GROUP BY channel ORDER BY sum(messages) DESC", [message.guild.id, user.id])
        if (messages.rowCount === 0) return message.reply("You have not sent any messages in this server.")
        const place = await db.query("SELECT COUNT(*)::integer FROM (SELECT member, sum(messages)::integer AS a FROM message WHERE guild = $1 GROUP BY member ORDER BY sum(messages) DESC) AS t WHERE a >= $2", [message.guild.id, messages.rows[0].sum])
        const embed = new MessageEmbed()
            .setTitle(`${user.username}'s Messages`)
            .setColor('WHITE')
            .setFooter(`${user.username} is in ${place.rows[0].count} place with ${messages.rows.reduce((acc, cur) => acc + cur.sum, 0)} messages.`)

        let empty_message = 0
        let total_message = []
        messages.rows.forEach(row => {
            if (!message.guild.channels.cache.has(row.channel)) empty_message += row.sum
            else total_message.push(`**<#${row.channel}>** - ${row.sum}`)
        })
        embed.setDescription(empty_message > 0 ? `${total_message.join("\n")}\n\n**deleted channel(s)** - ${empty_message}` : total_message.join("\n"))
        message.reply({embeds: [embed]})
        await db.release()
    }
}