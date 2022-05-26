const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {Util, MessageEmbed, Formatters, Modal, TextInputComponent, MessageActionRow} = require("discord.js");
const {ConvertDate, display_time} = require("../../structures/converters");
const {Reminder} = require("../../structures/tasks");
const {resolveAsChannel_Dm_Here} = require("../../structures/resolvers");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("remind")
        .setDescription("Sends a reminder to a user or channel")
        .addSubcommand(subcommand => subcommand
            .setName("create")
            .setDescription("Creates a reminder")
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
                .setColor('WHITE')
                .setFooter(`You have ${reminders.rows.length} reminders`)
            for (const reminder of reminders.rows) {
                const channel = message.client.channels.cache.get(reminder.destination)
                embed.addField(`Reminder ${Formatters.inlineCode(reminder.id)}: <t:${(Math.round(reminder.date.valueOf() / 1000))}:R>`, `${channel?.type === "GUILD_TEXT" ? Formatters.channelMention(channel.id) : Formatters.userMention(message.user.id)} - ${reminder.message} ${reminder.repeat ? `\nRepeats every ${reminder.assigned}` : ''}`)
            }
            await message.reply({embeds: [embed]})
        }
        else if (message.options.getSubcommand() === "delete") {
            const id = message.options.getString("id")
            await db.query("DELETE FROM remind WHERE id = $1 and member = $2", [id, message.user.id])
            const reminder_start = await new Reminder()
            await reminder_start.dispatch_reminder(message)
            await message.reply("Reminder deleted")
        } else if (message.options.getSubcommand() === "create") {
            await showModal()

            async function showModal() {
                const modal = new Modal()
                    .setCustomId('remindModal')
                    .setTitle('Create Reminder')

                const description = new TextInputComponent()
                    .setCustomId('description')
                    .setLabel('What is the reminder about?')
                    .setRequired(true)
                    .setStyle('SHORT')

                const duration = new TextInputComponent()
                    .setCustomId('duration')
                    .setLabel('How long should the reminder last?')
                    .setRequired(true)
                    .setStyle('SHORT')
                    .setPlaceholder('Example: 1d1h')

                modal.addComponents(new MessageActionRow().addComponents(description), new MessageActionRow().addComponents(duration))

                await message.showModal(modal)
            }

            const filter = (interaction) => interaction.customId === 'remindModal';
            message.awaitModalSubmit({ filter, time: 20000 })
                .then(async (modal) => {
                    const description = modal.fields.getTextInputValue('description')
                    const duration = modal.fields.getTextInputValue('duration')
                    const channel = resolveAsChannel_Dm_Here(message, message.options.getString("destination")) || message.channel
                    const repeats = message.options.getBoolean('repeats') || false
                    const reminder = new Reminder()

                    await modal.deferUpdate()
                    const time = await ConvertDate(duration)
                    if (time === null) {
                        await message.channel.send("Invalid duration")
                        return
                    } else if (time < 0) {
                        await message.channel.send("Duration must be in the future")
                        return
                    }

                    const delta = new Date(Date.now() + time * 1000)
                    const id = Math.random().toString(36).substr(2, 8)
                    if (repeats && time < 7200) {
                        await message.channel.send("To prevent spam in servers, repeating reminders must be at least 2 hours long")
                        return
                    }
                    await db.query("INSERT INTO remind (id, member, date, message, destination, repeat, assigned) VALUES ($1, $2, $3, $4, $5, $6, $7)", [id, message.user.id, delta, description, channel.id, repeats, new Date()])
                    await message.channel.send(`Ok, reminding you ${repeats ? "every" : "in"} ${display_time(time)} ${channel?.type === "GUILD_TEXT" ? `in ${Formatters.channelMention(channel.id)}` : `in DMs`} for ${Formatters.inlineCode(description)}`)
                    await reminder.dispatch_reminder(message.client)
                })
        }
        await db.release()
    }
}