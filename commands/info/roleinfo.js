const {SlashCommandBuilder} = require("@discordjs/builders");
const {Formatters, MessageEmbed} = require("discord.js");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("roleinfo")
        .setDescription("Shows info about a role")
        .addRoleOption(option =>
            option.setName("role")
                .setDescription("The role to get information about")
                .setRequired(true)),
    async execute(message) {
        const role = await message.options.getRole('role')
        let rolePermissions = []
        for (const rolePerms of role.permissions.toArray()) {
            // this method of comparing const rolePerms will not work properly unless we put some random string at the beginning for whatever reason
            if (["ahklfewkawejhfk;", "STREAM", "CONNECT", "SPEAK", "READ_MESSAGES", "SEND_MESSAGES", "EMBED_LINKS", "ATTACH_FILES", "USE_VOICE_ACTIVATION", "READ_MESSAGE_HISTORY", "VIEW_CHANNEL", "EXTERNAL_MESSAGES", "ADD_REACTIONS", "PRIORITY_SPEAKER", "CHANGE_NICKNAME"].indexOf(rolePerms) <= 0) {
                rolePermissions.push(rolePerms)
            }
            if (rolePerms === "ADMINISTRATOR") {
                rolePermissions = []
                rolePermissions.push(rolePerms)
                break
            }
        }
        const embed = new MessageEmbed()
            .setTitle("Role Info")
            .setColor(role.color)
            .addFields({name: "Role Name", value: Formatters.codeBlock(role.name), inline: true},
                {name: "Role ID", value: Formatters.codeBlock(role.id), inline: true},
                {name: "Created At", value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {dateStyle: 'long', timeStyle: 'long'}).format(role.createdAt))},
                {name: "Color", value: Formatters.codeBlock(role.hexColor), inline: true},
                {name: "Position", value: Formatters.codeBlock(role.position), inline: true},
                {name: "Has Role", value: Formatters.codeBlock(role.members.size), inline: true},
                {name: "Hoisted", value: Formatters.codeBlock(role.hoist), inline: true},
                {name: "Integrated", value: Formatters.codeBlock(role.managed), inline: true},
                {name: "Mentionable", value: Formatters.codeBlock(role.mentionable), inline: true},
                {name: "Key Permissions", value: Formatters.codeBlock(rolePermissions.join(', '))}
            )
        await message.reply({embeds: [embed]})
    }
}