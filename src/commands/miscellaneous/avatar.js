const {SlashCommandBuilder} = require("@discordjs/builders");
const {MessageEmbed} = require("discord.js");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("avatar")
        .setDescription("Enlarges a members avatar")
        .addUserOption(option =>
            option.setName('user')
                .setDescription("The avatar to enlarge")
                .setRequired(false))
        .addBooleanOption(option => option
            .setName("banner")
            .setDescription("Whether or not to show the banner instead")
            .setRequired(false)),
    async execute(message) {
        const user = await message.options.getUser('user') || message.user
        await user.fetch(true)
        if (message.options.getBoolean("banner")) {
            // fetch user banner
            const embed = new MessageEmbed()
                .setTitle(`${user.username}'s Banner`)
                .setImage(user.bannerURL({dynamic: true, size: 2048}))
                .setColor('RANDOM')
            message.reply({embeds: [embed]})
        } else {
            const embed = new MessageEmbed()
                .setTitle(`${user.username}'s Avatar`)
                .setImage(user.displayAvatarURL({dynamic: true, size: 2048}))
                .setColor('WHITE')
            message.reply({embeds: [embed]})
        }
    }
}