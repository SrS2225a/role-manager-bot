const {SlashCommandBuilder} = require("@discordjs/builders");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("opensource")
        .setDescription("Gives you a link to the open source project of the bot"),
    async execute(message) {
        await message.reply("https://github.com/SrS2225a/role-manager-bot")
    }
}