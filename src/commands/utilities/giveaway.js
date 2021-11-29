const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
const {ConvertDate} = require("../../structures/converters");
const {MessageEmbed} = require("discord.js");
const {Giveaway} = require("../../structures/tasks");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("giveaway")
        .setDescription("Creates a giveaway")
        .addSubcommand(subcommand => subcommand
            .setName("create")
            .setDescription("Creates a giveaway")
            .addStringOption(option => option
                .setName("name")
                .setDescription("The name of the giveaway")
                .setRequired(true))
            .addStringOption(option => option
                .setName("duration")
                .setDescription("The duration of the giveaway")
                .setRequired(true))
            .addIntegerOption(option => option
                .setName("winners")
                .setDescription("The number of winners")
                .setRequired(true))
            .addStringOption(option => option
                .setName("requirement")
                .setDescription("The optional requirement for the giveaway")
                .setRequired(false)))
        .addSubcommand(subcommand => subcommand
            .setName("list")
            .setDescription("Lists all current running giveaways"))
        .addSubcommand(subcommand => subcommand
            .setName("end")
            .setDescription("Ends a giveaway")
            .addStringOption(option => option
                .setName("id")
                .setDescription("The id of the giveaway")
                .setRequired(true)))
        .addSubcommand(subcommand => subcommand
            .setName("reroll")
            .setDescription("Rerolls a ended giveaway")
            .addStringOption(option => option
                .setName("id")
                .setDescription("The id of the giveaway")
                .setRequired(true))),
    async execute(message) {
        userPermissions(message, ["MANAGE_MESSAGES"]);
        const db = await pool.connect()
        if (message.options.getSubcommand() === "create") {
            const name = message.options.getString("name");
            const duration = ConvertDate(message.options.getString("duration"));
            const winners = message.options.getInteger("winners");
            const requirement = message.options.getString("requirement");
            if (duration === null) {
                return message.reply("Invalid duration");
            } else if (duration < 0) {
                return await message.reply("Duration must be in the future")
            }
            if (winners < 1) {
                return await message.reply("You must have at least one winner")
            }
            const delta = new Date(Date.now() + duration * 1000)
            const id = Math.random().toString(36).substr(2, 8)
            const embed = new MessageEmbed()
                .setTitle(name)
                .setDescription(`React with 🎉 to enter!\n\n${requirement ? `**Requirements:** ${requirement}\n` : ""} **Winners:** ${winners} \n**Ends:** <t:${Math.round(delta.valueOf() / 1000)}:R>`)
                .setColor('WHITE')
            const msg = await message.channel.send({embeds: [embed]});
            await msg.react("🎉");
            await db.query("INSERT INTO vote(guild, message, date, win, type, channel, id) VALUES($1, $2, $3, $4, $5, $6, $7)", [message.guild.id, msg.id, delta, winners, "giveaway", message.channel.id, id]);
            await new Giveaway().dispatch_giveaway(message.client)
            return await message.reply(`Giveaway created with id: ${id}`);
        } else if (message.options.getSubcommand() === "list") {
            const rows = await db.query("SELECT * FROM vote WHERE guild=$1 AND type='giveaway'", [message.guild.id]);
            if (rows.rowCount === 0) {
                return await message.reply("There are no active giveaways running");
            }
            const embed = new MessageEmbed()
                .setTitle("Current giveaways")
                .setColor('WHITE')
                .setTimestamp();
            for (const row of rows.rows) {
                const delta = new Date(row.date)
                embed.addField(`${row.id}`, `[Jump To Active Giveaway](https://discordapp.com/channels/${message.guild.id}/${row.channel}/${row.message}) - ${row.win} Winners\nEnds <t:${Math.round(delta.valueOf() / 1000)}:R>`)
            }
            return await message.reply({embeds: [embed]});
        } else if (message.options.getSubcommand() === "end") {
            const id = message.options.getString("id");
            const rows = await db.query("SELECT * FROM vote WHERE id=$1 AND guild=$2 AND type='giveaway'", [id, message.guild.id]);
            if (rows.rowCount === 0) {
                return await message.reply("Invalid giveaway id");
            }
            const row = rows.rows[0];
            const delta = new Date(row.date)
            if (delta < Date.now()) {
                return await message.reply("Giveaway has already ended");
            }
            await db.query("UPDATE vote SET date = $1 WHERE guild= $2 and id = $3 and type = $4", [new Date(), message.guild.id, id, 'giveaway']);
            await new Giveaway().dispatch_giveaway(message.client)
            return await message.reply("Giveaway ended");
        } else if (message.options.getSubcommand() === "reroll") {
            const id = message.options.getString("id");
            const rows = await db.query("SELECT * FROM vote WHERE id=$1 AND guild=$2 AND type='finished'", [id, message.guild.id]);
            if (rows.rowCount === 0) {
                return await message.reply("Invalid giveaway id or the giveaway has not ended yet");
            }
            await new Giveaway().call_giveaway(message, rows, db)
            return await message.reply("Giveaway rerolled");
        }
        await pool.release(db)
    }
}