const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {ConvertDate} = require("../../structures/converters");
const {userPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("autoposition")
        .setDescription("Adds roles based on someones account join or creation date")
        .addSubcommand(subcommand => subcommand
            .setName("join")
            .setDescription("Sets if the role should be added by join date")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to add")
                .setRequired(true))
            .addStringOption(option => option
                .setName("delay")
                .setDescription("How long the account should be in the server for before getting the role")
                .setRequired(true)))
        .addSubcommand(subcommand => subcommand
            .setName("create")
            .setDescription("Sets if the role should be added by creation date")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to add")
                .setRequired(true))
            .addStringOption(option => option
                .setName("delay")
                .setDescription("How long the account should of existed before getting the role")
                .setRequired(true))),
    async execute(message) {
        const db = await pool.connect()
        userPermissions(message, ["MANAGE_ROLES"])
        if (message.options.getSubcommand() === "create") {
            const role = await message.options.getRole("role")
            const date = message.options.getString("delay") || undefined
            const result = await db.query("SELECT role FROM roles WHERE guild = $1 and type = $2 and role = $3", [message.guildId, 'create', role.id])
            if (!result.rows.length) {
                const time = ConvertDate(date)
                if (time < 1) {
                    await message.reply('Times cannot be in the past!')
                    return
                }
                await db.query("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", [message.guildId, time, role.id, 'create'])
                await message.reply("Auto Position Set Successfully!")
            } else {
                await db.query("DELETE FROM roles WHERE guild = $1 and role = $2 and type = $3", [message.guildId, role.id, 'create'])
                await message.reply("Auto Position Removed Successfully!")
            }
        } else if (message.options.getSubcommand() === "join") {
            const role = await message.options.getRole("role")
            const date = message.options.getString("delay") || undefined
            const result = await db.query("SELECT role FROM roles WHERE guild = $1 and type = $2 and role = $3", [message.guildId, 'join', role.id])
            if (!result.rows.length) {
                const time = ConvertDate(date)
                if (time < 1) {
                    await message.reply('Times cannot be in the past!')
                    return
                }
                await db.query("INSERT INTO roles(guild, member, role, type) VALUES($1, $2, $3, $4)", [message.guildId, time, role.id, 'join'])
                await message.reply("Auto Position Set Successfully!")
            } else {
                await db.query("DELETE FROM roles WHERE guild = $1 and role = $2 and type = $3", [message.guildId, role.id, 'join'])
                await message.reply("Auto Position Removed Successfully!")
            }
        }
        await db.release()
    }
}