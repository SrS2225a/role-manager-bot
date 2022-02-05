const {SlashCommandBuilder} = require("@discordjs/builders");
const {ConvertDate} = require("../../structures/converters");
const {MessageEmbed} = require("discord.js");
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
            .addStringOption(option => option
                .setName("questions")
                .setDescription("The questions for the poll. To add more questions, add a comma between each one")
                .setRequired(true))
            .addStringOption(option => option
                .setName("topic")
                .setDescription("The topic of the poll")
                .setRequired(true))
            .addStringOption(option => option
                .setName("duration")
                .setDescription("The duration of the poll")
                .setRequired(true))
            .addBooleanOption(option => option
                .setName("multiple")
                .setDescription("Whether the poll allows multiple answers")
                .setRequired(false)))
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
            clientPermissions(message, ["ADD_REACTIONS", "EMBED_LINKS"]);
            const questions = message.options.getString("questions").split(",");
            const topic = message.options.getString("topic");
            const time = ConvertDate(message.options.getString("duration"))
            const multiple = message.options.getBoolean("multiple");
            if (questions.length < 2) {
                return await message.reply("You must provide at least 2 questions");
            } else if (questions.length > 20) {
                return await message.reply("You can only provide a maximum of 20 questions");
            }
            if (time === undefined) {
                return await message.reply("Invalid duration")
            } else if (time < 0) {
                return await message.reply("Duration must be in the future")
            }
            const delta = new Date(Date.now() + time * 1000)
            const multiple_choice = multiple ? "multiple-choice" : "single-choice";
            const indicators = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸", "🇹"].slice(0, questions.length);
            const embed = new MessageEmbed()
                .setTitle(topic)
                .setDescription(`${questions.map((question, index) => `${indicators[index]} ${question}`).join("\n")} \n\nEnds <t:${Math.round(delta.valueOf() / 1000)}:R>`)
                .setColor('WHITE')
                .setFooter(`This is a ${multiple_choice} poll`)
            const interaction = await message.channel.send({embeds: [embed]})
            await indicators.forEach(emoji => interaction.react(emoji))
            const id = Math.random().toString(36).substr(2, 8)
            await db.query("INSERT INTO vote(guild, message, date, win, type, channel, id) VALUES($1, $2, $3, $4, $5, $6, $7)", [message.guild.id, interaction.id, delta, multiple, 3, message.channel.id, id]);
            await new Poll().dispatch_poll(message.client)
            return await message.reply(`Poll created with id: ${id}`);
        } else if (message.options.getSubcommand() === "list") {
            clientPermissions(message, ["EMBED_LINKS"]);
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
            await db.query("UPDATE vote SET date = $1 WHERE guild = $1 and message = $2 and type = $3", [new Date(), poll.rows[0].message, "poll"]) // update this instead to current date to trigger the endpoll and reload task
            await new Poll().dispatch_poll(message)
            await message.reply("Poll ended")
        }
        await db.release()
    }
}