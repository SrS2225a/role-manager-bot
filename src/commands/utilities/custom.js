const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {rolePermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("custom")
        .setDescription("Lets you manage your custom ")
        .addSubcommandGroup(group => group
            .setName("create")
            .setDescription("Allows you to create a custom role, text or voice channel")
            .addSubcommand(subcommand => subcommand
                .setName("role")
                .setDescription("Creates a custom role")
                .addStringOption(option => option
                    .setName("name")
                    .setDescription("The name of the role")
                    .setRequired(true))
                .addStringOption(option => option
                    .setName("color")
                    .setDescription("The color of the role")
                    .setRequired(true)))
            .addSubcommand(subcommand => subcommand
                .setName("text")
                .setDescription("Creates a custom text channel")
                .addStringOption(option => option
                    .setName("name")
                    .setDescription("The name of the text channel")
                    .setRequired(true))
                .addStringOption(option => option
                    .setName("topic")
                    .setDescription("The topic of the text channel")
                    .setRequired(true)))
            .addSubcommand(subcommand => subcommand
                .setName("voice")
                .setDescription("Creates a custom voice channel")
                .addStringOption(option => option
                    .setName("name")
                    .setDescription("The name of the voice channel")
                    .setRequired(true))
                .addIntegerOption(option => option
                    .setName("limit")
                    .setDescription("The limit of the voice channel")
                    .setRequired(true))))
        .addSubcommandGroup(group => group
            .setName("delete")
            .setDescription("Allows you to delete a custom role, text or voice channel")
            .addSubcommand(subcommand => subcommand
                .setName("role")
                .setDescription("Deletes a custom role"))
            .addSubcommand(subcommand => subcommand
                .setName("text")
                .setDescription("Deletes a custom text channel"))
            .addSubcommand(subcommand => subcommand
                .setName("voice")
                .setDescription("Deletes a custom voice channel")))
        .addSubcommandGroup(group => group
            .setName("edit")
            .setDescription("Allows you to edit a custom role, text or voice channel")
            .addSubcommand(subcommand => subcommand
                .setName("role")
                .setDescription("Edits a custom role")
                .addStringOption(option => option
                    .setName("name")
                    .setDescription("The new name of the role")
                    .setRequired(true))
                .addStringOption(option => option
                    .setName("color")
                    .setDescription("The new color of the role")
                    .setRequired(true)))
            .addSubcommand(subcommand => subcommand
                .setName("text")
                .setDescription("Edits a custom text channel")
                .addStringOption(option => option
                    .setName("name")
                    .setDescription("The new name of the text channel")
                    .setRequired(true))
                .addStringOption(option => option
                    .setName("topic")
                    .setDescription("The new topic of the text channel")
                    .setRequired(true)))
            .addSubcommand(subcommand => subcommand
                .setName("voice")
                .setDescription("Edits a custom voice channel")
                .addChannelOption(option => option
                    .setName("name")
                    .setDescription("The voice channel to edit")
                    .setRequired(true))
                .addIntegerOption(option => option
                    .setName("limit")
                    .setDescription("The new limit of the voice channel")
                    .setRequired(true))))
        .addSubcommandGroup(group => group
            .setName("give")
            .setDescription("Allows you to give a custom role, text or voice channel")
            .addSubcommand(subcommand => subcommand
                .setName("role")
                .setDescription("Gives a custom role")
                .addUserOption(option => option
                    .setName("user")
                    .setDescription("The user to give the role to")
                    .setRequired(true)))
            .addSubcommand(subcommand => subcommand
                .setName("text")
                .setDescription("Gives a custom text channel")
                .addUserOption(option => option
                    .setName("user")
                    .setDescription("The user to give the text channel to")
                    .setRequired(true)))
            .addSubcommand(subcommand => subcommand
                .setName("voice")
                .setDescription("Gives a custom voice channel")
                .addUserOption(option => option
                    .setName("user")
                    .setDescription("The user to give the voice channel to")
                    .setRequired(true))))
        .addSubcommandGroup(group => group
            .setName("configure")
            .setDescription("Modifies who is allowed to create a custom role, voice or text channel")
            .addSubcommand(subcommand => subcommand
                .setName("role")
                .setDescription("Modifies who is allowed to create a custom role")
                .addRoleOption(role => role
                    .setName("role")
                    .setDescription("The role that is allowed to create a custom role")
                    .setRequired(true)
                )
                .addRoleOption(role => role
                    .setName("position")
                    .setDescription("The position of the role")
                    .setRequired(true)
                )
                .addIntegerOption(option => option
                    .setName("limit")
                    .setDescription("The maximum amount of users the custom role can be added to")
                    .setRequired(true)
                )
                .addStringOption(option => option
                    .setName("tag")
                    .setDescription("The tag of the custom role")
                    .setRequired(true))
                .addBooleanOption(option => option
                    .setName("remove")
                    .setDescription("Whether or not the role should be deleted upon the user losing the required role")
                    .setRequired(true)))
            .addSubcommand(subcommand => subcommand
                .setName("text")
                .setDescription("Modifies who is allowed to create a custom text channel")
                .addRoleOption(role => role
                    .setName("role")
                    .setDescription("The role that is allowed to create a custom text channel")
                    .setRequired(true)
                )
                .addChannelOption(role => role
                    .setName("position")
                    .setDescription("The position of the role")
                    .setRequired(true)
                )
                .addIntegerOption(option => option
                    .setName("limit")
                    .setDescription("The maximum amount of users the custom text channel can be added to")
                    .setRequired(true)
                )
                .addStringOption(option => option
                    .setName("tag")
                    .setDescription("The tag of the custom text channel")
                    .setRequired(true))
                .addBooleanOption(option => option
                    .setName("remove")
                    .setDescription("Whether or not the text channel should be deleted upon the user losing the required role")
                    .setRequired(true)))
            .addSubcommand(subcommand => subcommand
                .setName("voice")
                .setDescription("Modifies who is allowed to create a custom voice channel")
                .addRoleOption(role => role
                    .setName("role")
                    .setDescription("The role that is allowed to create a custom voice channel")
                    .setRequired(true)
                )
                .addChannelOption(role => role
                    .setName("position")
                    .setDescription("The position of the role")
                    .setRequired(true)
                )
                .addIntegerOption(option => option
                    .setName("limit")
                    .setDescription("The maximum amount of users the custom voice channel can be added to")
                    .setRequired(true)
                )
                .addStringOption(option => option
                    .setName("tag")
                    .setDescription("The tag of the custom voice channel")
                    .setRequired(true))
                .addBooleanOption(option => option
                    .setName("remove")
                    .setDescription("Whether or not the voice channel should be deleted upon the user losing the required role")
                    .setRequired(true)))
    ),
    async execute(message) {
        const db = await pool.connect()
        if (message.options.getSubcommandGroup() === "create") {
            if (message.options.getSubcommand() === "role") {
                const settings = await db.query("SELECT role, position, role FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'role'])
                if (settings.rowCount === 0) {
                    return message.reply("There is no custom role set up")
                }
                rolePermissions(message, settings.rows[0]?.role)
                const result = await db.query("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'role'])
                if (result.rowCount === 0) {
                    const role = await message.guild.roles.create({
                            name: settings.rows[0]?.tag ? `${message.options.getString("name")} (${settings.rows[0].tag})` : message.options.getString("name"),
                            color: message.options.getString("color").toUpperCase(),
                            position: settings.rows[0].position,
                    })
                    await message.member.roles.add(role)
                    await db.query("INSERT INTO roles(guild, member, type, role) VALUES ($1, $2, $3, $4)", [message.guild.id, message.user.id, 'role', role.id])
                    return message.reply(`The custom role ${message.options.getString("name")} has been created`)
                } else {
                    return message.reply("You already have a custom role")
                }
            } else if (message.options.getSubcommand() === "text") {
                const settings = await db.query("SELECT role, position, tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'text'])
                if (settings.rowCount === 0) {
                    return message.reply("There is no custom text channel set up")
                }
                rolePermissions(message, settings.rows[0]?.role)
                const result = await db.query("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'text'])
                if (result.rowCount === 0) {
                    const channel = await message.guild.channels.create(message.options.getString("name"), {
                        type: "text",
                        topic: settings.rows[0]?.tag ? `${message.options.getString("topic")} **(${settings.rows[0].tag})**` : message.options.getString("topic"),
                        permissionOverwrites: [{
                            id: message.guild.id,
                            deny: ["VIEW_CHANNEL"],
                        }, {
                            id: message.user.id,
                            allow: ["VIEW_CHANNEL"],
                        }],
                        parent: settings.rows[0].position
                    })
                    await db.query("INSERT INTO roles(guild, member, type, role) VALUES ($1, $2, $3, $4)", [message.guild.id, message.user.id, 'text', channel.id])
                    return message.reply(`The custom text channel ${message.options.getString("name")} has been created`)
                } else {
                    return message.reply("You already have a custom text channel")
                }
            } else if (message.options.getSubcommand() === "voice") {
                const settings = await db.query("SELECT role, position, tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'voice'])
                rolePermissions(message, settings.rows[0].role)
                const result = await db.query("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'voice'])
                if (result.rowCount === 0) {
                    const channel = await message.guild.channels.create(settings.rows[0]?.tag ? `${message.options.getString("name")} (${settings.rows[0].tag})` : message.options.getString("name"), {
                        type: "voice",
                        userLimit: message.options.getInteger("limit"),
                        permissionOverwrites: [{
                            id: message.guild.id,
                            deny: ["VIEW_CHANNEL"],
                        }, {
                            id: message.user.id,
                            allow: ["VIEW_CHANNEL"],
                        }],
                        position: settings.rows[0].position
                    })
                    await db.query("INSERT INTO roles(guild, member, type, role) VALUES ($1, $2, $3, $4)", [message.guild.id, message.user.id, 'voice', channel.id])
                    return message.reply(`The custom voice channel ${message.options.getString("name")} has been created`)
                } else {
                    return message.reply("You already have a custom voice channel")
                }
            }
        } else if (message.options.getSubcommandGroup() === "edit") {
            if (message.options.getSubcommand() === "role") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'role'])
                const settings = await db.query("SELECT tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'role'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom role")
                }
                const role = message.guild.roles.cache.get(result.rows[0].role)
                role.edit({
                    name: settings.rows[0]?.tag ? `${message.options.getString("name")} (${settings.rows[0].tag})` : message.options.getString("name"),
                    color: message.options.getString("color").toUpperCase()
                })
                return message.reply(`The custom role ${role.name} has been edited`)
            } else if (message.options.getSubcommand() === "text") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'text'])
                const settings = await db.query("SELECT tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'text'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom text channel")
                }
                const channel = message.guild.channels.cache.get(result.rows[0].role)
                channel.edit({
                    type: "text",
                    topic: settings.rows[0]?.tag ? `${message.options.getString("topic")} **(${settings.rows[0].tag})**` : message.options.getString("topic")
                })
                await message.reply(`The custom text channel ${channel.name} has been edited`)
            } else if (message.options.getSubcommand() === "voice") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'voice'])
                const settings = await db.query("SELECT tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'voice'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom voice channel")
                }
                const channel = message.guild.channels.cache.get(result.rows[0].role)
                channel.edit({
                    name: settings.rows[0]?.tag ? `${message.options.getString("name")} (${settings.rows[0].tag})` : message.options.getString("name"),
                    userLimit: message.options.getInteger("limit")
                })
                await message.reply(`The custom voice channel ${channel.name} has been edited`)
            }
        } else if (message.options.getSubcommandGroup() === "delete") {
            if (message.options.getSubcommand() === "role") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'role'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom role")
                }
                const role = message.guild.roles.cache.get(result.rows[0].role)
                role.delete()
                await db.query("DELETE FROM roles WHERE guild = $1 and member = $2 and type = $3", [message.guild.id, message.user.id, 'role'])
                return message.reply(`The custom role ${role.name} has been deleted`)
            } else if (message.options.getSubcommand() === "text") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'text'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom text channel")
                }
                const channel = message.guild.channels.cache.get(result.rows[0].role)
                channel.delete()
                await db.query("DELETE FROM roles WHERE guild = $1 and member = $2 and type = $3", [message.guild.id, message.user.id, 'text'])
                return message.reply(`The custom text channel ${channel.name} has been deleted`)
            } else if (message.options.getSubcommand() === "voice") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'voice'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom voice channel")
                }
                const channel = message.guild.channels.cache.get(result.rows[0].role)
                channel.delete()
                await db.query("DELETE FROM roles WHERE guild = $1 and member = $2 and type = $3", [message.guild.id, message.user.id, 'voice'])
                return message.reply(`The custom voice channel ${channel.name} has been deleted`)
            }
        } else if (message.options.getSubcommandGroup() === "give") {
            if (message.options.getSubcommand() === "role") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'role'])
                const settings = await db.query("SELECT amount FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'role'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom role")
                }
                const role = message.guild.roles.cache.get(result.rows[0].role)
                const member = await message.options.getMember("user")
                if (message.user.id === member.id) {
                    await message.reply("You cannot give or remove yourself your own custom role")
                } else {
                    if (member.roles.cache.has(role.id)) {
                        await member.roles.remove(role)
                        await message.reply(`The custom role ${role.name} has been removed from ${member.user.tag}`)
                    } else {
                        if (role.members.size > settings.rows[0].amount) {
                            await message.reply(`The role has reached the maximum amount of ${settings.rows[0].amount} members`)
                        } else {
                            await member.roles.add(role)
                            await message.reply(`The custom role ${role.name} has been given to ${member.user.tag}`)
                        }
                    }
                }
            } else if (message.options.getSubcommand() === "text") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'text'])
                const settings = await db.query("SELECT amount FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'text'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom text channel")
                }
                const channel = message.guild.channels.cache.get(result.rows[0].role)
                const member = await message.options.getMember("user")
                if (message.user.id === member.id) {
                    await message.reply("You cannot give or remove yourself your own custom text channel")
                } else {
                    if (channel.permissionsFor(member).has("VIEW_CHANNEL")) {
                        channel.permissionOverwrites.delete(member)
                        await message.reply(`The custom text channel ${channel.name} has been removed from ${member.user.tag}`)
                    } else {
                        if (channel.members.size > settings.rows[0].amount) {
                            await message.reply(`The text channel has reached the maximum amount of ${settings.rows[0].amount} members`)
                        } else {
                            await channel.permissionOverwrites.create(member, {
                                VIEW_CHANNEL: true,
                                SEND_MESSAGES: true
                            })
                            await message.reply(`The custom text channel ${channel.name} has been given to ${member.user.tag}`)
                        }
                    }
                }
            } else if (message.options.getSubcommand() === "voice") {
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'voice'])
                const settings = await db.query("SELECT amount FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'voice'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom voice channel")
                }
                const channel = message.guild.channels.cache.get(result.rows[0].role)
                const member = await message.options.getMember("user")
                if (message.user.id === member.id) {
                    await message.reply("You cannot give or remove yourself your own custom voice channel")
                } else {
                    if (channel.permissionsFor(member).has("VIEW_CHANNEL")) {
                        channel.permissionOverwrites.delete(member)
                        await message.reply(`The custom voice channel ${channel.name} has been removed from ${member.user.tag}`)
                    } else {
                        if (channel.members.size > settings.rows[0].amount) {
                            await message.reply(`The voice channel has reached the maximum amount of ${settings.rows[0].amount} members`)
                        } else {
                            await channel.permissionOverwrites.create(member, {
                                VIEW_CHANNEL: true,
                                CONNECT: true,
                                SPEAK: true
                            })
                            await message.reply(`The custom voice channel ${channel.name} has been given to ${member.user.tag}`)
                        }
                    }
                }
            }
        } else if (message.options.getSubcommandGroup() === "configure") {
            if (message.options.getSubcommand() === "role") {
                const result = await db.query("SELECT role FROM custom WHERE guild = $1 and system = $2 LIMIT 1", [message.guild.id, 'role'])
                if (result.rowCount > 0) {
                    await db.query("DELETE FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'role'])
                    await message.reply("The custom role has been removed")
                } else {
                    await db.query("INSERT INTO custom(guild, system, role, position, amount, tag, remove) VALUES($1, $2, $3, $4, $5, $6, $7)", [message.guild.id, 'role', message.options.getRole("role").id, message.options.getRole("position").id, message.options.getInteger("limit"), message.options.getString("tag"), message.options.getBoolean("remove")])
                    await message.reply("The custom role has been added")
                }
            } else if (message.options.getSubcommand() === "text") {
                const result = await db.query("SELECT role FROM custom WHERE guild = $1 and system = $2 LIMIT 1", [message.guild.id, 'text'])
                if (result.rowCount > 0) {
                    await db.query("DELETE FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'text'])
                    await message.reply("The custom text channel has been removed")
                } else {
                    await db.query("INSERT INTO custom(guild, system, role, position, amount, tag, remove) VALUES($1, $2, $3, $4, $5, $6, $7)", [message.guild.id, 'text', message.options.getChannel("channel").id, message.options.getRole("position").id, message.options.getInteger("limit"), message.options.getString("tag"), message.options.getBoolean("remove")])
                    await message.reply(`The custom text channel has been added`)
                }
            } else if (message.options.getSubcommand() === "voice") {
                const result = await db.query("SELECT role FROM custom WHERE guild = $1 and system = $2 LIMIT 1", [message.guild.id, 'voice'])
                if (result.rowCount > 0) {
                    await db.query("DELETE FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'voice'])
                    await message.reply("The custom voice channel has been removed")
                } else {
                    await db.query("INSERT INTO custom(guild, system, role, position, amount, tag, remove) VALUES($1, $2, $3, $4, $5, $6, $7)", [message.guild.id, 'voice', message.options.getChannel("channel").id, message.options.getRole("position").id, message.options.getInteger("limit"), message.options.getString("tag"), message.options.getBoolean("remove")])
                    await message.reply("The custom voice channel has been added")
                }
            }
        }
        await db.release()
    }
}