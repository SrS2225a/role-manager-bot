const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {userPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("pingonjoin")
        .setDescription("Modifies whether or not the bot should ping users when they join")
        .addChannelOption(channel => channel
            .setName("channel")
            .setDescription("The channel that the bot should ping users when they join")
            .setRequired(true)),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"])
        const db = await pool.connect();
        const result = await db.query("SELECT role FROM reward WHERE guild = $1 and channel = $2 and type = $3", [message.guild.id, message.options.getChannel('channel').id, 'poj'])
        if (result.rowCount === 0) {
            await db.query("INSERT INTO reward(guild, channel, type) VALUES($1, $2, $3)", [message.guild.id, message.options.getChannel('channel').id, 'poj'])
            message.reply(`Set the ping on join to ${message.options.getChannel('channel').name}`)
        } else {
            await db.query("DELETE FROM reward WHERE guild = $1 and channel = $2 and type = $3", [message.guild.id, message.options.getChannel('channel').id, 'poj'])
            message.reply(`Set the ping on join to ${message.options.getChannel('channel').name}`)
        }
        await db.release();
    }
}