const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("suggestion")
        .setDescription("Sets up the suggestion channel")
        .addChannelOption(channel => channel
            .setName("channel")
            .setDescription("The channel that suggestions are sent to")
            .setRequired(true)
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"]);
        const db = await pool.connect();
        const result = await db.query("SELECT suggest FROM settings WHERE suggest = $1 and guild = $2", [message.options.getChannel('channel').id, message.guild.id])
        const search = await db.query("SELECT suggest FROM settings WHERE guild = $1", [message.guild.id])
        if (result.rowCount === 0) {
            if (search.rowCount === 0) {
                await db.query("INSERT INTO settings(guild, suggest) VALUES($1, $2)", [message.guild.id, message.options.getChannel('channel').id])
                message.reply(`Set the suggestion to ${message.options.getChannel('channel').name}`)
            } else {
                await db.query("UPDATE settings SET suggest = $1 WHERE guild = $2", [message.options.getChannel('channel').id, message.guild.id])
                message.reply(`Set the suggestion to ${message.options.getChannel('channel').name}`)
            }
        } else {
            await db.query("DELETE FROM settings WHERE suggest = $1 and guild = $2", [message.options.getChannel('channel').id, message.guild.id])
            message.reply(`Set the suggestion to ${message.options.getChannel('channel').name}`)
        }
        await db.release()
    }
}