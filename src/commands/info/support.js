const {SlashCommandBuilder} = require("@discordjs/builders");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("support")
        .setDescription("Gives you a link to the Dionysus support server"),
    async execute(message) {
        await message.reply("https://discord.gg/JHkhnzDvWG")
    }
}