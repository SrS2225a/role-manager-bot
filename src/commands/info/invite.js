const {SlashCommandBuilder} = require("@discordjs/builders");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("invite")
        .setDescription("Gives you a link to invite the bot"),
    async execute(message) {
        await message.reply("https://discord.com/api/oauth2/authorize?client_id=437447118127366154&permissions=8&scope=bot%20applications.commands")
    }
}