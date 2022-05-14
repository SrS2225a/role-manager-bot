const {Collection} = require("discord.js");
const fs = require("fs");
const {Routes} = require("discord-api-types/v9");
const {REST} = require("@discordjs/rest");
const json = require('../config.json');

function resolveAsChannel_Dm_Here(message, args) {
    if (args) {
        if (args.toLowerCase() === 'here') {
            return message.channel;
        } else if (args.toLowerCase() === 'dm') {
            return message.user;
        } else {
            const channel = resolveById(args, message.guild) ?? resolveByQuery(args, message.guild);
            return channel ? channel : (() => {
                throw {identifier: "ChannelNotFound", message: `I could not find the channel ${args}!`}
            })()

            function resolveById(args, guild) {
                const channelId = /^<#(?<id>\d{17,19})>$/.exec(args) ?? /^(?<id>\d{17,19})$/.exec(args);
                return channelId ? guild.channels.get(channelId.groups.id) : null;
            }

            function resolveByQuery(args, guild) {
                const channel = guild.channels.find(c => c.name === args.toLowerCase());
                return channel ? channel : null;
            }
        }
    }
}

function resolveAsChannel_Role(message, args) {
    if (args) {
        const role = resolveById(args, message.guild) ?? resolveByQuery(args, message.guild);
        return role ? role : (() => {
            throw {identifier: "ChannelOrRoleNotFound", message: `I could not find the channel or role ${args}!`}
        })()

        function resolveById(args, guild) {
            const channelId = /^<#(?<id>\d{17,19})>$/.exec(args) ?? /^(?<id>\d{17,19})$/.exec(args);
            if (channelId) {
                return guild.channels.cache.get(channelId.groups.id);
            } else {
                const roleId = /^<@&(?<id>\d{17,19})>$/.exec(args) ?? /^(?<id>\d{17,19})$/.exec(args);
                return roleId ? guild.roles.cache.get(roleId.groups.id) : null;
            }
        }

        function resolveByQuery(args, guild) {
            const channel = guild.channels.cache.find(c => c.name === args.toLowerCase());
            if (channel) {
                return channel;
            }
            const role = guild.roles.cache.find(r => r.name === args.toLowerCase());
            if (role) {
                return role;
            }
        }
    }
}

async function resolveMessage(message, parameter) {
    const channel = message.channel ?? message.message.channel

    async function resolveById(message, parameter) {
        try {
            return await channel.messages.fetch(parameter);
        } catch (e) {
            return null;
        }
    }

    function getMessageFromChannel(channels, messages) {
        const channel = messages.client.channels.cache.get(channels)
        if(!channel) return null
        const message = channels.messages.cache.get(messages)
        if(!message) return null
        return message
    }

    async function resolveByLink(message, parameter) {
        const match = /^(?<channel>\d{17,19})?\/(?<message>\d{17,19})$/.exec(message)
        if(!match) return null
        const channel = match.groups.channel ? await resolveById(match.groups.channel, parameter) : parameter.message.channel
        if(!channel) return null
        try {
            return channel.messages.fetch(match.groups.message)
        } catch (e) {
            return null
        }
    }

    async function resolveByChannelAndMessage(message, parameter) {
        const result = /^<#(?<id>\d{17,19})>$/.exec(parameter)?.groups
        if(!result) return null
        return getMessageFromChannel(result.channelId, result.messageId)
    }
    const msg = await resolveById(message, parameter) ?? await resolveByLink(message, parameter) ?? await resolveByChannelAndMessage(message, parameter)
    if(msg) {return msg} else {(() => {throw {identifier: "ArgumentMessageError", message: `I could not find the message ${parameter}`}})()}
}

async function resolveRole(message, parameter) {
    const role = resolveById(parameter, message.guild) ?? resolveByQuery(parameter, message.guild);
    return role ? role : (() => {
        throw {identifier: "RoleNotFound", message: `I could not find the role ${parameter}!`}
    })()
    async function resolveById(args, guild) {
        const roleId = /^<@&(?<id>\d{17,19})>$/.exec(args) ?? /^(?<id>\d{17,19})$/.exec(args);
        return roleId ? guild.roles.cache.get(roleId.groups.id) : null;
    }
    async function resolveByQuery(args, guild) {
        const role = guild.roles.cache.find(r => r.name === args.toLowerCase());
        return role ? role : null;
    }
}

async function checkChannelType(parameter, channel) {
    if (channel.type === parameter) {
        return channel
    } else {
        (() => {throw {identifier: "ArgumentChannelTypeError", message: `The channel ${channel.name} is not a ${parameter}!`}})()
    }
}

function resolveCommands(client) {
    const commands = []
    const guildCommands = []
    client.commands = new Collection()
    const commandFolders = fs.readdirSync('commands')
    for (const folder of commandFolders) {
        const commandFiles = fs.readdirSync(`commands/${folder}/`).filter(file => file.endsWith('.js'))
        for (const file of commandFiles) {
            const command = require(`../commands/${folder}/${file}`)
            // register command.data or command.context
            if (command.data) {
                client.commands.set(command.data.name, command)
                if (command.data.name === "dev") {
                    guildCommands.push(command.data.toJSON())
                }
                commands.push(command.data.toJSON())
            }
            if (command.context) {
                client.commands.set(command.context.name, command)
                commands.push(command.context.toJSON())
            }
        }
    }

    (async () => {
        const rest = new REST({version: '9'}).setToken(json['token'])
        await rest.put(Routes.applicationCommands(json["clientID"]), {body: commands})
    })()
}

function resolveEvents(client) {
    const eventFiles = fs.readdirSync('events').filter(file=> file.endsWith('.js'))
    const eventFolders = fs.readdirSync('events').filter(file=> fs.statSync(`events/${file}`).isDirectory())
    for (const file of eventFiles) {
        const event = require(`../events/${file}`)
        if (event.once) {
            client.once(event.name, (...args) => event.execute(...args))
        } else {
            client.on(event.name, (...args) => event.execute(...args))
        }

    }
    for (const folder of eventFolders) {
        const eventFiles = fs.readdirSync(`events/${folder}`).filter(file => file.endsWith('.js'))
        for (const file of eventFiles) {
            const event = require(`../events/${folder}/${file}`)
            if (event.once) {
                client.once(event.name, (...args) => event.execute(...args))
            } else {
                client.on(event.name, (...args) => event.execute(...args))
            }
        }
    }
}

module.exports = {
    resolveAsChannel_Dm_Here,
    resolveAsChannel_Role,
    resolveMessage,
    checkChannelType,
    resolveRole,
    resolveCommands,
    resolveEvents
}