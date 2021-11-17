const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("lookback")
        .setDescription("Sets how many days back the lookback should go")
        .addIntegerOption(option => option
            .setName("days")
            .setDescription("The number of days to look back")
            .setRequired(true)
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"]);
        const db = await pool.connect();
        const result = await db.query("SELECT lookback FROM settings WHERE lookback = $1 and guild = $2", [message.options.getInteger('days'), message.guild.id])
        const search = await db.query("SELECT lookback FROM settings WHERE guild = $1", [message.guild.id])
        if (result.rowCount === 0) {
            if (message.options.getInteger('days') <= 120) {
                if (search.rowCount === 0) {
                    await db.query("INSERT INTO settings(guild, lookback) VALUES($1, $2)", [message.guild.id, message.options.getInteger('days')])
                    message.reply(`Set the lookback to ${message.options.getInteger('days')} days`)
                } else {
                    await db.query("UPDATE settings SET lookback = $1 WHERE guild = $2", [message.options.getInteger('days'), message.guild.id])
                    message.reply(`Set the lookback to ${message.options.getInteger('days')} days`)
                }
            } else {
                message.reply("The lookback can't be more than 120 days")
            }
        } else {
            await db.query("UPDATE settings SET lookback = $1 WHERE guild = $2", [message.options.getInteger('days'), message.guild.id])
            message.reply(`Set the lookback to ${message.options.getInteger('days')} days`)
        }
        await db.release()
    }
}