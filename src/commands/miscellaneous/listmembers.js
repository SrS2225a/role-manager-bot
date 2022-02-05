const {SlashCommandBuilder} = require("@discordjs/builders");
const {paginator} = require("../../structures/paginators");
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
        const flag = await message.options.getBoolean("has") || true
        const result = flag ? message.guild.members.cache.filter(member => member.roles.cache.has(role.id)) : message.guild.members.cache.filter(member => !member.roles.cache.has(role.id))
        if (result.size === 0) return message.reply("No members found")
        const pages = new paginator(message, result.map(member => member.user.tag))
        pages.show_points = true
        await pages.paginate()
    }
}