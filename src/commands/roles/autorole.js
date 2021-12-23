const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {ConvertDate} = require("../../structures/converters");
const {userPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("autorole")
        .setDescription("Sets what role will be given or removed automatically upon the user joining the guild")
        .addSubcommand(subcommand => subcommand
            .setName("add")
            .setDescription("Adds a role upon the user joining the server")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to add")
                .setRequired(true))
            .addStringOption(option => option
                .setName("delay")
                .setDescription("Optional delay for when the role should be added upon the user joining the server")
                .setRequired(false)))
        .addSubcommand(subcommand => subcommand
            .setName("remove")
            .setDescription("Removes a role upon the user joining the server")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to remove")
                .setRequired(true))
            .addStringOption(option => option
                .setName("delay")
                .setDescription("Optional delay for when the role should be removed upon the user joining the server")
                .setRequired(false))),
    async execute(message) {
        const db = await pool.connect()
        userPermissions(message, ["MANAGE_ROLES"]);
        if (message.options.getSubcommand() === "add") {
            const role = await message.options.getRole("role")
            const date = message.options.getString("delay")
            const result = await db.query("SELECT role FROM roles WHERE guild = $1 and type = $2 and role = $3", [message.guildId, 'add', role.id])
            if (!result.rows.length) {
                const time = ConvertDate(date)
                if (time < 0) {
                    await message.reply('Times cannot be in the past!')
                    return
                }
                await db.query("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", [message.guildId, time, role.id, 'add'])
                await message.reply("Auto Position Set Successfully!")
            } else {
                await db.query("DELETE FROM roles WHERE guild = $1 and role = $2 and type = $3", [message.guildId, role.id, 'add'])
                await message.reply("Auto Position Removed Successfully!")
            }
        } else if (message.options.getSubcommand() === "remove") {
            const role = await message.options.getRole("role")
            const date = message.options.getString("delay")
            const result = await db.query("SELECT role FROM roles WHERE guild = $1 and type = $2 and role = $3", [message.guildId, 'remove', role.id])
            if (!result.rows.length) {
                const time = new ConvertDate(date).time || 0
                if (time < 0) {
                    await message.reply('Times cannot be in the past!')
                    return
                }
                await db.query("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", [message.guildId, time, role.id, 'remove'])
                await message.reply("Auto Position Set Successfully!")
            } else {
                await db.query("DELETE FROM roles WHERE guild = $1 and role = $2 and type = $3", [message.guildId, role.id, 'remove'])
                await message.reply("Auto Position Removed Successfully!")
            }
        }
        await db.release()
    }
}