const {SlashCommandBuilder} = require("@discordjs/builders");
const {PermissionsBitField, EmbedBuilder, Colors} = require("discord.js");
const {clientPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("avatar")
        .setDescription("Enlarges a members avatar")
        .addSubcommand(subcommand =>
            subcommand
                .setName("default")
                .setDescription("Shows the default avatar")
                .addUserOption(option =>
                    option
                        .setName("user")
                        .setRequired(false)
                        .setDescription("The user to show the avatar of")
                ))
        .addSubcommand(subcommand =>
            // show the avatar of the users server avatar
            subcommand
                .setName("server")
                .setDescription("Shows the server avatar")
                .addUserOption(option =>
                    option
                        .setName("user")
                        .setRequired(false)
                        .setDescription("The user to show the avatar of")
                ))
        .addSubcommand(subcommand =>
            // show the avatar of the users avatar
            subcommand
                .setName("banner")
                .setDescription("Shows the banner avatar")
                .addUserOption(option =>
                    option
                        .setName("user")
                        .setRequired(false)
                        .setDescription("The user to show the banner of")
                )),
    async execute(message) {
        // turn the boolean option into a subcommand with the additional option of getting the users server avatar
        clientPermissions(message, [PermissionsBitField.Flags.EmbedLinks]);
        if (message.options.getSubcommand() === "default") {
            const user = await message.options.getUser('user') || message.user
            await user.fetch(true)
            const embed = new EmbedBuilder()
                .setTitle(`${user.username}'s Avatar`)
                .setImage(user.displayAvatarURL({format: "png", dynamic: true, size: 2048}))
                .setColor(Colors.White)
            await message.reply({embeds: [embed]})
        } else if (message.options.getSubcommand() === "server") {
            // get the member
            const user = await message.options.getUser('user') || message.member
            const embed = new EmbedBuilder()
                .setTitle(`${user.username}'s Server Avatar`)
                .setImage(user.displayAvatarURL({format: "png", dynamic: true, size: 2048}))
                .setColor(Colors.White)
            await message.reply({embeds: [embed]})
        } else if (message.options.getSubcommand() === "banner") {
            const user = await message.options.getUser('user') || message.user
            await user.fetch(true)
            const embed = new EmbedBuilder()
                .setTitle(`${user.username}'s Banner`)
                .setImage(user.bannerURL({format: "png", dynamic: true, size: 2048}))
                .setColor(Colors.White)
            await message.reply({embeds: [embed]})
        }
    }
}