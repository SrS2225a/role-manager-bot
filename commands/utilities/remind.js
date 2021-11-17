const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {Util, MessageEmbed, Formatters} = require("discord.js");
const {ConvertDate, display_time} = require("../../structures/converters");
const {Reminder} = require("../../structures/tasks");
const {resolveAsChannel_Dm_Here} = require("../../structures/resolvers");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("remind")
        .setDescription("Sends a reminder to a user or channel.")
        .addSubcommand(subcommand => subcommand
            .setName("create")
            .setDescription("Creates a reminder")
            .addStringOption(option => option
                .setName("description")
                .setDescription("The description of the reminder")
                .setRequired(true))
            .addStringOption(option => option
                .setName("duration")
                .setDescription("The duration of the reminder")
                .setRequired(true))
            .addStringOption(option => option
                .setName("destination")
                .setDescription("The destination of the reminder")
                .setRequired(false))
            .addBooleanOption(option => option
                .setName("repeats")
                .setDescription("The number of times to repeat the reminder")
                .setRequired(false)))
        .addSubcommand(subcommand => subcommand
            .setName("list")
            .setDescription("Lists all your reminders"))
        .addSubcommand(subcommand => subcommand
            .setName("delete")
            .setDescription("Deletes a reminder")
            .addStringOption(option => option
                .setName("id")
                .setDescription("The id of the reminder")
                .setRequired(true))),
    async execute(message) {
        const db = await pool.connect()
        if (message.options.getSubcommand() === "list") {
            const reminders = await db.query("SELECT * FROM remind WHERE member = $1", [message.user.id])
            if (reminders.rowCount === 0) {
                await message.reply("You have no reminders")
                return
            }
            const embed = new MessageEmbed()
                .setTitle("Reminders")
                .setColor(0x00FF00)
                .setFooter(`You have ${reminders.rows.length} reminders`)
            for (const reminder of reminders.rows) {
                const channel = message.client.channels.cache.get(reminder.destination) || await message.client.channels.fetch(reminder.destination)
                embed.addField(`Reminder ${Formatters.inlineCode(reminder.id)}: <t:${(Math.round(reminder.date.valueOf() / 1000))}:R>`, `${channel ? Formatters.channelMention(channel.id) : Formatters.userMention(message.user.id)} - ${reminder.message} ${reminder.repeat ? `\nRepeats every ${reminder.assigned}` : ''}`)
            }
            await message.reply({embeds: [embed]})
        }
        else if (message.options.getSubcommand() === "delete") {
            const id = message.options.getString("id")
            await db.query("DELETE FROM remind WHERE id = $1 and member = $2", [id, message.user.id])
            const reminder_start = new Reminder()
            await reminder_start.dispatch_reminder(message)
            await message.reply("Reminder deleted")
        } else if (message.options.getSubcommand() === "create") {
            const time = ConvertDate(message.options.getString("duration"))
            if (time === null) {
                await message.reply("Invalid duration")
                return
            } else if (time < 0) {
                await message.reply("Duration must be in the future")
                return
            }
            const description = message.options.getString("description")
            const channel = resolveAsChannel_Dm_Here(message, message.options.getString("destination")) || message.channel
            const delta = new Date(Date.now() + time * 1000)
            const id = Math.random().toString(36).substr(2, 8)
            const repeat = message.options.getBoolean("repeats") || false
            if (repeat && time < 7200) {
                await message.reply("Repeating reminders must be at least 2 hours")
                return
            }
            await db.query("INSERT INTO remind (id, member, date, message, destination, repeat, assigned) VALUES ($1, $2, $3, $4, $5, $6, $7)", [id, message.user.id, delta, description, channel.id, repeat, new Date()])
            await message.reply(`Ok, reminding you ${repeat ? "every": "in"} ${display_time(time)} about: **${Util.removeMentions(description)}**`)
            await new Reminder().dispatch_reminder(message.client)
        }
        await db.release()
    }
}