const {SlashCommandBuilder, ContextMenuCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {PermissionsBitField, Colors, EmbedBuilder} = require("discord.js");
const {clientPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("invites")
        .setDescription("Shows your current invites.")
        .addUserOption(option => option
            .setName("user")
            .setDescription("The user to check invites for.")
            .setRequired(false)),
    context: new ContextMenuCommandBuilder()
        .setName("Invites")
        .setType(2),
    async execute(message) {
        // TODO: Add support to show invites overtime as a graph.
        clientPermissions(message, [PermissionsBitField.Flags.EmbedLinks]);
        const db = await pool.connect()
        const user = message.options.getUser("user") || message.user
        const totalInvites = await db.query("SELECT SUM(amount)::integer AS a, SUM(amount2)::integer AS b, SUM(amount3)::integer AS c FROM invite WHERE guild = $1 and member = $2 GROUP BY member", [message.guild.id, user.id])
        const place = await db.query("SELECT COUNT(*)::integer FROM (SELECT member, sum(amount)::integer AS amount FROM invite WHERE guild = $1 GROUP BY member ORDER BY sum(amount) DESC) AS a WHERE amount >= $2", [message.guild.id,  totalInvites.rows[0]?.a])
        if (totalInvites.rows.length) {
            const total = totalInvites.rows[0].a - (totalInvites.rows[0].b + totalInvites.rows[0].c)
            const embed = new EmbedBuilder()
                .setTitle(`${user.username}'s Invites`)
                .setColor(Colors.White)
                .setDescription(`${total} total invites.`)
                .addFields({name: "Joins", value: totalInvites.rows[0].a.toString(), inline: true}, {name: "Leaves", value: totalInvites.rows[0].b.toString(), inline: true}, {name: "Fakes", value: totalInvites.rows[0].c.toString(), inline: true}, {name: "Place", value: place.rows[0].count.toString(), inline: true}, {name: "Deficit", value: `${totalInvites.rows[0].b + totalInvites.rows[0].c !== 0 ? ((totalInvites.rows[0].b + totalInvites.rows[0].c) / totalInvites.rows[0].a * 100).toFixed(2) : 0.0}%`, inline: true}, {name: "Invited Server", value: `${totalInvites.rows[0].a !== 0 ? (total / message.guild.memberCount * 100).toFixed(2).toString() : '0.0'}%`, inline: true})
            message.reply({embeds: [embed]})
        } else {
            message.reply("You don't have any invites.")
        }
        await db.release()
    }
}