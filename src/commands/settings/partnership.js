const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("partnership")
        .setDescription("Sets what role to give based on how many partners were completed")
        .addChannelOption(channel => channel
            .setName("channel")
            .setDescription("The channel that the partnership channel is in")
            .setRequired(true)
        )
        .addRoleOption(role => role
            .setName("required")
            .setDescription("The role that is required to be in the partnership channel")
            .setRequired(true)
        )
        .addRoleOption(role => role
            .setName("role")
            .setDescription("The role to give based on how many partners were completed")
            .setRequired(false)
        )
        .addIntegerOption(option => option
            .setName("amount")
            .setDescription("The amount of partners that must be completed before getting the reward")
            .setRequired(false)
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"]);
        const db = await pool.getConnection();
        const result = await db.query("SELECT type FROM leveling WHERE guild = $1 and system = $2 and type = $3 and level = $4", [message.guild.id, 'partners', message.options.getChannel('channel')?.id, message.options.getInteger("amount")])
        if (result.rowCount === 0) {
            await db.query("INSERT INTO leveling(guild, system, level, difficulty, type, role) VALUES($1, $2, $3,$4, $5,$6)", [message.guild.id, 'partners', message.options.getInteger("amount"), message.options.getRole("required")?.id, message.options.getChannel("channel")?.id, message.options.getRole('role')?.id || null])
            message.reply(`Set the partnership channel to ${message.options.getChannel('channel').name}`)
        } else {
            await db.query("DELETE FROM leveling WHERE guild = $1 and system = $2 and type = $3 and level = $4", [message.guild.id, 'partners', message.options.getChannel('channel')?.id, message.options.getInteger("amount")])
            message.reply(`Removed the partnership channel from ${message.options.getChannel('channel').name}`)
        }
        await db.release();
    }
}