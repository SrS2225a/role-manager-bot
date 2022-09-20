// Require the necessary discord.js classes
const {Client, GatewayIntentBits, Partials} = require('discord.js');
const json = require('./config.json');
const {resolveCommands, resolveEvents} = require("./structures/resolvers");

// Create a new client instance
console.log("Initializing and connecting to discord!")

const client = new Client({intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.GuildMessages, GatewayIntentBits.GuildInvites, GatewayIntentBits.GuildVoiceStates, GatewayIntentBits.GuildMessageReactions], partials: [Partials.Message, Partials.Channel, Partials.Reaction, Partials.User]});

resolveCommands(client);
resolveEvents(client);

client.login(json['token']).catch(error => console.error(error))