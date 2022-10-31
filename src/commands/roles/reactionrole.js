const {SlashCommandBuilder, PermissionsBitField} = require('discord.js');
const {pool} = require("../../database");
const emote = require('../../emojis.json')

const {resolveMessage} = require("../../structures/resolvers");
const {clientPermissions, userPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("reactionrole")
        .setDescription("Allows you to set up a reaction role")
        .addStringOption(option => option
            .setName("message")
            .setDescription("The message to add the reaction role to")
            .setRequired(true))
        .addStringOption(option =>
            option.setName("emoji")
            .setDescription("The emoji for the reaction")
                .setRequired(true))
        .addRoleOption(option => option
            .setName("role")
            .setDescription("The role to add when the reaction role gets triggered")
            .setRequired(true))
        .addStringOption(option => option
            .setName("type")
            .setDescription("The type of reaction role to set up")
            .addChoices({name: "reaction", value: "reaction"}, {name: "toggle", value: "toggle"}, {name: "once", value: "once"})
            .setRequired(true))
        .addRoleOption(option => option
            .setName("blacklist")
            .setDescription("The optional role that is needed to use the reaction role")),
    async execute(message) {
        userPermissions(message, PermissionsBitField.Flags.ManageRoles);
        clientPermissions(message, [PermissionsBitField.Flags.AddReactions]);
        const db = await pool.connect()
        const msg = await resolveMessage(message, message.options.getString("message"))
        const emoji = message.options.getString("emoji")
        const role = await message.options.getRole("role")
        const type = message.options.getString("type")
        const blacklist = message.options.getRole("blacklist")
        const unicode = []
        for(const key in emote) {
            if (emote.hasOwnProperty(key)) {
                unicode.push(emote[key].emoji)
            }
        }
        if (unicode.includes(emoji) || message.guild.emojis.cache.get(/<?(a)?:?(\w{2,32}):(\d{17,19})>?/.exec(emoji)?.[3])) {
            const emote = message.guild.emojis.cache.get(/<?(a)?:?(\w{2,32}):(\d{17,19})>?/.exec(emoji)?.[3])?.id ?? emoji
            const result = await db.query("SELECT type FROM reaction WHERE guild = $1 and message = $2 and channel = $3 and role = $4", [message.guildId, msg.id, message.channelId, role.id])
            if (!result.rows.length) {
                await db.query("INSERT INTO reaction(guild, role, channel, emote, blacklist, type, message) VALUES($1, $2, $3, $4, $5, $6, $7)", [message.guildId, role.id, message.channelId, emote, blacklist?.id || 0, type, msg.id])
                await msg.react(emote)
                await message.reply('Reaction Role Set Successfully!')
            } else {
                await db.query("DELETE FROM reaction WHERE guild = $1 and message = $2 and channel = $3 and role = $4", [message.guildId, msg.id, message.channelId, role.id])
                if (result.rows.length === 1) {
                    await msg.reactions.resolve(emote)?.remove()
                }
                message.reply("Reaction Role Deleted Successfully!")
            }
        } else {
            message.reply("I could not find that emoji!")
        }
        await db.release()
    }
}