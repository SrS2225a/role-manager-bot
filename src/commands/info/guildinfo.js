const {MessageEmbed, Formatters} = require("discord.js");
const {SlashCommandBuilder} = require("@discordjs/builders");
const {clientPermissions} = require("../../structures/permissions");

module.exports = {
    data: new SlashCommandBuilder()
        .setName('guildinfo')
        .setDescription("Shows info about the current guild"),
    async execute(message) {
        clientPermissions(message, ["EMBED_LINKS"]);
        const guild = message.guild
        let channel_count = 0
        let voice_count = 0
        let category_count = 0
        let stage_count = 0
        let thread_count = 0
        for (const [, channel] of guild.channels.cache) {
            if (channel.type === 'GUILD_TEXT' ||  'GUILD_NEWS' || 'GUILD_STORE' || 'UNKNOWN') {
                channel_count++
            }
            if (channel.type === 'GUILD_VOICE') {
                voice_count++
            }
            if (channel.type === 'GUILD_CATEGORY') {
                category_count++
            }
            if (channel.type === 'GUILD_STAGE_VOICE') {
                stage_count++
            }
            if (channel.isThread()) {
                thread_count++
            }

        }
        const owner = await guild.members.fetch(guild.ownerId)
        const premiumSince = guild.members.cache
            .map(member => member.premiumSince)
            .filter(x => x)
        const roles = guild.roles.cache
            .map(roles => roles.id)
            .filter(x => x)
        const emotes = guild.emojis.cache
            .map(emoji => emoji.id)
            .filter(x => x)
        const stickers = guild.stickers.cache
            .map(emoji => emoji.id)
            .filter(x => x)
        const embed = new MessageEmbed()
            .setTitle("Guild Info")
            .setColor('WHITE')
            .setThumbnail(message.guild.iconURL())
            .addFields({name: "Guild Name", value: Formatters.codeBlock(guild.name), inline: true},
                {name: "Owner", value: Formatters.codeBlock(owner.user.username + '#' + owner.user.discriminator), inline: true},
                {name: "Guild ID", value: Formatters.codeBlock(guild.id), inline: false},
                {name: "Created At", value: Formatters.codeBlock(Intl.DateTimeFormat('en-US', {dateStyle: 'long', timeStyle: 'long'}).format(guild.createdAt)), inline: false},
                {name: "Boosts", value: Formatters.codeBlock(`Level ${guild.premiumTier} With ${guild.premiumSubscriptionCount} Boosts And ${premiumSince.length} Actual`), inline: false},
                {name: "Features", value: Formatters.codeBlock(guild.features?.join(', ') || "None"), inline: false},
                {name: "Text Channels", value: Formatters.codeBlock(`${channel_count} Channels, ${thread_count} Threads`), inline: true},
                {name: "Voice Channels", value: Formatters.codeBlock(`${voice_count} Channels, ${stage_count} Stages`),inline: true},
                {name: "Emotes", value: Formatters.codeBlock(`${emotes.length} Emotes, ${stickers.length} Stickers`), inline: true},
                {name: "Members", value: Formatters.codeBlock(guild.memberCount), inline: true},
                {name: "Roles", value: Formatters.codeBlock(roles.length), inline: true},
                {name: "Categories", value: Formatters.codeBlock(category_count), inline: true},
                {name: "Verification", value: Formatters.codeBlock(guild.verificationLevel), inline: true},
                {name: "System Channel", value: Formatters.codeBlock(guild.systemChannel.name), inline: true},
                {name: "Vanity URL", value: Formatters.codeBlock(guild.vanityURLCode), inline: true},
                {name: "2FA", value: Formatters.codeBlock(guild.mfaLevel), inline: true},
                {name: "Explicit Content", value: Formatters.codeBlock(guild.explicitContentFilter), inline: true},
                {name: "Notifications", value: Formatters.codeBlock(guild.defaultMessageNotifications), inline: true},
                {name: "Splash", value: guild.splash?`[Click Here](${guild.splashURL()})`:Formatters.codeBlock('False'), inline: true},
                {name: "Banner", value: guild.banner?`[Click Here](${guild.bannerURL()})`:Formatters.codeBlock('False'), inline: true})
        if (guild.description) {embed.setDescription(guild.description)}
        await message.reply({embeds: [embed]});

    }
}