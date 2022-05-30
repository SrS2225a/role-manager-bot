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
        if (voice.rowCount === 0) return message.channel.send("You have not yet recorded any voice time")
        const place = await db.query("SELECT COUNT(*) FROM (SELECT member, SUM(voice)::integer AS a, SUM(voice2)::integer AS b FROM voice WHERE guild = $1 GROUP BY member ORDER BY sum(voice) DESC, sum(voice2) DESC) AS t WHERE a >= $2 AND b >= $3", [message.guild.id, voice.rows[0]?.a, voice.rows[0].b])
        const embed = new MessageEmbed()
            .setTitle(`${user.username}'s Voice Time`)
            .setColor('WHITE')
            .setFooter(`You are in place #${place.rows[0].count} with ${display_time(voice.rows.map(row => row.a + row.b).reduce((acc, val) => acc + val, 0), 6)} voice time.`)
        
        let empty_voice = 0
        let total_voice = []
        voice.rows.forEach(row => {
            if (!message.guild.channels.cache.has(row.channel)) empty_voice += row.a + row.b
            else total_voice.push(`**<#${row.channel}>** - ${display_time(row.a + row.b, 6)}`)
        })
        embed.setDescription(empty_voice > 0 ? `${total_voice.join("\n")}\n\n**deleted channel(s)** - ${display_time(empty_voice, 6)}` : total_voice.join("\n"))
        message.reply({embeds: [embed]})
        await db.release()
    }
}