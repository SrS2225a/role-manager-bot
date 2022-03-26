const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {userPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("update")
        .setDescription("Allows you to update any members various stats")
        .addSubcommand(subcommand => subcommand
            .setName("rank")
            .setDescription("Updates someones rank for the leveling system")
            .addUserOption(option => option
                .setName("member")
                .setDescription("The member to update the rank for")
                .setRequired(true))
            .addIntegerOption(option => option
                .setName("rank")
                .setDescription("The rank to update to")
                .setRequired(true)))
        .addSubcommand(subcommand => subcommand
            .setName("messages")
            .setDescription("Updates a members sent messages")
            .addUserOption(option => option
                .setName("member")
                .setDescription("The member to update messages for")
                .setRequired(true))
            .addChannelOption(option => option
                .setName("channel")
                .setDescription("The channel that the updated messages should apply for")
                .setRequired(true))
            .addIntegerOption(option => option
                .setName("messages")
                .setDescription("The amount of messages to update to")
                .setRequired(true)))
        .addSubcommand(subcommand => subcommand
            .setName("invites")
            .setDescription("Updates a members invites")
            .addUserOption(option => option
                .setName("member")
                .setDescription("The member to update invites for")
                .setRequired(true))
            .addStringOption(option => option
                .setName("invite")
                .setDescription("The invite of the member to update")
                .setRequired(true))
            .addIntegerOption(option => option
                .setName("leaves")
                .setDescription("The amount of leaves to update to")
                .setRequired(true))
            .addIntegerOption(option => option
                .setName("fakes")
                .setDescription("The amount of fakes to update to")
                .setRequired(true)))
        .addSubcommand(subcommand => subcommand
            .setName("partners")
            .setDescription("Updates a members completed partnerships")
            .addUserOption(option => option
                .setName("member")
                .setDescription("The member to update the partnerships for")
                .setRequired(true))
            .addIntegerOption(option => option
                .setName("partners")
                .setDescription("The partners to update to")
                .setRequired(true))),
    async execute(message) {
        userPermissions(message, ["MANAGE_GUILD"])
        const db = await pool.connect()
        if (message.options.getSubcommand() === "rank") {
            const member = await message.options.getMember("member")
            const rank = await message.options.getInteger("rank")
            if (rank < 0) {return message.reply("Integer cannot be less than 0!")}
            const check = await db.query("SELECT guild_id FROM levels WHERE guild_id = $1 and user_id = $2", [message.guildId, member.id])
            if (check.rows.length) {
                await db.query("UPDATE levels SET lvl = $1, exp = $2 WHERE guild_id = $3 and user_id = $4", [rank, 0, message.guildId, member.id])
                await message.reply(`Levels updated successfully for ${member.user.username}!`)
            } else {
                await db.query("INSERT INTO levels(guild_id, user_id, exp, lvl) VALUES($1, $2, $3, $4)", [message.guildId, member.id, 0, rank])
                await message.reply(`Levels updated successfully for ${member.user.username}!`)
            }
        } else if (message.options.getSubcommand() === "messages") {
            const member = await message.options.getMember("member")
            const channel = await message.options.getChannel("channel")
            const messages = await message.options.getInteger("messages")
            if (messages < 0) {return message.reply("Integer cannot be less thank 0!")}
            const check = await db.query("SELECT channel FROM message WHERE guild = $1 and member = $2 and channel = $3", [message.guildId, member.id, channel.id])
            if (check.rows.length) {
                await db.query("UPDATE message SET messages = $1 WHERE guild = $2 and member = $3 and channel= $4", [messages, message.guildId, member.id, channel.id])
                await message.reply(`Messages updated successfully for ${member.user.username}!`)
            } else {
                await db.query("INSERT INTO message(guild, messages, day, member, channel) VALUES($1, $2, $3, $4, $5)", [message.guildId, messages, new Date(), member.id, channel.id])
                await message.reply(`Messages updated successfully for ${member.user.username}!`)
            }
        } else if (message.options.getSubcommand() === "invites") {
            const member = await message.options.getMember("member")
            const invite = await message.options.getString("invite")
            const leaves = await message.options.getInteger("leaves")
            const fakes = await message.options.getInteger("fakes")
            if (leaves < 0 || fakes < 0) {return message.reply("Integer cannot be less thank 0!")}
            const check = await db.query("SELECT member FROM invite WHERE guild = $1 and member = $2 and invite = $3", [message.guildId, member.id, invite])
            if (check.rows.length) {
                await db.query("UPDATE invite SET amount2 = $1, amount3 = $2 WHERE guild = $1 and member = $2 and invite = $3", [leaves, fakes, message.guildId, member.id, invite])
                await message.channel.send(`Invite updated successfully for ${member.user.username}`)
            } else {
                await message.channel.send(`${member.username} does not have any invites yet or this current invite!`)
            }
        } else if (message.options.getSubcommand() === "partners") {
            const member = await message.options.getMember("member")
            const partners = await message.options.getInteger("partners")
            if (partners < 0) {return message.reply("Integer cannot be less than 0!")}
            const check = await db.query("SELECT number FROM partner WHERE guild = $1 and member = $2", [message.guildId, member.id])
            if (check.rows.length) {
                await db.query("UPDATE partner SET number = $1 WHERE guild = $2 and member = $3", [partners, message.guildId, member.id])
                await message.channel.send(`Partnerships updated successfully for ${member.user.username}!`)
            } else {
                await db.query("INSERT INTO partner(guild, member, number) VALUES($1, $2, $3)", [message.guildId, member.id, partners])
                await message.channel.send(`Partnerships updated successfully for ${member.user.username}!`)
            }
        } else {
            message.reply("Invalid sub-command!")
        }
        await db.release()
    }
}