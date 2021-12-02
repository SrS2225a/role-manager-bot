const {pool} = require("../../database");
const {Util, MessageEmbed, Formatters} = require('discord.js');

module.exports = {
    name: 'interactionCreate',
    once: false,
    async execute(interaction) {
        const command = interaction.client.commands.get(interaction.commandName)
        if(!command) return
        try {
            const db = await pool.connect()
            const blacklistedCommand = await db.query('SELECT message FROM blacklist WHERE member = $1 and message = $2 and type = $3 LIMIT 1', [interaction.guildId, command.name, 'command'])
            const blockedUser = await db.query("SELECT message FROM blacklist WHERE member = $1 and type = $2 LIMIT 1", [interaction.user.id, 'user'])
            await db.release()
            if (blacklistedCommand.rows.length) {interaction.reply(`DisabledCommand: ${command.name} command is disabled.`)}
            else if (blockedUser.rows.length) {interaction.reply(`ClientPermissionsMissing: You are currently blocked from using this bot for **${Util.removeMentions(blockedUser.rows[0].message)}**. If you believe that this is an error, please join the support server @ https://discord.gg/JHkhnzDvWG and explain why.`)}
            else {
                await command.execute(interaction)
                const channel = interaction.client.channels.cache.get('866678659862626355')
                await channel.send(`A new command was ran **${command.data.name}** in guild **${interaction.guild.name} (${interaction.guildId})**`)
                await db.query('UPDATE bot SET ran = ran + 1')
            }
        } catch (error) {
            console.log(error.stack)
            if (error.identifier) {
                await interaction.channel.send(`${error.identifier}: ${Util.removeMentions(error.message)}`)
            } else {
                const embed = new MessageEmbed()
                    .setColor('WHITE')
                    .setTitle("An unexpected error has occurred")
                    .setDescription(`**This error has automatically been sent to the bot developers and will work to sort this out ASAP**\n• [For more support, visit the support server here](https://discord.gg/JHkhnzDvWG)\n\n${Formatters.codeBlock('js', error)}`)
                interaction.channel.send({embeds: [embed]});
                const channel = interaction.client.channels.cache.get('840276875301224479')
                await channel.send(`New exception occurred in guild **${interaction.guild.name} (${interaction.guild.id})** for command **${command.data.name}**\n${Formatters.codeBlock('js', error.stack)}`)
            }
        }
    }
}