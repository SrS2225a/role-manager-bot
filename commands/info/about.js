const {MessageEmbed} = require("discord.js");
const si = require('systeminformation');
const {pool} = require("../../database.js");
const {display_time} = require("../../structures/converters");
const { SlashCommandBuilder } = require('@discordjs/builders');
module.exports = {
    data: new SlashCommandBuilder()
        .setName("about")
        .setDescription("Shows info about the bot"),
    async execute(message) {
        const db = await pool.connect();
        await message.deferReply()
        const ran = await db.query('SELECT ran FROM bot LIMIT 1')
        const memory = (await si.mem()).total - ((await si.mem()).free + (await si.mem()).buffers + (await si.mem()).cached)
        let rx = 0
        si.networkStats().then(data => {
            rx = data[0].rx_bytes
        })
        let tx = 0
        si.networkStats().then(data => {
            tx = data[0].tx_bytes
        })
        const embed = new MessageEmbed()
            .setTitle("About Dionysus")
            .setColor('RANDOM')
            .addFields(
                {name: "Credits", value: "**Main Devs**\n<@!270848136006729728> <@!508455796783317002>\n**Contributors**\n<@!332180997653135383>", inline: true},
                {name: "Url's", value: "Bot Invite: [Click Here](https://discord.com/api/oauth2/authorize?client_id=437447118127366154&permissions=8&scope=bot)\nOpen Source: [Click Here](https://github.com/SrS2225a/role-manager-bot/tree/master)\nSupport: [Click Here](https://discord.gg/JHkhnzDvWG) \nDocumentation: [Click Here](https://github.com/SrS2225a/role-manager-bot/wiki)\nTO-DO: [Click Here](https://trello.com/b/Y86Q7qKA/dionysus-bot)\ntop.gg: [Click Here](https://top.gg/bot/437447118127366154)", inline: true},
                {name: "Stats", value: `Visible Guilds: ${message.client.guilds.cache.size}\nVisible Members: ${message.client.users.cache.size}\nCommands Ran: ${ran.rows[0].ran}\nUptime: ${display_time(si.time().uptime)}`, inline: true},
                {name: "Usage", value: `CPU: ${((await si.currentLoad()).avgLoad)}%\nMemory: ${(memory / (await si.mem()).total * 100).toFixed(2)}%\nNetwork: Download ${(rx / 1073742000).toFixed(2)} GB, Upload ${(tx / 1073742000).toFixed(2)} GB`, inline: true},
                {name: "Running On", value: `${(await si.osInfo()).platform} ${((await si.osInfo()).kernel)} (${((await si.osInfo()).distro)}) - node.js ${((await si.versions()).node)}`,inline: true})
        await message.editReply({embeds: [embed]})
        await db.release()
    }
}