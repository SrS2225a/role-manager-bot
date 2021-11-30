const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {Formatters, MessageEmbed} = require("discord.js");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("invitecodes")
        .setDescription("Shows info about how many members you invited or someone else's")
        .addUserOption(option => option
            .setName("user")
            .setDescription("The user to get the invite info of")
            .setRequired(false)),

    async execute(message) {
        const db = await pool.connect()
        const user = message.options.getUser("user") || message.user
        const total = await db.query("SELECT amount, amount2, amount3, invite, channel FROM invite WHERE guild = $1 and member = $2", [message.guild.id, user.id])
        if (total.rowCount === 0) return message.reply("You haven't invited anyone yet!")
        const embed = new MessageEmbed()
            .setTitle(`Invite Info For ${user.username + '#' + user.discriminator}`)
            .setColor(message.member.displayColor)
        for (const invite of total.rows) {
            const channel = await message.guild.channels.cache.get(invite.channel)
            embed.addField(`${invite.invite} - #${channel?.name || 'deleted-channel'}`, `${Formatters.bold(invite.amount)} joins, ${Formatters.bold(invite.amount2)} leaves, ${Formatters.bold(invite.amount3)} fakes (${Formatters.bold(invite.amount - invite.amount2 + invite.amount3)})`)
        }
        await message.reply({embeds: [embed]})
        await db.release()
    }
}