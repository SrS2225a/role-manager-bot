const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions, clientPermissions} = require("../../structures/permissions");
const {pool} = require("../../database");
const {MessageEmbed} = require("discord.js");
const {Giveaway} = require("../../structures/tasks");
const {GiveawayCreator} = require("../../structures/menus");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("giveaway")
        .setDescription("Creates a giveaway")
        .addSubcommand(subcommand => subcommand
            .setName("create")
            .setDescription("Creates a giveaway"))
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
        // giveaways issues
        // 1, change all vote of type parameters to int. 2, Dionysus is thinking a giveaway is active even though it is not from the event collector code. 3, will not accept more than 1 winner.
        userPermissions(message, ["MANAGE_MESSAGES"]);
        const db = await pool.connect()
        if (message.options.getSubcommand() === "create") {
            clientPermissions(message, ["ADD_REACTIONS", "EMBED_LINKS", "MANAGE_MESSAGES"]);
            const giveaway = new GiveawayCreator()
            await giveaway.createGiveaway(message)
        } else if (message.options.getSubcommand() === "list") {
            const rows = await db.query("SELECT * FROM vote WHERE guild=$1 AND type=0 or type=1", [message.guild.id]);
            if (rows.rowCount === 0) {
                return await message.reply("There are no active giveaways running");
            }
            const embed = new MessageEmbed()
                .setTitle("Current giveaways")
                .setColor('WHITE')
                .setTimestamp();
            for (const row of rows.rows) {
                const delta = new Date(row.date)
                if (row.type === 1) {
                    embed.addField(`${row.id}`, `[Jump To Active Giveaway](https://discordapp.com/channels/${message.guild.id}/${row.channel}/${row.message}) - ${row.win} Winners\nEnds in: <t:${Math.round(delta.valueOf() / 1000)}:R>`)
                } else {
                    embed.addField(`${row.id}`, `[Jump To Active Giveaway](https://discordapp.com/channels/${message.guild.id}/${row.channel}/${row.message}) - ${row.win} Winners\nStarts in: <t:${Math.round(delta.valueOf() / 1000)}:R>`)
                }
            }
            return await message.reply({embeds: [embed]});
        } else if (message.options.getSubcommand() === "end") {
            const id = message.options.getString("id");
            const rows = await db.query("SELECT * FROM vote WHERE id=$1 AND guild=$2", [id, message.guild.id]);
            if (rows.rowCount === 0) {
                return await message.reply("Invalid giveaway id");
            }
            const row = rows.rows[0];
            const delta = new Date(row.date)
            if (delta < Date.now()) {
                return await message.reply("Giveaway has already ended");
            }
            await db.query("UPDATE vote SET date = $1 WHERE guild= $2 and id = $3", [new Date(), message.guild.id, id]);
            await new Giveaway().dispatch_giveaway(message.client)
            return await message.reply("Giveaway ended");
        } else if (message.options.getSubcommand() === "reroll") {
            const id = message.options.getString("id");
            const rows = await db.query("SELECT * FROM vote WHERE id=$1 AND guild=$2 AND type=2", [id, message.guild.id]);
            if (rows.rowCount === 0) {
                return await message.reply("Invalid giveaway id or the giveaway has not ended yet");
            }
            await new Giveaway().call_giveaway(message, rows, db)
            return await message.reply("Giveaway rerolled");
        }
        await db.release()
    }
}