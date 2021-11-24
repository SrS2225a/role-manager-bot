const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("command")
        .setDescription("Allows you to enable/disable a command")
        .addSubcommand(subcommand => subcommand
            .setName("enable")
            .setDescription("Enables a command or cog")
            .addStringOption(option => option
                .setName("command")
                .setDescription("The name of the command to enable")
                .setRequired(true)))
        .addSubcommand(subcommand => subcommand
            .setName("disable")
            .setDescription("Disables a command or cog")
            .addStringOption(option => option
                .setName("command")
                .setDescription("The name of the command to disable")
                .setRequired(true))),
    async execute(message) {
        const db = await pool.connect()
        if (message.options.getSubcommand() === "enable") {
            const command = message.options.getString("command")
            message.client.application.commands.fetch(command).then(async cmd => {
                if (!cmd) {
                    message.channel.send("That command doesn't exist!")
                } else {
                    await db.query("DELETE FROM blacklist WHERE member = $1 and message = $2 and type = $3", [message.guildId, cmd.name, 'command'])
                }
            })
            message.reply("Command enabled!")
        } else if (message.options.getSubcommand() === "disable") {
            const command = message.options.getString("command")
            message.client.application.commands.fetch(command).then(async cmd => {
                if (!cmd) {
                    message.channel.send("That command doesn't exist!")
                } else {
                    await db.query("INSERT INTO blacklist (member, message, type) VALUES ($1, $2, $3)", [message.guildId, cmd.name, 'command'])
                }
            })
        }
        await db.release()
    }
}