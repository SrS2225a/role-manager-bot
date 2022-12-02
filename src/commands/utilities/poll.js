const {SlashCommandBuilder} = require("@discordjs/builders");
const {ConvertDate} = require("../../structures/converters");
const {MessageEmbed, Modal, TextInputComponent, MessageActionRow, PermissionsBitField} = require("discord.js");
const {userPermissions, clientPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
const {Poll} = require("../../structures/tasks");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("poll")
        .setDescription("Creates a poll")
        .addSubcommand(subcommand => subcommand
            .setName("create")
            .setDescription("Creates a poll")
        )
        .addSubcommand(subcommand => subcommand
            .setName("end")
            .setDescription("Ends a poll")
            .addStringOption(option => option
                .setName("poll")
                .setDescription("The id of the poll to end")
                .setRequired(true)))
        .addSubcommand(subcommand => subcommand
            .setName("list")
            .setDescription("Lists all current running polls")),
    async execute(message) {
        userPermissions(message, ["MANAGE_MESSAGES"]);
        const db = await pool.connect()
        if (message.options.getSubcommand() === "create") {
        clientPermissions(message, [PermissionsBitField.Flags.AddReactions, PermissionsBitField.Flags.EmbedLinks]);
        await showModal()

        async function showModal() {
            const modal = new Modal()
                .setCustomId('pollModal')
                .setTitle('Create Poll')

            const topicInput = new TextInputComponent()
                .setCustomId('topicInput')
                .setLabel('What is the topic of the poll?')
                .setRequired(true)
                .setStyle('SHORT')

            const durationInput = new TextInputComponent()
                .setCustomId('durationInput')
                .setLabel('How long should the poll last?')
                .setRequired(true)
                .setStyle('SHORT')
                .setPlaceholder('Example: 1d1h')

            const questions = new TextInputComponent()
                .setCustomId('questionsInput')
                .setLabel('What are the questions for the poll?')
                .setRequired(true)
                .setStyle('SHORT')
                .setPlaceholder('To add more questions, add a comma between each one')

            modal.addComponents(new MessageActionRow().addComponents(topicInput), new MessageActionRow().addComponents(durationInput), new MessageActionRow().addComponents(questions))

            await message.showModal(modal)
        }

        const filter = (interaction) => interaction.customId === 'pollModal';
        message.awaitModalSubmit({ filter, time: 40000 })
            .then(async modal => {
                const pollTopic = modal.fields.getTextInputValue('topicInput')
                const pollQuestions = modal.fields.getTextInputValue('questionsInput')
                const durationInput = modal.fields.getTextInputValue('durationInput')

                await modal.deferUpdate()
                const questions = pollQuestions.split(',')
                if (questions.length < 2) {
                    await message.channel.send('You need at least 2 questions')
                    return
                } else if (questions.length > 20) {
                    await modal.deferUpdate()
                    await message.channel.send("You can only provide a maximum of 20 questions")
                    return
                }

                const time = ConvertDate(durationInput)
                if (time === undefined) {
                    await message.channel.send("Invalid duration")
                    return
                } else if (time < 0) {
                    await message.channel.send("Duration must not be in the future")
                    return
                }

                const delta = new Date((Date.now() + time * 1000))
                const id = Math.random().toString(36).substr(2, 8)
                const indicators = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸", "🇹"].slice(0, questions.length);
                const embed = new MessageEmbed()
                    .setTitle(pollTopic)
                    .setDescription(`${questions.map((question, index) => `${indicators[index]} ${question}`).join("\n")} \n\nEnds <t:${Math.round(delta.valueOf() / 1000)}:R>`)
                    .setColor('WHITE')
                    .setFooter(`Poll ID: ${id}`)
                const pollMessage = await message.channel.send({embeds: [embed]})
                await indicators.forEach(emoji => pollMessage.react(emoji))
                await db.query("INSERT INTO vote(guild, message, date, type, channel, id) VALUES($1, $2, $3, $4, $5,$6)", [message.guild.id, pollMessage.id, delta, 3, message.channel.id, id]);
                await new Poll().dispatch_poll(message.client)
            }).catch(async () => {
                await message.channel.send("Timed out")
            })
        } else if (message.options.getSubcommand() === "list") {
            clientPermissions(message, [PermissionsBitField.Flags.EmbedLinks]);
            const rows = await db.query("SELECT * FROM vote WHERE guild = $1 AND type = $2", [message.guild.id, "poll"])
            if (rows.length === 0) {
                return await message.reply("There are no polls running")
            }
            const embed = new MessageEmbed()
                .setTitle("Current Running Polls")
                .setDescription(rows.map(row => {
                    const delta = new Date(row.date)
                    return `${row.vote.map(vote => vote.indicator).join("")} [${row.message}](https://discordapp.com/channels/${message.guild.id}/${row.channel}/${row.message}) - Ends ${delta.toLocaleString()}`
                }).join("\n"))
                .setColor('WHITE')
            await message.reply({embeds: [embed]})
        } else if (message.options.getSubcommand() === "end") {
            const poll = await db.query("SELECT * FROM vote WHERE guild = $1 AND id = $2 AND type = $3", [message.guild.id, message.options.getString("poll"), "poll"])
            if (poll.length === 0) {
                return await message.reply("That poll does not exist")
            }
            await db.query("UPDATE vote SET date = current_timestamp WHERE guild = $1 and message = $2 and type = $3", [poll.rows[0].message, "poll"]) // update this instead to current date to trigger the endpoll and reload task
            await new Poll().dispatch_poll(message)
            await message.reply("Poll ended")
        }
        await db.release()
    }
}