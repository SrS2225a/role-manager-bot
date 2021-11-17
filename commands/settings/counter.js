const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
const {ConvertDate} = require("../../structures/converters");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("counter")
        .setDescription("Modifies the counter channel")
        .addChannelOption(channel => channel
            .setName("channel")
            .setDescription("The channel that the counter should be in")
            .setRequired(true)
        )
        .addRoleOption(role => role
            .setName("role")
            .setDescription("The role that is given to users when they miss the next number")
            .setRequired(false)
        )
        .addStringOption(option => option
            .setName("delay")
            .setDescription("How long the delay should be before removing the role")
            .setRequired(false)
        )
        .addBooleanOption(option => option
            .setName("count")
            .setDescription("Whether or not the counter should be enabled")
            .setRequired(false)
        ),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"])
        const db = await pool.connect()
        const result = await db.query("SELECT channel FROM count WHERE guild = $1 and channel = $2", [message.guild.id, message.options.getChannel('channel').id])
        if (result.rowCount === 0) {
            await db.query("INSERT INTO count(guild, channel, role, count, delay, number) VALUES($1, $2, $3, $4, $5, 1)", [message.guild.id, message.options.getChannel('channel').id, message.options.getRole('role')?.id, message.options.getBoolean('count'), ConvertDate(message.options.getString('delay'))])
            message.reply(`Set the counter to ${message.options.getChannel("channel").name}`)
        } else {
            await db.query("DELETE FROM count WHERE guild = $1 and channel = $2", [message.guild.id, message.options.getOption('channel').id])
            message.reply(`Set the counter to ${message.options.getChannel("channel").name}`)
        }
        await db.release()
    }
}