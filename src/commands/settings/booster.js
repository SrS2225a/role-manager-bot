const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("booster")
        .setDescription("Sets up the role that is given to users when they are a booster")
        .addRoleOption(role => role
            .setName("role")
            .setDescription("The role that is given to users when they are a booster")
            .setRequired(true)
        )
        .addIntegerOption(option => option
            .setName("amount")
            .setDescription("The amount of boosters required to get the role")
            .setRequired(true)
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"]);
        const db = await pool.connect();
        const result = await db.query("SELECT role FROM boost WHERE guild = $1 and role = $2 and date = $3 and type = $4", [message.guild.id, message.options.getRole('role').id, message.options.getInteger('day'), 'booster'])
        if (result.rowCount === 0) {
            await db.query("INSERT INTO boost(guild, role, date, type) VALUES($1, $2, $3, $4)", [message.guild.id, message.options.getRole('role').id, message.options.getInteger('day'), 'booster'])
            message.reply(`Set the booster to ${message.options.getRole('role').id} for ${message.options.getInteger('day')} days`)
        } else {
            await db.query("DELETE FROM boost WHERE guild = $1 and role = $2 and date = $3 and type = $4", [message.guild.id, message.options.getRole('role').id, message.options.getInteger('day'), 'booster'])
            message.reply(`Set the booster to ${message.options.getRole('role').name} for ${message.options.getInteger('day')} days`)
        }
        await db.release();
    }
}