const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("flags")
        .setDescription("Sets the flag to give")
        .addRoleOption(role => role
            .setName("role")
            .setDescription("The role to give automatically depending on what flags the user has")
            .setRequired(true)
        )
        .addStringOption(option => option
            .setName("flag")
            .setDescription("The flag to check for")
            .setRequired(true)
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"]);
        const db = await pool.connect();
        const flags = ["staff", "partner", "hypesquad", "bug_hunter", "hypesquad_bravery", "hypesquad_brilliance", "hypesquad_balance", "early_supporter", "system", "bug_hunter_level_2", "verified_bot", "verified_bot_developer"].map(flag => flag.toUpperCase());
        const result = await db.query("SELECT role FROM flags WHERE guild = $1 and role = $2 and flag = $3", [message.guild.id, message.options.getRole('role').id, message.options.getString('flag')])
        if (flags.includes(message.options.getString('flag').toUpperCase())) {
            if (result.rowCount === 0) {
                await db.query("INSERT INTO flags(guild, role, flag) VALUES($1, $2, $3)", [message.guild.id, message.options.getRole('role').id, message.options.getString('flag')])
                message.reply(`Set the flag ${message.options.getString('flag')} to ${message.options.getRole('role').name}`)
            } else {
                await db.query("DELETE FROM flags WHERE role = $1 and guild = $2 and flag = $3", [message.options.getRole('role').id, message.guild.id, message.options.getString('flag')])
                message.reply(`Removed the flag ${message.options.getString('flag')} from ${message.options.getRole('role').name}`)
            }
        } else {
            message.reply(`The flag ${message.options.getString('flag')} is not supported`)
        }
        await db.release();
    }
}