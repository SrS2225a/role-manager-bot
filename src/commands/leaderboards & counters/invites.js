const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {MessageEmbed} = require("discord.js");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("invites")
        .setDescription("Shows your current invites.")
        .addUserOption(option => option
            .setName("user")
            .setDescription("The user to check invites for.")
            .setRequired(false)),
    async execute(message) {
        // TODO: Add support to show invites overtime as a graph.
        const db = await pool.connect()
        const user = message.options.getUser("user") || message.user
        const totalInvites = await db.query("SELECT SUM(amount)::integer AS a, SUM(amount2)::integer AS b, SUM(amount3)::integer AS c FROM invite WHERE guild = $1 and member = $2 GROUP BY member", [message.guild.id, user.id])
       const place = await db.query("SELECT COUNT(*)::integer FROM (SELECT member, sum(amount)::integer AS amount FROM invite WHERE guild = $1 GROUP BY member ORDER BY sum(amount) DESC) AS a WHERE amount >= $2", [message.guild.id,  totalInvites.rows[0].a])
        if (totalInvites.rows.length) {
            const total = totalInvites.rows[0].a - (totalInvites.rows[0].b + totalInvites.rows[0].c)
            const embed = new MessageEmbed()
                .setTitle(`${user.username}'s Invites`)
                .setDescription(`${total} total invites.`)
                .addField("Joins", totalInvites.rows[0].a.toString(), true)
                .addField("Leaves", totalInvites.rows[0].b.toString(), true)
                .addField("Fakes", totalInvites.rows[0].c.toString(), true)
                .addField("Place", place.rows[0].count.toString(), true)
                .addField("Deficit", `${totalInvites.rows[0].b + totalInvites.rows[0].c !== 0 ? ((totalInvites.rows[0].b + totalInvites.rows[0].c) / totalInvites.rows[0].a * 100).toFixed(2) : 0.0}%`, true)
                .addField("Invited Server", `${totalInvites.rows[0].a !== 0 ? (total / message.guild.memberCount * 100).toFixed(2).toString() : '0.0'}%`, true)
            message.reply({embeds: [embed]})
        } else {
            message.reply("You don't have any invites.")
        }
        await db.release()
    }
}