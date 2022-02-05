const {SlashCommandBuilder} = require("@discordjs/builders");
const {MessageEmbed} = require("discord.js");
const {HelpMenu} = require("../../structures/menus");

async function startCollector() {
    const filter = i => i.user.id === this.author.id
    const collector = this.channel.createMessageComponentCollector({filter, time: 128000})
    collector.on('collect', async i => {
        if (i.customId === 'firstPage') {
            await this.show_page(1, i)
        } else if (i.customId === 'back') {
            await this.show_page(this.current_page - 1, i)
        } else if (i.customId === 'stop') {
            await i.message.delete()
        } else if (i.customId === 'next') {
            await this.show_page(this.current_page + 1, i)
        } else if (i.customId === 'lastPage') {
            await this.show_page(this.maxium_pages, i)
        }
        await i.deferUpdate();
    })
}

module.exports = {
    data: new SlashCommandBuilder()
        .setName("help")
        .setDescription("Displays a list of commands.")
        .addStringOption(option => option
            .setName("command")
            .setDescription("The command to get help for.")
            .setRequired(false)
        ),
    async execute(message) {
        if (message.options.getString("command") === null) {
            const help = new HelpMenu()
            await help.startHelp(message)
        } else {
            const command = message.client.commands.get(message.options.getString("command"));
            console.log(command.data)
            if (command) {
                // check if subcommands
                let usage = "";
                let subcommand = "";
                for (const subcommands of command.data.options) {
                    if (!subcommands.type) {
                        subcommand += `${subcommands.name}\n`;
                    }
                }
                for (let usages of command.data.options) {
                    if (usages.type) {
                        if (usages.required) {
                            usage += `**<${usages.name}>** - ${usages.description}\n`
                        } else {
                            usage += `**[${usages.name}]** - ${usages.description}\n`
                        }
                    }
                }
                 if (subcommand !== "") {
                     const embed = new MessageEmbed()
                         .setTitle(`${command.data.name} Help`)
                         .setDescription(`${command.data.description}`)

                         .addField("Subcommands", `**Subcommands:**\n${subcommand}`, true)
                     message.reply({embeds: [embed]});
                 } else {
                     const embed = new MessageEmbed()
                         .setTitle(`Dionysus Help - ${command.data.name}`)
                         .setDescription(`${command.data.description}`)
                         .addField("Usage", usage)
                     message.reply({embeds: [embed]});
                 }
            } else {
                message.reply("That command does not exist.");
            }
        }
    }
}