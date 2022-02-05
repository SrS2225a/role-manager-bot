const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {MessageEmbed} = require("discord.js");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("suggest")
        .setDescription("Makes a suggestion for the server")
        .addStringOption(option =>
        option.setName("suggestion")
            .setDescription("The suggestion to suggest")
            .setRequired(true)),
    async execute(message) {
        const db = await pool.connect()
        const vote = ['✔', '❌']
        const result = db.query("SELECT suggest FROM settings WHERE guild = $1", message.guild.id)
        if (result.rows.length) {
            const channel = message.guild.channels.fetch(result.rows[0].suggest).catch(null)
            const embed = new MessageEmbed()
                .setTitle(`${message.author.username + '#' + message.author.tag} Suggestion`)
                .setDescription(await message.interaction.getString("suggestion"))
            const sent = await channel.send({embeds: [embed]})
            for (const reaction in vote) {
                await sent.react(reaction)
            }
            await message.channel.send("Suggestion sent!")
        } else {
            await message.channel.send("Suggestions are currently not enabled by this server!")
        }
        await db.release()
    }
}