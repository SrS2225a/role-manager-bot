const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {userPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("application")
        .setDescription("Manages the application settings")
        .addSubcommand(subcommand => subcommand
            .setName("channel")
            .setDescription("Sets the channel that applications should be sent to")
            .addChannelOption(channel => channel
                .setName("channel")
                .setDescription("The channel that applications are sent to")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("give")
            .setDescription("Sets up the role that is given to users when they apply")
            .addRoleOption(role => role
                .setName("role")
                .setDescription("The role that is given to users when an application is accepted")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("require")
            .setDescription("Sets up the role that is required to apply")
            .addRoleOption(role => role
                .setName("role")
                .setDescription("The role that is required to apply")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("accept")
            .setDescription("Sets up the role that is given to users when an application is accepted")
            .addStringOption(option => option
                .setName("message")
                .setDescription("The message that is sent to users when they accept the application")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("deny")
            .setDescription("The message to send to the user when the application is denied")
            .addStringOption(option => option
                .setName("message")
                .setDescription("The message to send to the user when the application is denied")
                .setRequired(true)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("question")
            .setDescription("Sets up the question that is asked to the user")
            .addStringOption(option => option
                .setName("question")
                .setDescription("The question that is asked to the user")
                .setRequired(true)
            )
            .addIntegerOption(option => option
                .setName("edit")
                .setDescription("Edits a question")
                .setRequired(false)
            )
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"])
        const db = await pool.connect()
        if (message.options.getSubcommand() === "question") {
            const result = await db.query("SELECT text FROM questions WHERE guild = $1 and text = $2 and type = $3", [message.guild.id, message.options.getOption('question'), 'question'])
            if (result.rowCount === 0) {
                const edit = message.options.getInteger('edit')
                if (edit === 0) {
                    await db.query("INSERT INTO questions(guild, text, type) VALUES($1, $2, $3)", [message.guild.id, message.options.getOption('question'), 'question'])
                    message.reply(`Set the application question to ${message.options.getString('question')}`)
                } else {
                    await db.query("UPDATE questions SET text = $1 WHERE guild = $2 and number = $3", [message.options.getOption('question'), message.guild.id, edit])
                    message.reply(`Edited the application question to ${message.options.getString('edit')}`)
                }
            } else {
                await db.query("DELETE FROM questions WHERE guild = $1 and text = $2 and type = $3", [message.guild.id, message.options.getOption('question'), 'question'])
                message.reply(`Set the application question to ${message.options.getString('question')}`)
            }
        } else if (message.options.getSubcommand() === "give") {
            const result = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'give'])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO questions(guild, text, type) VALUES($1, $2, $3)", [message.guild.id, message.options.getRole('role').id, 'give'])
                message.reply(`Set the application give to ${message.options.getRole('give').name}`)
            } else {
                await db.query("DELETE FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'give'])
                message.reply(`Set the application give to ${message.options.getRole('give').name}`)
            }
        } else if (message.options.getSubcommand() === "require") {
            const result = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'require'])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO questions(guild, text, type) VALUES($1, $2, $3)", [message.guild.id, message.options.getRole('role').id, 'require'])
                message.reply(`Set the application require to ${message.options.getRole('role').name}`)
            } else {
                await db.query("DELETE FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'require'])
                message.reply(`Set the application require to ${message.options.getRole('role').name}`)
            }
        } else if (message.options.getSubcommand() === "channel") {
            const result = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'channel'])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO questions(guild, text, type) VALUES($1, $2, $3)", [message.guild.id, message.options.getChannel('channel').id, 'channel'])
                message.reply(`Set the application channel to ${message.options.getChannel('channel').name}`)
            } else {
                await db.query("DELETE FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'channel'])
                message.reply(`Set the application channel to ${message.options.getChannel('channel').name}`)
            }
        } else if (message.options.getSubcommand() === "accept") {
            const result = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'accept'])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO questions(guild, text, type) VALUES($1, $2, $3)", [message.guild.id, message.options.getString('message'), 'accept'])
                message.reply(`Set the application accept to ${message.options.getString('message')}`)
            } else {
                await db.query("DELETE FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'accept'])
                message.reply(`Set the application accept to ${message.options.getString('message')}`)
            }
        } else if (message.options.getSubcommand() === "deny") {
            const result = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'deny'])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO questions(guild, text, type) VALUES($1, $2, $3)", [message.guild.id, message.options.getString('message'), 'deny'])
                message.reply(`Set the application deny to ${message.options.getString('message')}`)
            } else {
                await db.query("DELETE FROM questions WHERE guild = $1 and type = $2", [message.guild.id, 'deny'])
                message.reply(`Set the application deny to ${message.options.getString('message')}`)
            }
        }
        await db.release()
    }
}