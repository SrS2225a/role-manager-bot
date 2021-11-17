const {MessageEmbed, Formatters} = require("discord.js");
const {SlashCommandBuilder} = require("@discordjs/builders");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("userinfo")
        .setDescription("Shows info about a user")
        .addUserOption(option =>
            option.setName("member")
                .setDescription("The user to get information about")
                .setRequired(false)),
    async execute(message) {
        const user = await message.options.getMember('member') || message.member
        await user.user.fetch(true)
        let userPermissions = []
        const roles = user.roles.cache
            .sort((a, b) => b.position - a.position)
            .map(role => role.toString())
            .slice(0, -1)
        user.permissions
        for (const userPerms of user.permissions.toArray()) {
            // this method of comparing const rolePerms will not work properly unless we put some random string at the beginning for whatever reason
            if (["ahklfewkawejhfk;", "STREAM", "CONNECT", "SPEAK", "READ_MESSAGES", "SEND_MESSAGES", "EMBED_LINKS", "ATTACH_FILES", "USE_VOICE_ACTIVATION", "READ_MESSAGE_HISTORY", "VIEW_CHANNEL", "EXTERNAL_MESSAGES", "ADD_REACTIONS", "PRIORITY_SPEAKER", "CHANGE_NICKNAME"].indexOf(userPerms) >= 0) {
                userPermissions.push(userPerms)
            }
            if (userPerms === "ADMINISTRATOR") {
                userPermissions = []
                userPermissions.push(userPerms)
                break
            }
        }
        const joinPos = message.guild.members.cache
            .sort((a, b) => a.joinedAt || b.createdAt)
            .map(member => member.id)
            .indexOf(user.id)

        const embed = new MessageEmbed()
            .setTitle("User Info")
            .setColor(user.displayColor)
            .setThumbnail(user.user.displayAvatarURL( {dynamic: true} ))
            .setImage(user.user.bannerURL({dynamic: true, size: 512}))
            .addFields(
                {name: "Name", value: Formatters.codeBlock(user.user.username + '#' + user.user.discriminator), inline: true},
                {name: "User ID", value: Formatters.codeBlock(user.id), inline: true},
                {name: "Key Permissions", value: Formatters.codeBlock(userPermissions.join(', ')), inline: false},
                {name: "Created At", value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {dateStyle: 'long', timeStyle: 'long'}).format(user.user.createdAt)), inline: false},
                {name: "Joined At", value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {dateStyle: 'long', timeStyle: 'long'}).format(user.joinedAt)), inline: false},
                {name: "Booster", value: Formatters.codeBlock((user.premium_since) ? user.premium_since:"False"), inline: false},
                {name: "Public Flags", value: Formatters.codeBlock(user.public_flags?.toArray().join(', ') || "None"), inline: false},
                {name: "Join Position", value: Formatters.codeBlock(joinPos), inline: true},
                {name: "Color", value: Formatters.codeBlock(user.displayHexColor), inline: true},
                {name: "Bot", value: Formatters.codeBlock(user.user.bot), inline: true},
                {name: `Roles [${roles.length}]`, value: roles.join(" "), inline: false}

            )
        await message.reply({embeds: [embed]});
    }
}