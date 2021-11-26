const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {Formatters, MessageEmbed, Permissions} = require("discord.js");
const {rolePermissions, userPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("club")
        .setDescription("Allows you to manage clubs")
        .addSubcommand(subcommand =>
        subcommand
            .setName("setup")
            .setDescription("Sets up clubs")
            .addChannelOption(option =>
            option.setName("channel")
                .setDescription("The channel of which new clubs available to join should be posted to")
                .setRequired(true))
            .addChannelOption(option =>
            option.setName("category")
                .setDescription("The category of where a new club channel should be created under")
                .setRequired(true))
            .addRoleOption(option =>
            option.setName("role")
                .setDescription("The role required to create clubs")
                .setRequired(false)))
        .addSubcommand(subcommand =>
        subcommand
            .setName("create")
            .setDescription("Allows you to create a club")
            .addStringOption(option =>
            option.setName("name")
                .setDescription("The name of the club")
                .setRequired(true))
            .addStringOption(option =>
            option.setName("description")
                .setDescription("The description of what your club is about")
                .setRequired(true))
            .addStringOption(option =>
            option.setName("graphic")
                .setDescription("The url to your clubs graphic")
                .setRequired(true))
            .addUserOption(option =>
            option.setName("representative1")
                .setDescription("The representative of the club")
                .setRequired(true))
            .addUserOption(option =>
                option.setName("representative2")
                    .setDescription("The representative of the club")
                    .setRequired(false))
            .addUserOption(option =>
                option.setName("representative3")
                    .setDescription("The representative of the club")
                    .setRequired(false)))
        .addSubcommand(subcommand =>
        subcommand
            .setName("edit")
            .setDescription("Edits a created club")
            .addChannelOption(option => option
                .setName("channel")
                .setDescription("The channel of the club to edit")
                .setRequired(true))
            .addStringOption(option =>
                option.setName("name")
                    .setDescription("The name of the club")
                    .setRequired(true))
            .addStringOption(option =>
                option.setName("description")
                    .setDescription("The description of what your club is about")
                    .setRequired(true))
            .addStringOption(option =>
                option.setName("graphic")
                    .setDescription("The url to your clubs graphic")
                    .setRequired(true))
            .addUserOption(option =>
                option.setName("representative1")
                    .setDescription("The representative of the club")
                    .setRequired(true))
            .addUserOption(option =>
                option.setName("representative2")
                    .setDescription("The representative of the club")
                    .setRequired(false))
            .addUserOption(option =>
                option.setName("representative3")
                    .setDescription("The representative of the club")
                    .setRequired(false)))
        .addSubcommand(subcommand =>
        subcommand
            .setName("delete")
            .setDescription("Deletes a created club")
            .addChannelOption(option =>
            option.setName("club")
                .setDescription("The channel of the club to delete")
                .setRequired(true)))
        .addSubcommand(subcommand =>
        subcommand
            .setName("blacklist")
            .setDescription("Allows you to blacklist someone from a club")
            .addChannelOption(option =>
            option.setName("club")
                .setDescription("The channel of the club to blacklist the user for")
                .setRequired(true))
            .addUserOption(option =>
            option.setName("user")
                .setDescription("The user to blacklist")
                .setRequired(true))),
    async execute(message) {
        const db = await pool.connect()
        if (message.options.getSubcommand() === "setup") {
            const channel = await message.options.getChannel("channel")
            const category =  await message.options.getChannel("channel")
            if (!category.type === 'GUILD_CATEGORY') {return message.reply("The category argument must be a valid category channel")}
            const role = await message.options.getRole("role")
            const type = await db.query("SELECT system FROM leveling WHERE guild = $1 and system= $2", [message.guildId, 'points'])
            const check1 = await db.query("SELECT type FROM leveling WHERE guild = $1 and system = $2 and role = $3 and level = $4 and type = $5 and difficulty = $5", [message.guildId, 'points', category.id, channel.id, role?.id])
            if (check1.rows.length) {
                await db.query("DELETE FROM leveling WHERE guild = $1 and system = $2 and role = $3 and difficulty = $4", [message.guildId, 'points', category.id, channel.id, role?.id])
                await message.channel.send("Clubs requirement deleted successfully!")
            } else if (!type.rows.length) {
                await db.query("INSERT INTO leveling(guild, system, role, level, difficulty) VALUES($1, $2, $3, $4, $5)", [message.guildId, 'points', category.id, channel.id, role?.id])
                await message.channel.send("Clubs requirement set successfully!")
            } else {
                await db.query("UPDATE leveling SET role = $1, level = $2, difficulty = $3 WHERE guild = $4 and system = $5", [category.id, channel.id, role?.id, message.guildId, 'points'])
                await message.channel.send("Club requirement updated successfully!")
            }
        } else if (message.options.getSubcommand() === "create") {
            const db = await pool.connect()
            const name = await message.options.getString("name")
            const description = await message.options.getString("description")
            const graphic = await message.options.getString("url")
            if (/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/.test(graphic)) {return message.reply("The graphic argument must be a valid url")}
            const owners = [await message.options.getMember("representative1"), await message.options.getMember("representative2"), await message.options.getMember("representative3")].filter(item => typeof item === 'string')
            const club = await db.query("SELECT level, role, difficulty FROM leveling WHERE guild = $1 and system = $2", [message.guildId, 'points'])
            if (club.rows.length) {
                rolePermissions(message, [club?.rows[0].difficulty || message.guild.roles.everyone.id])
                await message.reply(`Creating the club with the name ${name}!`)
                const embed = new MessageEmbed()
                    .setTitle(`${name} Club`)
                    .setDescription(`${description} \n\n**Representatives:** \n${owners.map(owner => Formatters.userMention(owner?.user.id)).join(' ')}\n\n React with ☑ to join`)
                    .setImage(graphic)
                const created = await message.guild.roles.create({
                    name: name,
                    color: 'RANDOM'
                })
                let overwrites = [{
                    id: created.id,
                    allow: [Permissions.FLAGS.VIEW_CHANNEL]
                }, {
                    id: message.guild.roles.everyone.id,
                    deny: [Permissions.FLAGS.VIEW_CHANNEL]
                }]
                const give = await message.guild.roles.fetch(club.rows[0].difficulty)
                for (const owner of owners) {
                    await owner?.roles.add(created)
                    await owner?.roles.add(give)
                    overwrites.push({
                        id: owner?.user.id,
                        allow: [Permissions.FLAGS.MENTION_EVERYONE, Permissions.FLAGS.MANAGE_MESSAGES, Permissions.FLAGS.MANAGE_CHANNELS],
                    })
                }
                const clubChannel = await message.guild.channels.create(name, {
                    type: 'GUILD_TEXT',
                    topic: description,
                    parent: await message.guild.channels.fetch(club.rows[0].role),
                    permissionOverwrites: overwrites
                })
                const channel = await message.guild.channels.fetch(club.rows[0].level)
                const sent = await channel.send({embeds: [embed]})
                await sent.react('☑')
                await db.query("INSERT INTO club(channel, message, role, guild) VALUES($1, $2, $3, $4)", [clubChannel.id, sent.id, created.id, message.guildId])
                await db.query("INSERT INTO reaction(guild, role, channel, message, emote, blacklist, type) VALUES($1, $2, $3, $4, $5, $6, $7)", [message.guildId, created.id, sent.channel.id, sent.id, '☑', 0, 'club'])
                const started = await clubChannel.send(`Welcome to your new club ${owners.map(owner => Formatters.userMention(owner.id)).join(' ')}! To get started please read the instructions in <#${channel.id}>. Have fun!`)
                await started.pin()
                await message.editReply({content: `Club ${name} created successfully!`})
            } else {
                await message.channel.reply("Clubs has not been set up yet by this guild!")
            }
        } else if (message.options.getSubcommand() === "edit") {
            const channel = await message.options.getChannel("channel")
            const name = await message.options.getString("name")
            const description = await message.options.getString("description")
            const graphic = await message.options.getString("url")
            if (/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/.test(graphic)) {return message.reply("The graphic argument must be a valid url")}
            const owners = [await message.options.getMember("representative1"), await message.options.getMember("representative2"), await message.options.getMember("representative3")]
            const club = await db.query("SELECT channel, message, role FROM club WHERE guild = $1 and channel = $2", [message.guildId, channel.id])
            const check2 = await db.query("SELECT level, difficulty FROM leveling WHERE guild = $1 and system = $2", [message.guildId, 'points'])
            if (club.rows.length) {
                rolePermissions(message, check2.rows[0].difficulty || message.guild.roles.everyone.id)
                await message.reply(`Editing the club with the name ${name}`)
                const clubChannel = await message.guild.channels.fetch(check2.rows[0].level)
                const msg = await clubChannel.messages.fetch(club.rows[0].message)
                const role = await message.guild.roles.fetch(club.rows[0].role)
                const newChannel = await message.guild.channels.fetch(club.rows[0].channel)
                let overwrites = [{
                    id: role.id,
                    allow: [Permissions.FLAGS.VIEW_CHANNEL]
                }, {
                    id: msg.guild.roles.everyone.id,
                    deny: [Permissions.FLAGS.VIEW_CHANNEL]
                }]
                const embedDescriptionMention = /<[@]?[0-9]+>/g.exec(msg.embeds[0].description)
                for (const host of embedDescriptionMention) {
                    const user = await message.guild.members.fetch(host.replace(/[^0-9]*/g, '')).catch(undefined)
                    if (user) {
                        if (!owners.includes(user.id)) {
                            await user.roles.remove(role)
                        } else {
                            for (const owner of owners) {
                                await owner.roles.add(role)
                                overwrites.update({
                                    id: owner.id,
                                    allow: [Permissions.FLAGS.MENTION_EVERYONE, Permissions.FLAGS.MANAGE_MESSAGES, Permissions.FLAGS.MANAGE_CHANNELS]
                                })
                            }
                        }
                    }
                }
                await role.edit({name: name})
                await newChannel.edit({
                    name: name,
                    topic: description,
                    permissionOverwrites: overwrites
                })
                const embed = new MessageEmbed()
                    .setTitle(`${name} Club`)
                    .setDescription(` ${description} \n\n**Representatives:** \n${owners.map(member => Formatters.userMention(member.id))} \n\n React with ☑ to join`)
                    .setImage(graphic)
                await msg.edit({embeds: [embed]})
                await message.editReply({content: `Club ${name} edited successfully!`})
            } else {
                await message.channel.send("I could not find that club!")
            }
        } else if (message.options.getSubcommand() === "delete") {
            const channel = await message.options.getChannel("club")
            const del = await db.query("SELECT channel, message, role FROM club WHERE guild = $1 and channel = $2", [message.guildId, channel.id])
            if (del.rows.length) {
                const owner = await db.query("SELECT level, difficulty FROM leveling WHERE guild = $1 and system = $2", [message.guildId, 'points'])
                rolePermissions(message, [owner.rows[0].difficulty || message.guild.roles.everyone.id])
                await message.reply(`Deleting the club with the name ${channel.name}`)
                const menu = await message.guild.roles.fetch(owner.rows[0].difficulty)
                const main = await message.guild.channels.fetch(owner.rows[0].level)
                const msg = await main.messages.fetch(del.rows[0].message)
                const chan = await message.guild.channels.fetch(del.rows[0].channel)
                const give = await message.guild.roles.fetch(del.rows[0].role)
                const embedDescriptionMention = /<[@]?[0-9]+>/g.exec(msg.embeds[0].description)
                for (const host of embedDescriptionMention) {
                    const user = await message.guild.members.fetch(host.replace(/[^0-9]*/g, '')).catch(undefined)
                    if (user) {
                        await user.roles.remove(menu)
                    }
                }
                await chan.delete()
                await msg.delete()
                await give.delete()
                await db.query("DELETE FROM club WHERE guild = $1 and channel = $2", [message.guildId, chan.id])
                await db.query("DELETE FROM reaction WHERE role = $1 and channel = $2 and message = $3 and guild = $4", [menu.id, message.channel.id, chan.id, message.guildId])
                await message.editReply({content: `Club ${chan.name} deleted successfully!`})
            } else {
                await message.reply(`This club does not exist, create one with ``/club create``!`)
            }
        } else if (message.options.getSubcommand() === "blacklist") {
            const member = await message.options.getMember("member")
            const channel = await message.options.getChannel("channel")
            const reason = await message.options.getString("reason") || undefined
            const club = await db.query("SELECT message, role FROM club WHERE guild = $1 and channel= $2", [message.guildId, channel.id])
            const check3 = await db.query("SELECT difficulty FROM leveling WHERE guild = $1", [message.guildId])
            if (club.rows.length) {
                userPermissions(message, ["MANAGE_GUILD", "MANAGE_MESSAGES"])
                const ch = await db.query("SELECT member FROM owner WHERE guild = $1 and member = $2 and message = $3 and type = $4", [message.guildId, member.id, club.rows[0].role, 'club'])
                if (!ch.rows.length) {
                    let remove = false
                    const give = await message.guild.roles.fetch(club.rows[0].message)
                    if (give) {remove = true
                        await member.role.remove(give)}
                    await db.query("INSERT INTO owner(guild, member, type, message) VALUES($1, $2, $3, $4)", [message.guildId, member.id, 'club', club.rows[0].role])
                    await member.send(`You have been blacklisted from joining the club <#${channel.id}> in the server ${message.guild.name} for the reason: ${reason || 'bye'}. ${remove ? "You have automatically been removed from this club!" : ""}`).catch(null)
                    await message.channel.send(`User blacklisted successfully from club ${channel.name}`)
                } else {
                    await db.query("DELETE FROM owner WHERE guild = $1 and member= $2 and message= $3 and type = $4", [message.guildId, member.id, club.rows[0].role, 'club'])
                    await message.reply(`User unblacklisted successfully from club ${channel.name}`)
                }
            } else {
                await message.reply("This club does not exist!")
            }
        }
        await db.release()
    }
}