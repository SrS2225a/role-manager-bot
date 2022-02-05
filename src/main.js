// Require the necessary discord.js classes
const {Client, Intents} = require('discord.js');
const json = require('./config.json');
const {resolveCommands, resolveEvents} = require("./structures/resolvers");

// Create a new client instance
console.log("Initializing and connecting to discord!")
const client = new Client({intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES, Intents.FLAGS.GUILD_MEMBERS, Intents.FLAGS.GUILD_INVITES, Intents.FLAGS.GUILD_VOICE_STATES, Intents.FLAGS.GUILD_MESSAGE_REACTIONS], partials: ['MESSAGE', 'CHANNEL', 'REACTION', 'USER']});

resolveCommands(client);
resolveEvents(client);

client.login(json['token']).catch(error => console.error(error))