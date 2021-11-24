const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
const {resolveAsChannel_Role} = require("../../structures/resolvers");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("leveling")
        .setDescription("Sets the leveling system")
        .addSubcommand(subcommand => subcommand
            .setName("blacklist")
            .setDescription("Sets the blacklist for the leveling system")
            .addStringOption(option => option
                .setName("main")
                .setDescription("The role text, or voice channel to blacklist")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("rank")
            .setDescription("Sets the rank role for the leveling system")
            .addRoleOption(role => role
                .setName("role")
                .setDescription("The role to give when leveling up")
                .setRequired(true)
            )
            .addIntegerOption(option => option
                .setName("level")
                .setDescription("The level to give the role")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("weight")
            .setDescription("Sets the weight of the leveling system")
            .addIntegerOption(option => option
                .setName("weight")
                .setDescription("The weight to set")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("behavior")
            .setDescription("Sets if level roles should \"stack\" on each other")
            .addBooleanOption(options => options
                .setName("type")
                .setDescription("Whether or not to stack the roles")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("multiplier")
            .setDescription("Sets the multiplier for the leveling system")
            .addStringOption(option => option
                .setName("type")
                .setDescription("The text channel, voice or role to set the multiplier to")
                .setRequired(true)
            )
            .addIntegerOption(option => option
                .setName("multi")
                .setDescription("The multiplier to set")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("tor")
            .setDescription("Allows you to add support for member of the day, week, or month")
            .addStringOption(option => option
                .setName("type")
                .addChoices([['day', 'day'], ['week', 'week'], ['month', 'month']])
                .setDescription("The type of tor to set")
                .setRequired(true)
            )
            .addRoleOption(role => role
                .setName("role")
                .setDescription("The role to give when the tor is reached")
                .setRequired(true)
            )
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"]);
        const db = await pool.connect();
        if (message.options.getSubcommand() === "blacklist") {
            const main = resolveAsChannel_Role(message.options.getString('main'))
            const result = await db.query("SELECT type FROM leveling WHERE guild = $1 and system = $2 and role = $3", [message.guild.id, 'blacklist', main.id])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO leveling(guild, system, role) VALUES($1, $2, $3)", [message.guild.id, 'blacklist', main.id])
                message.reply(`Set the blacklist channel to ${main.name}`)
            } else {
                await db.query("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3", [message.guild.id, 'blacklist', main.id])
                message.reply(`Set the blacklist channel to ${main.name}`)
            }
        } else if (message.options.getSubcommand() === "multiplier") {
            const main = resolveAsChannel_Role(message.options.getString('main'))
            const result = await db.query("SELECT type FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", [message.guild.id, 'multiplier', main.id, message.options.getInteger("multiply")])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO leveling(guild, system, role, difficulty) VALUES($1, $2, $3, $4)", [message.guild.id, 'multiplier', main.id, message.options.getInteger("multiply")])
                message.reply(`Set the multiplier channel to ${main.name}`)
            } else {
                await db.query("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", [message.guild.id, 'multiplier', main.id, message.options.getInteger("multiply")])
                message.reply(`Set the multiplier channel to ${main.name}`)
            }
        } else if (message.options.getSubcommand() === "weight") {
            const result = await db.query("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", [message.guild.id, 'weight'])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO leveling(guild, system, difficulty) VALUES($1, $2, $3)", [message.guild.id, 'weight', message.options.getInteger('weight')])
                message.reply(`Set the weight to ${message.options.getInteger('weight')}`)
            } else {
                await db.query("DELETE FROM leveling WHERE guild = $1 and system = $2", [message.guild.id, 'weight', message.options.getInteger('weight')])
                message.reply(`Set the weight to ${message.options.getInteger('weight')}`)
            }
        } else if (message.options.getSubcommand() === "behavior") {
            const result = await db.query("SELECT type FROM leveling WHERE guild = $1 and system = $2 and type = $3", [message.guild.id, 'behavior', message.options.getBoolean('type')])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO leveling(guild, system, type) VALUES($1, $2, $3)", [message.guild.id, 'behavior', message.options.getBoolean('type')])
                message.reply(`Set the behavior to ${message.options.getBoolean('type')}`)
            } else {
                await db.query("DELETE FROM leveling WHERE guild = $1 and system = $2 and type = $3", [message.guild.id, 'behavior', message.options.getBoolean('type')])
                message.reply(`Set the behavior to ${message.options.getBoolean('type')}`)
            }
        } else if (message.options.getSubcommand() === "rank") {
            const result = await db.query("SELECT type FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4", [message.guild.id, 'rank', message.options.getRole('role').id, message.options.getInteger('level')])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO leveling(guild, system, role, level) VALUES($1, $2, $3, $4)", [message.guild.id, 'rank', message.options.getRole('role').id, message.options.getInteger('level')])
                message.reply(`Set the rank to ${message.options.getRole('role').name} at level ${message.options.getInteger('level')}`)
            } else {
                await db.query("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4", [message.guild.id, 'rank', message.options.getRole('role').id, message.options.getInteger('level')])
                message.reply(`Set the rank to ${message.options.getRole('role').name} at level ${message.options.getInteger('level')}`)
            }
        } else if (message.options.getSubcommand() === "tor") {
            const result = await db.query("SELECT role FROM leveling WHERE guild = $1 and system = $2 and type = $3", [message.guild.id, 'tor', message.options.getString('type')])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO leveling(guild, system, role, type) VALUES($1, $2, $3, $4)", [message.guild.id, 'tor', message.options.getRole('role').id, message.options.getString('type')])
                message.reply(`Set the tor to ${message.options.getRole('role').name}`)
            } else {
                await db.query("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and type = $4", [message.guild.id, 'tor', message.options.getRole('role').id, message.options.getString('type')])
                message.reply(`Set the tor to ${message.options.getRole('role').name}`)
            }
        }
        await db.release()
    }
}