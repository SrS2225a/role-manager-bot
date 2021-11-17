const {SlashCommandBuilder} = require("@discordjs/builders");
const {paginator} = require("../../structures/paginator");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("listmembers")
        .setDescription("Lists members by a role or not")
        .addRoleOption(option =>
        option.setName("role")
            .setDescription("The role to list members under")
            .setRequired(true))
        .addBooleanOption(option =>
        option.setName("has")
            .setDescription("Lists if members should be listed that dont have the role")
            .setRequired(false)),
    async execute(message) {
        const role = await message.options.getRole("role")
        const flag = await message.options.getBoolean("has") || false
        const pages = flag ? new paginator(message, role.members.map(member => member.user.username + "#" + member.user.discriminator)) :  new paginator(message, !role.members.map(member => member.user.username + "#" + member.user.discriminator))
        pages.show_points = true
        await pages.paginate()
    }
}