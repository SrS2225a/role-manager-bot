const {SlashCommandBuilder} = require("@discordjs/builders");
const {MessageEmbed} = require("discord.js");
const {HelpMenu} = require("../../structures/menus");
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

                         .addField("Subcommands", `\n${subcommand}`, true)
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