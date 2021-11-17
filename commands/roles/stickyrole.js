const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("stickyrole")
        .setDescription('Sets what role will "stick" to the user upon getting the set role')
        .addRoleOption(option => option
            .setName("role")
            .setDescription("The role to set the sticky role to")
            .setRequired(true)),
    async execute(message) {
        const db = await pool.connect()
        const role = message.options.getRole("role")
        const result = await db.query("SELECT role FROM reward WHERE guild = $1 and role = $2 and type = $3", [message.guild.id, role.id, "sticky"])
        if (!result.rows.length) {
            await db.query("INSERT INTO reward (guild, role, type) VALUES ($1, $2, $3)", [message.guild.id, role.id, "sticky"])
            message.reply(`Sticky role set to ${role.name}`)
        } else {
            await db.query("DELETE FROM reward WHERE guild = $1 and role = $2 and type = $3", [message.guild.id, role.id, "sticky"])
            message.reply(`Sticky role removed from ${role.name}`)
        }
        await db.release()
    }
}