const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("reward")
        .setDescription("Sets what role to give when someone is invited")
        .addRoleOption(role => role
            .setName("role")
            .setDescription("The role to give based on how many users were invited by the inviter")
            .setRequired(true)
        )
        .addIntegerOption(option => option
            .setName("amount")
            .setDescription("The amount of users that need to be invited before getting the reward")
            .setRequired(true)
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"]);
        const db = await pool.connect();
        const result = await db.query("SELECT role FROM boost WHERE guild = $1 and role = $2 and date = $3 and type = $4", [message.guild.id, message.options.getRole('inviter').id, message.options.getInteger('day'), 'inviter'])
        if (result.rowCount === 0) {
            await db.query("INSERT INTO boost(guild, role, date, type) VALUES($1, $2, $3, $4)", [message.guild.id, message.options.getRole('inviter').id, message.options.getInteger('day'), 'inviter'])
            message.reply(`Set the inviter to ${message.options.getRole('inviter').id} for ${message.options.getInteger('day')} days`)
        } else {
            await db.query("DELETE FROM boost WHERE guild = $1 and role = $2 and date = $3 and type = $4", [message.guild.id, message.options.getRole('inviter').id, message.options.getInteger('day'), 'inviter'])
            message.reply(`Set the inviter to ${message.options.getRole('inviter').name} for ${message.options.getInteger('day')} days`)
        }
        await db.release()
    }
}