const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {PaginatorAsTable} = require("../../structures/paginator");
const {display_time} = require("../../structures/converters");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("leaderboard")
        .setDescription("View the leaderboard for a specific counter.")
        .addSubcommand(subcommand => subcommand
            .setName("invites")
            .setDescription("View the leaderboard for invites."))
        .addSubcommand(subcommand => subcommand
            .setName("messages")
            .setDescription("View the leaderboard for messages."))
        .addSubcommand(subcommand => subcommand
            .setName("voice")
            .setDescription("View the leaderboard for voice."))
        .addSubcommand(subcommand => subcommand
            .setName("partners")
            .setDescription("View the leaderboard for partners.")),
    async execute(message) {
        const db = await pool.connect()
        if (message.options.getSubcommand() === "invites") {
            const result = await db.query("SELECT member, SUM(amount) AS a, SUM(amount2) AS b, SUM(amount3) AS c FROM invite WHERE guild = $1 GROUP BY member ORDER BY SUM(amount) DESC, SUM(amount2) DESC, SUM(amount3) DESC", [message.guild.id])
            const table = []
            for (const row of result.rows) {
                const user = await message.guild.members.cache.get(row.member)
                if (user) {
                    table.push([row.a, row.b, row.c, user.user.username + "#" + user.user.discriminator])
                }
            }
            const paginate = new PaginatorAsTable(message, table)
            paginate.heading = ['JOINS', 'LEAVES', 'FAKES', 'USER']
            paginate.title = "Invites Leaderboard"
            await paginate.paginate()
        } else if (message.options.getSubcommand() === "messages") {
            const result = await db.query("SELECT member, SUM(messages) AS a FROM message WHERE guild = $1 GROUP BY member ORDER BY SUM(messages) DESC", [message.guildId])
            const table = []
            for (const row of result.rows) {
                const user = await message.guild.members.cache.get(row.member)
                if (user) {
                    table.push([row.a, user.user.username + "#" + user.user.discriminator])
                }
            }
            const paginate = new PaginatorAsTable(message, table)
            paginate.heading=['MESSAGES', 'USER']
            paginate.title='Messages Leaderboard'
            await paginate.paginate()
        } else if (message.options.getSubcommand() === "voice") {
            const result = await db.query("SELECT member, SUM(voice) AS a, sum(voice2) AS b FROM voice WHERE guild = $1 GROUP BY member ORDER BY SUM(voice) DESC, sum(voice2) DESC", [message.guildId])
            const table = []
            for (const row of result.rows) {
                const user = await message.guild.members.cache.get(row.member)
                if (user) {
                    table.push([display_time(row.a, 6), display_time(row.b, 6), user.user.username + "#" + user.user.discriminator])
                }
            }
            const paginate = new PaginatorAsTable(message, table)
            paginate.heading=['VOICE', 'VOICE2', 'USER']
            paginate.title='Voice Leaderboard'
            await paginate.paginate()
        } else if (message.options.getSubcommand() === "partners") {
            const result = await db.query("SELECT member, number FROM partner WHERE guild = $1 ORDER BY number DESC", [message.guildId])
            const table = []
            for (const row of result.rows) {
                const user = await message.guild.members.cache.get(row.member)
                if (user) {
                    table.push([row.number, user.user.username + "#" + user.user.discriminator])
                }
            }
            const paginate = new PaginatorAsTable(message, table)
            paginate.heading=['PARTNERS', 'USER']
            paginate.title='Partner Leaderboard'
            await paginate.paginate()
        }
        await db.release()
    }
}