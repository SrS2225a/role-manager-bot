const {SlashCommandBuilder} = require("@discordjs/builders");
const {paginator} = require("../../structures/paginators");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("listroles")
        .setDescription("Shows a list of all the roles in the server"),
    async execute(message) {
        const roles = message.guild.roles.cache
        const paginate = new paginator(message, roles.map(role => role.name))
        paginate.show_points=true
        await paginate.paginate()
    }
}