const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {userPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("voicerole")
        .setDescription("Modifies the role that is given to users when they join a voice channel")
        .addRoleOption(role => role
            .setName("role")
            .setDescription("The role that is given to users when they join a voice channel")
            .setRequired(true)
        )
        .addChannelOption(channel => channel
            .setName("channel")
            .setDescription("The voice channel that the role is given to users when they join")
            .setRequired(true)),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"])
        const db = await pool.connect()
        const result = await db.query("SELECT role FROM reward WHERE guild = $1 and channel = $2 and role = $3 and type = $4", [message.guild.id, message.options.getChannel('channel').id, message.options.getRole('role').id, 'voice'])
        if (result.rowCount === 0) {
            await db.query("INSERT INTO reward(guild, channel, role, type) VALUES($1, $2, $3, $4)", [message.guild.id, message.options.getChannel('channel').id, message.options.getRole('role').id, 'voice'])
            message.reply(`Set the voice role to ${message.options.getRole('role').name}`)
        } else {
            await db.query("DELETE FROM reward WHERE guild = $1 and channel = $2 and role = $3 and type = $4", [message.guild.id, message.options.getChannel('channel').id, message.options.getRole('role').id, 'voice'])
            message.reply(`Set the voice role to ${message.options.getRole('role').name}`)
        }
        await db.release()
    }

}