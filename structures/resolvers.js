const {Permissions} = require("discord.js");

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
            throw {identifier: "RoleNotFound", message: `I could not find the role ${args}!`}
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
            return null;
        }
    }
}

async function resolveMessage(message, parameter) {
    const channel = message.channel ?? message.message.channel

    async function resolveById(message, parameter) {
        const resolved = await channel.messages.fetch(parameter)
        if (!resolved) return null
        return resolved
    }

    function getMessageFromChannel(channels, messages) {
        const channel = message.client.channels.cache.get(channels)
        if(!channel) return null
        return channel.messages.fetch(messages)
    }

    async function resolveByLink(message, parameter) {
        const match = /^(?<channel>\d{17,19})?\/(?<message>\d{17,19})$/.exec(message)
        if(!match) return null
        const channel = match.groups.channel ? await resolveById(match.groups.channel, parameter) : parameter.message.channel
        if(!channel) return null
        return channel.messages.fetch(match.groups.message)
    }

    async function resolveByChannelAndMessage(message, parameter) {
        const result = /^<#(?<id>\d{17,19})>$/.exec(parameter)?.groups
        if(!result) return null
        return getMessageFromChannel(result.channelId, result.messageId)
    }
    const msg = await resolveById(message, parameter) ?? await resolveByLink(message, parameter) ?? await resolveByChannelAndMessage(message, parameter)
    if(msg) {return msg} else {(() => {throw {identifier: "ArgumentMessageError", message: `I could not find the message ${parameter}`}})()}
}

module.exports = {
    resolveAsChannel_Dm_Here,
    resolveAsChannel_Role,
    resolveMessage
}