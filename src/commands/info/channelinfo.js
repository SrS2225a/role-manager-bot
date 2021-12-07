const {MessageEmbed, Formatters} = require("discord.js");
const {SlashCommandBuilder} = require("@discordjs/builders");
const {clientPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("channelinfo")
        .setDescription("Shows info about a channel")
        .addChannelOption(option =>
        option.setName('channel')
            .setDescription("The channel to get information about")
            .setRequired(false)),
    async execute(message) {
        const channel = await message.options.getChannel('channel') || message.channel
        if (channel.isThread()) {
            clientPermissions(message, ['MANAGE_MESSAGES', 'EMBED_LINKS'])
            let yes = []
            let no = []
            for (const [, overwrite] of channel.permissionOverwrites.cache) {
                if (overwrite.type === 'role') {
                    console.log('role')
                    if (overwrite.allow.has('SEND_MESSAGES')) {
                        yes.push(`<@&${overwrite.id}>`)
                    } else {
                        no.push(`<@&${overwrite.id}>`)
                    }
                }
            }
            const embed = new MessageEmbed()
                .setTitle("Channel Info")
                .setColor('WHITE')
                .setFields({name: "Channel Name", value: Formatters.codeBlock(channel.name), inline: true},
                    {name: "Category", value: Formatters.codeBlock(channel.parent.name), inline: true},
                    {name: "Channel ID", value: Formatters.codeBlock(channel.id)},
                    {name: "Created At", value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {dateStyle: 'long', timeStyle: 'long'}).format(channel.createdAt)), inline: true},
                    {name: "Archived At", value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {dateStyle: 'long', timeStyle: 'long'}).format(channel.archivedAt)), inline: true},
                    {name: "Overwrites", value: `**Permitted**\n${yes.join(' ')}\n**Denied**\n${no.join(' ')}`},
                    {name: "Owner", value: Formatters.codeBlock(channel.fetchOwner().name), inline: true},
                    {name: "Locked", value: Formatters.codeBlock(channel.locked), inline: true},
                    {name: "Pins", value: Formatters.codeBlock((await channel.messages.fetchPinned()).size), inline: true},
                    {name: "Archived", value: Formatters.codeBlock(channel.archived), inline: true},
                    {name: "Type", value: Formatters.codeBlock(channel.type), inline: true})
            await message.reply({embeds: [embed]})
        } else if (channel.isVoice()) {
            clientPermissions(message, ['EMBED_LINKS'])
            let yes = []
            let no = []
            for (const [, overwrite] of channel.permissionOverwrites.cache) {
                if (overwrite.type === 'role') {
                    if (overwrite.allow.has('SEND_MESSAGES')) {
                        yes.push(`<@&${overwrite.id}>`)
                    } else {
                        no.push(`<@&${overwrite.id}>`)
                    }
                }
            }
            const embed = new MessageEmbed()
                .setTitle("Channel Info")
                .setFields({name: "Channel Name", value: Formatters.codeBlock(channel.name), inline: true},
                    {name: "Category", value: Formatters.codeBlock(channel.parent.name), inline: true},
                    {name: "Channel ID", value: Formatters.codeBlock(channel.id)},
                    {name: "Created At", value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {dateStyle: 'long', timeStyle: 'long'}).format(channel.createdAt))},
                    {name: "Overwrites", value: `**Permitted**\n${yes.join(' ')}\n**Denied**\n${no.join(' ')}`},
                    {name: "Bitrate", value: Formatters.codeBlock(channel.bitrate), inline: true},
                    {name: "Position", value: Formatters.codeBlock((channel.position)), inline: true},
                    {name: "User Limit", value: Formatters.codeBlock(channel.userLimit), inline: true},
                    {name: "Region", value: Formatters.codeBlock(channel.rtcRegion), inline: true},
                    {name: "Synced", value: Formatters.codeBlock(channel.permissionsLocked), inline: true},
                    {name: "Type", value: Formatters.codeBlock(channel.type), inline: true})
            await message.reply({embeds: [embed]})
        }
        else if (channel.isText()) {
            clientPermissions(message, ['EMBED_LINKS', 'MANAGE_MESSAGES', 'MANAGE_GUILD', 'MANAGE_WEBHOOKS'])
            let yes = []
            let no = []
            for (const [, overwrite] of channel.permissionOverwrites.cache) {
                if (overwrite.type === 'role') {
                    if (overwrite.allow.has('SEND_MESSAGES')) {
                        yes.push(`<@&${overwrite.id}>`)
                    } else {
                        no.push(`<@&${overwrite.id}>`)
                    }
                }
            }
            const embed = new MessageEmbed()
                .setTitle("Channel Info")
                .setFields({name: "Channel Name", value: Formatters.codeBlock(channel.name), inline: true},
                    {name: "Category", value: Formatters.codeBlock(channel.parent.name), inline: true},
                    {name: "Channel ID", value: Formatters.codeBlock(channel.id)},
                    {
                        name: "Created At",
                        value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {
                            dateStyle: 'long',
                            timeStyle: 'long'
                        }).format(channel.createdAt))
                    },
                    {name: "Topic", value: Formatters.codeBlock(channel.topic)},
                    {name: "Overwrites", value: `**Permitted**\n${yes.join(' ')}\n**Denied**\n${no.join(' ')}`},
                    {name: "Slow Mode", value: Formatters.codeBlock(channel.rateLimitPerUser), inline: true},
                    {
                        name: "Pins",
                        value: Formatters.codeBlock((await channel.messages.fetchPinned()).size),
                        inline: true
                    },
                    {name: "Invites", value: Formatters.codeBlock((await channel.fetchInvites()).size), inline: true},
                    {
                        name: "Threads",
                        value: Formatters.codeBlock(`${(await channel.threads.fetchActive()).threads.size} Active, ${(await channel.threads.fetchArchived()).threads.size} Archived`),
                        inline: true
                    },
                    {name: "Webhooks", value: Formatters.codeBlock((await channel.fetchWebhooks()).size), inline: true},
                    {name: "Position", value: Formatters.codeBlock(channel.position), inline: true},
                    {name: "Synced", value: Formatters.codeBlock(channel.permissionsLocked), inline: true},
                    {name: "NSFW", value: Formatters.codeBlock(channel.nsfw), inline: true},
                    {name: "Type", value: Formatters.codeBlock(channel.type), inline: true})
            await message.reply({embeds: [embed]})
        } else if (channel.type === 'GUILD_CATEGORY') {
            clientPermissions(message, ['EMBED_LINKS'])
            let yes = []
            let no = []
            for (const [, overwrite] of channel.permissionOverwrites.cache) {
                if (overwrite.type === 'role') {
                    if (overwrite.allow.has('SEND_MESSAGES')) {
                        yes.push(`<@&${overwrite.id}>`)
                    } else {
                        no.push(`<@&${overwrite.id}>`)
                    }
                }
            }
            const embed = new MessageEmbed()
                .setTitle("Channel Info")
                .setFields({name: 'Channel Name', value: Formatters.codeBlock(channel.name), inline: true},
                    {name: "Channel ID", value: Formatters.codeBlock(channel.id), inline: true},
                    {
                        name: "Created At",
                        value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {
                            dateStyle: 'long',
                            timeStyle: 'long'
                        }).format(channel.createdAt))
                    },
                    {name: "Overwrites", value: `**Permitted**\n${yes.join(' ')}\n**Denied**\n${no.join(' ')}`},
                    {name: "Position", value: Formatters.codeBlock(channel.position), inline: true},
                    {name: "Type", value: Formatters.codeBlock(channel.type), inline: true})
            await message.reply({embeds: [embed]})
        }
    }
}