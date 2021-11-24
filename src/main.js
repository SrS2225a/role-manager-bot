// Require the necessary discord.js classes
const {Client, Intents, Collection} = require('discord.js');
const json = require('./config.json');
const { Routes } = require('discord-api-types/v9');
const fs = require("fs");
const {REST} = require("@discordjs/rest");

// Create a new client instance
console.log("Initializing and connecting to discord!")
const client = new Client({intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES, Intents.FLAGS.GUILD_MEMBERS, Intents.FLAGS.GUILD_INVITES, Intents.FLAGS.GUILD_VOICE_STATES, Intents.FLAGS.GUILD_MESSAGE_REACTIONS], partials: ['MESSAGE', 'CHANNEL', 'REACTION', 'USER']});
const commands = []
const guildCommands = []
client.commands = new Collection()
const commandFolders = fs.readdirSync(`./commands`)
for (const folder of commandFolders) {
    const commandFiles = fs.readdirSync(`./commands/${folder}`).filter(file => file.endsWith('.js'))
    for (const file of commandFiles) {
        const command = require(`./src/commands/${folder}/${file}`)
        client.commands.set(command.data.name, command)
            if (command.data.name === "dev") {
                guildCommands.push(command.data.toJSON())
            } else {
                commands.push(command.data.toJSON());
            }
    }
}

(async () => {
    const rest = new REST({version: '9'}).setToken(json['token'])
    await rest.put(Routes.applicationCommands(json["clientID"]), {body: commands})
    await rest.put(Routes.applicationGuildCommands(json["clientID"], '531247629649182750'), {body: guildCommands})
})()

const eventFiles = fs.readdirSync('./events').filter(file=> file.endsWith('.js'))
const eventFolders = fs.readdirSync('./events').filter(file=> fs.statSync(`./events/${file}`).isDirectory())
for (const file of eventFiles) {
    const event = require(`./src/events/${file}`)
    if (event.once) {
        client.once(event.name, (...args) => event.execute(...args))
    } else {
        client.on(event.name, (...args) => event.execute(...args))
    }

}
for (const folder of eventFolders) {
    const eventFiles = fs.readdirSync(`./events/${folder}`).filter(file => file.endsWith('.js'))
    for (const file of eventFiles) {
        const event = require(`./src/events/${folder}/${file}`)
        if (event.once) {
            client.once(event.name, (...args) => event.execute(...args))
        } else {
            client.on(event.name, (...args) => event.execute(...args))
        }
    }
}

client.login(json['token']).catch(error => console.error(error))