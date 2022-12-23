const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {rolePermissions, clientPermissions} = require("../../structures/permissions");
const {Modal, TextInputComponent, MessageActionRow, PermissionsBitField} = require("discord.js");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("custom")
        .setDescription("Lets you manage your custom roles or channels")
        .addSubcommandGroup(group => group
            .setName("create")
            .setDescription("Allows you to create a custom role, text or voice channel")
            .addSubcommand(subcommand => subcommand
                .setName("role")
                .setDescription("Creates a custom role"))
            .addSubcommand(subcommand => subcommand
                .setName("text")
                .setDescription("Creates a custom text channel"))
            .addSubcommand(subcommand => subcommand
                .setName("voice")
                .setDescription("Creates a custom voice channel")))
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
                .setDescription("Edits a custom role"))
            .addSubcommand(subcommand => subcommand
                .setName("text")
                .setDescription("Edits a custom text channel"))
            .addSubcommand(subcommand => subcommand
                .setName("voice")
                .setDescription("Edits a custom voice channel")))
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
                    .setRequired(false))
                .addBooleanOption(option => option
                    .setName("remove")
                    .setDescription("Whether or not the role should be deleted upon the user losing the required role")
                    .setRequired(false)))
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
        async function showModal(message, id, title, options) {
            const modal = new Modal()
                .setCustomId(id)
                .setTitle(title)
            // .setComponents with for loop
            for (const option of options) {
                const component = new TextInputComponent()
                    .setCustomId(option.id)
                    .setLabel(option.label)
                    .setRequired(option.required)
                    .setStyle('SHORT')
                if (component.placeholder) {
                    component.setPlaceholder(option.placeholder)
                }
                modal.addComponents(new MessageActionRow().addComponents(component))
            }

            await message.showModal(modal)
        }

        if (message.options.getSubcommandGroup() === "create") {
            // TO DO: Revise /custom command to be a menu command (current system is too much)
            if (message.options.getSubcommand() === "role") {
                clientPermissions(message, [PermissionsBitField.Flags.ManageRoles])
                const settings = await db.query("SELECT role, position, role FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'role'])
                if (settings.rowCount === 0) {
                    return message.reply("There is no custom role set up")
                }
                rolePermissions(message, settings.rows[0]?.role)
                await showModal(message,'customRole', 'Create Custom Role', [{
                    id: 'customRoleName',
                    label: "What should the custom role be called?",
                    required: true,
                }, {
                    id: 'customRoleColor',
                    label: "What color should the custom role be?",
                    required: true,
                }])
                const filter = (interaction) => interaction.customId === 'customRole';
                message.awaitModalSubmit({ filter, time: 40000 })
                    .then(async (modal) => {
                        const customRoleName = modal.fields.getTextInputValue('customRoleName')
                        const customRoleColor = modal.fields.getTextInputValue('customRoleColor').toUpperCase()
                        await modal.deferUpdate()

                        const result = await db.query("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'role'])
                        if (result.rowCount === 0) {
                            const role = await message.guild.roles.create({
                                    name: settings.rows[0]?.tag ? `${customRoleName} (${settings.rows[0].tag})` : customRoleName,
                                    color: customRoleColor,
                                    position: settings.rows[0].position,
                            })
                            await message.member.roles.add(role)
                            await db.query("INSERT INTO roles(guild, member, type, role) VALUES ($1, $2, $3, $4)", [message.guild.id, message.user.id, 'role', role.id])
                            return message.channel.send(`The custom role ${customRoleName} has been created`)
                        } else {
                            return message.channel.send("You already have a custom role")
                        }
                    }).catch(() => {
                        return message.channel.send("You took too long to respond")
                    })
            } else if (message.options.getSubcommand() === "text") {
                clientPermissions(message, [PermissionsBitField.Flags.ManageChannels])
                const settings = await db.query("SELECT role, position, tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'text'])
                if (settings.rowCount === 0) {
                    return message.reply("There is no custom text channel set up")
                }
                rolePermissions(message, settings.rows[0]?.role)
                await showModal(message,'customText', 'Create Custom Text Channel', [{
                    id: 'customTextName',
                    label: "What should the custom text channel be called?",
                    required: true,
                }, {
                    id: 'customTextTopic',
                    label: "What should the topic of the custom text channel be?",
                }])
                const filter = (interaction) => interaction.customId === 'customText';
                message.awaitModalSubmit({ filter, time: 40000 })
                    .then(async (modal) => {
                        const customTextName = modal.fields.getTextInputValue('customTextName')
                        const customTextTopic = modal.fields.getTextInputValue('customTextTopic')
                        await modal.deferUpdate()

                        const result = await db.query("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'text'])
                        if (result.rowCount === 0) {
                            const text = await message.guild.channels.create(customTextName, {
                                type: 'text',
                                topic: settings.rows[0]?.tag ? `${customTextTopic} **(${settings.rows[0].tag})**` : customTextTopic,
                                permissionOverwrites: [{
                                    id: message.guild.id,
                                    deny: ["VIEW_CHANNEL"],
                                }, {
                                    id: message.user.id,
                                    allow: ["VIEW_CHANNEL"],
                                }],
                                position: settings.rows[0].position,
                            })
                            await message.member.roles.add(text)
                            await db.query("INSERT INTO roles(guild, member, type, role) VALUES ($1, $2, $3, $4)", [message.guild.id, message.user.id, 'text', text.id])
                            return message.channel.send(`The custom text channel ${customTextName} has been created`)
                        } else {
                            return message.channel.send("You already have a custom text channel")
                        }
                    }).catch(() => {
                        return message.channel.send("You took too long to respond")
                    })
                }
            } else if (message.options.getSubcommand() === "voice") {
                clientPermissions(message, PermissionsBitField.Flags.ManageChannels)
                const settings = await db.query("SELECT role, position, tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'voice'])
                rolePermissions(message, settings.rows[0]?.role)
                await showModal(message,'customVoice', 'Create Custom Voice Channel', [{
                    id: 'customVoiceName',
                    label: "What should the custom voice channel be called?",
                    required: true,
                }, {
                    id: 'customVoiceLimit',
                    label: "What should the limit of the custom voice channel be?",
                }])
                const filter = (interaction) => interaction.customId === 'customVoice';
                message.awaitModalSubmit({ filter, time: 40000 })
                    .then(async (modal) => {
                        const customVoiceName = modal.fields.getTextInputValue('customVoiceName')
                        const customVoiceLimit = modal.fields.getTextInputValue('customVoiceLimit')
                        await modal.deferUpdate()

                        const result = await db.query("SELECT member FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'voice'])
                        if (result.rowCount === 0) {
                            const voice = await message.guild.channels.create(customVoiceName, {
                                type: 'voice',
                                userLimit: customVoiceLimit,
                                permissionOverwrites: [{
                                    id: message.guild.id,
                                    deny: [PermissionsBitField.Flags.ViewChannel],
                                }, {
                                    id: message.user.id,
                                    allow: [PermissionsBitField.Flags.ViewChannel],
                                }],
                                position: settings.rows[0].position,
                            })
                            await message.member.roles.add(voice)
                            await db.query("INSERT INTO roles(guild, member, type, role) VALUES ($1, $2, $3, $4)", [message.guild.id, message.user.id, 'voice', voice.id])
                            return message.channel.send(`The custom voice channel ${customVoiceName} has been created`)
                        } else {
                            return message.channel.send("You already have a custom voice channel")
                        }
                    }).catch(() => {
                        return message.channel.send("You took too long to respond")
                    })
                }
        else if (message.options.getSubcommandGroup() === "edit") {
            if (message.options.getSubcommand() === "role") {
                clientPermissions(message, PermissionsBitField.Flags.ManageRoles)
                await showModal(message,'editRole', 'Edit Custom Role', [{
                    id: 'editRoleName',
                    label: "What should the custom role be called?",
                    required: true,
                }, {
                    id: 'editRoleColor',
                    label: "What should the color of the custom role be?",
                }])
                const filter = (interaction) => interaction.customId === 'editRole';
                message.awaitModalSubmit({ filter, time: 40000 })
                    .then(async (modal) => {
                        const editRoleName = modal.fields.getTextInputValue('editRoleName')
                        const editRoleColor = modal.fields.getTextInputValue('editRoleColor').toUpperCase()
                        await modal.deferUpdate()

                        const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'role'])
                        const settings = await db.query("SELECT tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'role'])
                        if (result.rowCount === 0) {
                            return message.channel.send("You don't have a custom role set up")
                        }
                        const role = message.guild.roles.cache.get(result.rows[0].role)
                        if (role) {
                            await role.edit({
                                name: settings.rows[0]?.tag ? `${editRoleName} (${settings.rows[0].tag})` : editRoleName,
                                color: editRoleColor,
                            })
                            return message.channel.send(`The custom role ${role.name} has been edited`)
                        }
                    }).catch(() => {
                        return message.channel.send("You took too long to respond")
                    })
                }
            else if (message.options.getSubcommand() === "text") {
                clientPermissions(message, PermissionsBitField.Flags.ManageChannels)
                await showModal(message,'editText', 'Edit Custom Text Channel', [{
                    id: 'editTextName',
                    label: "What should the custom text channel be called?",
                    required: true,
                }, {
                    id: 'editTextTopic',
                    label: "What should the topic of the custom text channel be?",
                }])
                const filter = (interaction) => interaction.customId === 'editText';
                message.awaitModalSubmit({ filter, time: 40000 })
                    .then(async (modal) => {
                        const editTextName = modal.fields.getTextInputValue('editTextName')
                        const editTextTopic = modal.fields.getTextInputValue('editTextTopic')
                        await modal.deferUpdate()

                        const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'text'])
                        const settings = await db.query("SELECT tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'text'])
                        if (result.rowCount === 0) {
                            return message.channel.send("You don't have a custom text channel set up")
                        }
                        const text = message.guild.channels.cache.get(result.rows[0].role)
                        if (text) {
                            await text.edit({
                                name: settings.rows[0]?.tag ? `${editTextName} (${settings.rows[0].tag})` : editTextName,
                                topic: editTextTopic,
                            })
                            return message.channel.send(`The custom text channel ${text.name} has been edited`)
                        }
                    }).catch(() => {
                        return message.channel.send("You took too long to respond")
                    })
                }
            else if (message.options.getSubcommand() === "voice") {
                clientPermissions(message, PermissionsBitField.Flags.ManageChannels)
                await showModal(message,'editVoice', 'Edit Custom Voice Channel', [{
                    id: 'editVoiceName',
                    label: "What should the custom voice channel be called?",
                    required: true,
                }, {
                    id: 'editVoiceLimit',
                    label: "What should the user limit of the custom voice channel be?",
                }])
                const filter = (interaction) => interaction.customId === 'editVoice';
                message.awaitModalSubmit({ filter, time: 40000 })
                    .then(async (modal) => {
                        const editVoiceName = modal.fields.getTextInputValue('editVoiceName')
                        const editVoiceLimit = modal.fields.getTextInputValue('editVoiceLimit')
                        await modal.deferUpdate()

                        const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'voice'])
                        const settings = await db.query("SELECT tag FROM custom WHERE guild = $1 and system = $2", [message.guild.id, 'voice'])
                        if (result.rowCount === 0) {
                            return message.channel.send("You don't have a custom voice channel set up")
                        }
                        const voice = message.guild.channels.cache.get(result.rows[0].role)
                        if (voice) {
                            await voice.edit({
                                name: settings.rows[0]?.tag ? `${editVoiceName} (${settings.rows[0].tag})` : editVoiceName,
                                userLimit: editVoiceLimit,
                            })
                            return message.channel.send(`The custom voice channel ${voice.name} has been edited`)
                        }
                    }).catch(() => {
                        return message.channel.send("You took too long to respond")
                    })
                }
            }
        else if (message.options.getSubcommandGroup() === "delete") {
            if (message.options.getSubcommand() === "role") {
                clientPermissions(message, PermissionsBitField.Flags.ManageRoles)
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'role'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom role")
                }
                const role = message.guild.roles.cache.get(result.rows[0].role)
                role.delete()
                await db.query("DELETE FROM roles WHERE guild = $1 and member = $2 and type = $3", [message.guild.id, message.user.id, 'role'])
                return message.reply(`The custom role ${role.name} has been deleted`)
            } else if (message.options.getSubcommand() === "text") {
                clientPermissions(message, PermissionsBitField.Flags.ManageChannels)
                const result = await db.query("SELECT role FROM roles WHERE guild = $1 and member = $2 and type = $3 LIMIT 1", [message.guild.id, message.user.id, 'text'])
                if (result.rowCount === 0) {
                    return message.reply("You do not have a custom text channel")
                }
                const channel = message.guild.channels.cache.get(result.rows[0].role)
                channel.delete()
                await db.query("DELETE FROM roles WHERE guild = $1 and member = $2 and type = $3", [message.guild.id, message.user.id, 'text'])
                return message.reply(`The custom text channel ${channel.name} has been deleted`)
            } else if (message.options.getSubcommand() === "voice") {
                clientPermissions(message, PewrmissionsBitField.Flags.ManageChannels)
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
                clientPermissions(message, PermissionsBitField.Flags.ManageRoles)
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
                clientPermissions(message, PermissionsBitField.Flags.ManageChannels)
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
                        await channel.permissionOverwrites.delete(member)
                        await message.reply(`The custom text channel ${channel.name} has been removed from ${member.user.tag}`)
                    } else {
                        if (channel.members.size > settings.rows[0].amount) {
                            await message.reply(`The text channel has reached the maximum amount of ${settings.rows[0].amount} members`)
                        } else {
                            await channel.permissionOverwrites.create(member, {
                                VIEW_CHANNEL: true,
                                SEND_MESSAGES: true
                            })
                            await message.reply(`The custom text channel ${channel.name} has been added to ${member.user.tag}`)
                        }
                    }
                }
            } else if (message.options.getSubcommand() === "voice") {
                clientPermissions(message, PermissionsBitField.Flags.ManageChannels)
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
                        await channel.permissionOverwrites.delete(member)
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