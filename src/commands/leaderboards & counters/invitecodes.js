const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {Formatters, PermissionsBitField, EmbedBuilder, Colors} = require("discord.js");
const {clientPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("invitecodes")
        .setDescription("Shows the invite codes for the server.")
        .addUserOption(option => option
            .setName("user")
            .setDescription("The user to get the invite info of")
            .setRequired(false)),
    async execute(message) {
        clientPermissions(message, [PermissionsBitField.Flags.EmbedLinks]);
        const db = await pool.connect()
        const user = message.options.getUser("user") || message.user
        const total = await db.query("SELECT SUM(amount)::integer AS amount, SUM(amount2)::integer AS amount2, SUM(amount3)::integer AS amount3, invite FROM invite WHERE guild = $1 and member = $2 GROUP BY invite", [message.guild.id, user.id])
        if (total.rowCount === 0) return message.reply("You haven't invited anyone yet!")
        const embed = new EmbedBuilder()
            .setTitle(`Invite Info For ${user.username + '#' + user.discriminator}`)
            .setColor(Colors.White)
        for (const invite of total.rows) {
            embed.addFields({name: invite.invite, value: `${Formatters.bold(invite.amount)} joins, ${Formatters.bold(invite.amount2)} leaves, ${Formatters.bold(invite.amount3)} fakes (${Formatters.bold(invite.amount - (invite.amount2 + invite.amount3))} real)`})
        }
        await message.reply({embeds: [embed]})
        await db.release()
    }
}