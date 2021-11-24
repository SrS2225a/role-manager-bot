const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("overwrite")
        .setDescription("Sets if channel overwrites should be given back if the user rejoins the server")
        .addChannelOption(channel => channel
            .setName("channel")
            .setDescription("The channel to set the overwrite for")
            .setRequired(true)
        )
        .addRoleOption(role => role
            .setName("role")
            .setDescription("The role to set the overwrite for")
            .setRequired(true)
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"]);
        const db = await pool.connect();
        const result = await db.query("SELECT role FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", [message.guild.id, message.options.getRole('role').id, message.options.getChannel('channel').id, 'overwrite'])
        if (result.rowCount === 0) {
            await db.query("INSERT INTO roles(guild, role, member, type) VALUES($1, $2, $3, $4)", [message.guild.id, message.options.getRole('role').id, message.options.getChannel('channel').id, 'overwrite'])
            message.reply(`Set the overwrite to ${message.options.getRole('role').name} for ${message.options.getChannel('channel').name}`)
        } else {
            await db.query("DELETE FROM roles WHERE guild = $1 and role = $2 and member = $3 and type = $4", [message.guild.id, message.options.getRole('role').id, message.options.getChannel('channel').id, 'overwrite'])
            message.reply(`Removed the overwrite to ${message.options.getRole('role').name} for ${message.options.getChannel('channel').name}`)
        }
        await db.release()
    }
}