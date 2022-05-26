const {MessageEmbed, MessageActionRow, MessageButton, MessageSelectMenu, Modal, TextInputComponent} = require("discord.js");
const fs = require("fs");
const {ConvertDate} = require("./converters");
const {resolveRole, resolveAsChannel_Dm_Here} = require("./resolvers");
const {Giveaway, Reminder} = require("./tasks");
const {pool} = require("../database");

class HelpMenu {
    async startHelp(message) {
        const buttons = new MessageActionRow()
            .addComponents(
                new MessageButton()
                    .setCustomId("info")
                    .setEmoji("ℹ")
                    .setStyle("PRIMARY"),
                new MessageButton()
                    .setCustomId("leaderbard-&-counters")
                    .setEmoji("📈")
                    .setStyle("PRIMARY"),
                new MessageButton()
                    .setCustomId("miscellaneous")
                    .setEmoji("➕")
                    .setStyle("PRIMARY"),
                new MessageButton()
                    .setCustomId("roles")
                    .setEmoji("👤")
                    .setStyle("PRIMARY"),
                new MessageButton()
                    .setCustomId("settings")
                    .setEmoji("⚙")
                    .setStyle("PRIMARY"),
            )
        const buttons2 = new MessageActionRow()
            .addComponents(
                new MessageButton()
                    .setCustomId("Utilities")
                    .setEmoji("🛠")
                    .setStyle("PRIMARY"),
                new MessageButton()
                    .setCustomId("exit")
                    .setEmoji("❌")
                    .setLabel("Exit")
                    .setStyle("PRIMARY"),
            )
        const embed = new MessageEmbed()
            .setTitle("Dionysus Help")
            .setDescription(`Dionysus is a Greek themed, fun, interactive, general purpose discord bot - made to cater to various needs in a server. \n\nUse the interactive menu below to view our commands,  or use the command \`/help <command>\` to get help for a specific command.`)
            .addFields(
                {name: "ℹ - Information Commands", value: "The following commands are used to get information about the bot, or the server.", inline: true},
                {name: "📈 - Leaderboard & Counters", value: "These commands let you view the leaderboard and counters for the server.", inline: true},
                {name: "➕ - Miscellaneous Commands", value: "The following commands are used to interact with the bot.", inline: true},
                {name: "👤 - Roles Commands", value: "The following commands are used to manage roles.", inline: true},
                {name: "⚙ - Settings Commands", value: "The following commands are used to manage settings.", inline: true},
                {name: "🛠 - Utility Commands", value: "The following commands are used to manage utility commands.", inline: true},
            )
        if (this.sent_message) {
            await message.editReply({embeds: [embed], components: [buttons, buttons2]});
        } else {
            this.sent_message = message.reply({embeds: [embed], components: [buttons, buttons2]});
        }
        const filter = i => i.user === message.user
        const collector = message.channel.createMessageComponentCollector({filter, time: 60000})
        collector.on('collect', async i => {
            if (i.customId === 'info') {
                await this.loadHelpCog(message, 1)
            } else if (i.customId === 'leaderbard-&-counters') {
                await this.loadHelpCog(message, 2)
            } else if (i.customId === 'miscellaneous') {
                await this.loadHelpCog(message, 3)
            } else if (i.customId === 'roles') {
                await this.loadHelpCog(message, 4)
            } else if (i.customId === 'settings') {
                await this.loadHelpCog(message, 5)
            } else if (i.customId === 'Utilities') {
                await this.loadHelpCog(message,6)
            } else if (i.customId === 'exit') {
                await message.deleteReply()
                collector.stop()
            }
            await i.deferUpdate();
            collector.stop();
        })
    }
    async loadHelpCog(context, load) {
        // get commands from folder
        const embed = new MessageEmbed()
        embed.title = "Dionysus Help"
        switch (load) {
            case 1: {
                const commands = fs.readdirSync(`commands/info`).filter(file => file.endsWith('.js'));
                for (const command of commands) {
                    const command2 = context.client.commands.get(command.split('.')[0])
                    if (command2?.data) {
                        embed.addField(`${command2.data.name}`, `${command2.data.description}`)
                    }
                }
                break
            }
            case 2: {
                const commands = fs.readdirSync(`commands/leaderboards & counters`).filter(file => file.endsWith('.js'));
                for (const command of commands) {
                    const command2 = context.client.commands.get(command.split('.')[0])
                    if (command2?.data) {
                        embed.addField(`${command2.data.name}`, `${command2.data.description}`)
                    }
                }
                break
            }
            case 3: {
                const commands = fs.readdirSync(`commands/miscellaneous`).filter(file => file.endsWith('.js'));
                for (const command of commands) {
                    const command2 = context.client.commands.get(command.split('.')[0])
                    if (command2?.data) {
                        embed.addField(`${command2.data.name}`, `${command2.data.description}`)
                    }
                }
                break
            }
            case 4: {
                const commands = fs.readdirSync(`commands/roles`).filter(file => file.endsWith('.js'));
                for (const command of commands) {
                    const command2 = context.client.commands.get(command.split('.')[0])
                    if (command2?.data) {
                        embed.addField(`${command2.data.name}`, `${command2.data.description}`)
                    }
                }
                break
            }
            case 5: {
                const commands = fs.readdirSync(`commands/settings`).filter(file => file.endsWith('.js'));
                for (const command of commands) {
                    const command2 = context.client.commands.get(command.split('.')[0])
                    if (command2?.data) {
                        embed.addField(`${command2.data.name}`, `${command2.data.description}`)
                    }
                }
                break
            }
            case 6: {
                const commands = fs.readdirSync(`commands/utilities`).filter(file => file.endsWith('.js'));
                for (const command of commands) {
                    const command2 = context.client.commands.get(command.split('.')[0])
                    if (command2?.data) {
                        embed.addField(`${command2.data.name}`, `${command2.data.description}`)
                    }
                }
                break
            }
        }
        const button = new MessageActionRow()
            .addComponents(
                new MessageButton()
                    .setCustomId("main-menu")
                    .setEmoji("⬆")
                    .setLabel("Main Menu")
                    .setStyle("PRIMARY"),
                new MessageButton()
                    .setCustomId("exit")
                    .setEmoji("❌")
                    .setLabel("Exit")
                    .setStyle("PRIMARY"),
            )
        await context.editReply({embeds: [embed], components: [button]});
        const filter = i => i.user.id === context.user.id
        const collector = context.channel.createMessageComponentCollector({filter, time: 60000})
        collector.on('collect', async i => {
            if (i.customId === 'main-menu') {
                await this.startHelp(context)
            } else if (i.customId === 'exit') {
                await context.deleteReply()
            }
            await i.deferUpdate();
            collector.stop();
        })
    }
}

class GiveawayCreator {
    constructor() {
        this.giveArray = []
        this.json = {}
        this.sent_message = null
    }

    async createGiveaway(message) {
        await this.showModal(message,'giveawayModal', 'Create Giveaway', [{
            id: 'giveawayName',
            label: "What is the name of the giveaway?",
            required: true,
        }, {
            id: 'numberOfWinners',
            label: "How many winners do you want?",
            required: true,
        }, {
            id: 'giveawayTime',
            label: "How long do you want the giveaway to last?",
            required: true,
        }])
        const filter = (interaction) => interaction.customId === 'giveawayModal';
        message.awaitModalSubmit({ filter, time: 20000 })
            .then(async (modal) => {
                const giveawayName = modal.fields.getTextInputValue('giveawayName')
                const numberOfWinners = modal.fields.getTextInputValue('numberOfWinners')
                const giveawayTime = modal.fields.getTextInputValue('giveawayTime')
                await modal.deferUpdate()

                this.giveArray.push(giveawayName, numberOfWinners, giveawayTime)
                await this.extraGiveawayOptions(message)
            })
    }

    async showModal(message, id, title, options) {
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

    async extraGiveawayOptions(message, shouldEdit = false) {
        const embed = new MessageEmbed()
            .setColor("WHITE")
            .setTitle("Giveaway Creator")
            .setDescription("You may now select any additional options for your giveaway by selecting one of the dropdown options below. Or if you like, you can start the giveaway now")
            .setFooter("You have 60 seconds to select an option.")
        const dropdown = new MessageActionRow()
            .addComponents(
                new MessageSelectMenu()
                    .setCustomId("giveaway-options")
                    .setPlaceholder("Select an option")
                    .addOptions([{
                        label: "Add Role Requirement",
                        description: "Add a role requirement to the giveaway.",
                        value: "add-role-requirement",
                    }, {
                        label: "Add Message Requirement",
                        description: "Add a message requirement to the giveaway.",
                        value: "add-message-requirement",
                    }, {
                        label: "Add Voice Requirement",
                        description: "Add a voice requirement to the giveaway.",
                        value: "add-voice-requirement",
                    }, {
                        label: "Add Time Requirement",
                        description: "Add a time requirement to the giveaway for when it should start.",
                        value: "add-time-requirement",
                    }, {
                        label: "Add Role Multiplier",
                        description: "Add a role multiplier to the giveaway.",
                        value: "add-role-multiplier",
                    }, {
                        label: "Add Role Reward",
                        description: "Add a role reward for the giveaway.",
                        value: "add-role-reward",
                    }])
            )
        // show modal after dropdown interaction
        const button = new MessageActionRow()
            .addComponents(
                new MessageButton()
                    .setCustomId("start-giveaway")
                    .setLabel("Start Giveaway")
                    .setEmoji("🎉")
                    .setStyle("PRIMARY")
            )
        // send message
        if (shouldEdit) {
            await this.sent_message.edit({embeds: [embed], components: [dropdown, button]})
        } else {
            this.sent_message = await message.channel.send({embeds: [embed], components: [dropdown, button]})
        }
        await this.giveawayOptions(message)
    }

    async giveawayOptions(message) {
        const filter = (m) => m.user === message.author;
        // dropdown collector with button
        const collector = message.channel.createMessageComponentCollector(filter, {time: 240000, componentType: 'SELECT_MENU'})
        collector.on("collect", async (m) => {
            await m.deferUpdate()
            if (m.values === undefined) {
                await this.startGiveaway(message)
                collector.stop()
            } else {
                if (m.values[0] === "add-role-requirement") {
                    await this.addRoleRequirement(message)
                } else if (m.values[0] === "add-message-requirement") {
                    await this.addMessageRequirement(message)
                } else if (m.values[0] === "add-voice-requirement") {
                    await this.addVoiceRequirement(message)
                } else if (m.values[0] === "add-time-requirement") {
                    await this.addTimeRequirement(message)
                } else if (m.values[0] === "add-role-multiplier") {
                    await this.addRoleMultiplier(message)
                } else if (m.values[0] === "add-role-reward") {
                    await this.addRoleReward(message)
                }
            }
        })
        collector.on("end", async (collected, reason) => {
        })
    }

    async addRoleRequirement(message) {
        const roleadd = await message.channel.send("Please enter the role you would like to add.")
        const filter = (m) => m.user === message.author;
        await message.channel.awaitMessages({filter, time: 20000, max: 1})
            .then(async (collected) => {
                const role = await resolveRole(message, collected.first().content)
                if (role) {
                    this.json.role_requirement = role.id
                    const requirment = await message.channel.send("Added role requirement!")
                    setTimeout(async () => {
                        await requirment.delete();
                    }, 4000);
                } else {
                    const doesNotExist = await message.channel.send("That role doesn't exist!")
                    setTimeout(async () => {
                        await doesNotExist.delete();
                    }, 4000);
                }
                await collected.first().delete()
            })
            .catch(() => {
                message.channel.send("You didn't respond in time!")
            })
        await roleadd.delete()
    }

    async addMessageRequirement(message) {
        // send message prompt
        await message.channel.send("Please enter the message requirement!")
        const filter = (m) => m.user === message.author;
        await message.channel.awaitMessages({filter, time: 20000, max: 1})
            .then(async (collected) => {
                if (parseInt(collected.first().content)) {
                    this.json.message_requirement = parseInt(collected.first().content)
                    await message.channel.send("Added message requirement!")
                } else {
                    await message.channel.send("That's not a valid number!")
                }
                await collected.first().delete()
            })
            .catch(() => {
                message.channel.send("You didn't respond in time!")
            })
    }

    async addVoiceRequirement(message) {
        await message.channel.send("Please enter the voice requirement!")
        const filter = (m) => m.user === message.author;
        await message.channel.awaitMessages({filter, time: 20000, max: 1})
            .then(async (collected) => {
                const toDate = ConvertDate(collected.first().content)
                if (toDate === undefined) {
                    message.channel.send("That's not a valid date!")
                } else if (toDate <= 0) {
                    message.channel.send("You can't set voice time in the past!")
                } else {
                    this.json.voice_requirement = toDate
                    await message.channel.send("Added voice requirement!")
                }
            })
            .catch(() => {
                message.channel.send("You didn't respond in time!")
            })
    }

    async addTimeRequirement(message) {
        await message.channel.send("Please enter the time requirement!")
        const filter = (m) => m.user === message.author;
        await message.channel.awaitMessages({filter, time: 20000, max: 1})
            .then(async (collected) => {
                const duration = ConvertDate(collected.first().content)
                if (duration) {
                    this.json.time_requirement = duration
                    await message.channel.send("Added time requirement!")
                } else {
                    await message.channel.send("That's not a valid duration!")
                }
                await collected.first().delete()
            })
            .catch(() => {
                message.channel.send("You didn't respond in time!")
            })
    }

    async addRoleMultiplier(message) {
        await message.channel.send("Please enter the role multiplier!")
        const filter = (m) => m.user === message.author;
        await message.channel.awaitMessages({filter, time: 20000, max: 1})
            .then(async (collected) => {
                const role = await resolveRole(message, collected.first().content)
                if (role) {
                    this.json.role_multiplier_role = role.id
                    await message.channel.send("Added role multiplier role! Now add the multiplier!")
                } else {
                    await message.channel.send("That's not a valid role!")
                }
                await collected.first().delete()
            })
            .catch(() => {
                message.channel.send("You didn't respond in time!")
            })
        await message.channel.awaitMessages({filter, time: 20000, max: 1})
            .then(async (collected) => {
                if (parseInt(collected.first().content)) {
                    this.json.role_multiplier = parseInt(collected.first().content)
                    await message.channel.send("Added role multiplier!")

                } else {
                    await message.channel.send("That's not a valid number!")
                }
                await collected.first().delete()
            })
            .catch(() => {
                message.channel.send("You didn't respond in time!")
            })
    }

    async addRoleReward(message) {
        await message.channel.send("Please enter the role reward!")
        const filter = (m) => m.user === message.author;
        await message.channel.awaitMessages({filter, time: 20000, max: 1})
            .then(async (collected) => {
                const role = resolveRole(message, collected.first().content)
                if (role) {
                    this.json.role_reward = role.id
                    await message.channel.send("Added role reward!")
                    await this.giveawayOptions(message, this.giveArray)
                } else {
                    await message.channel.send("That's not a valid role!")
                }
                await collected.first().delete()
            })
            .catch(() => {
                message.channel.send("You didn't respond in time!")
            })
    }

    async startGiveaway(message) {
        const array = this.giveArray
        const json = this.json
        const id = Math.random().toString(36).substr(2, 8)
        const embed = new MessageEmbed()
        let startAs = 0;
        const db = await pool.connect()
        const requirements = `${json.role_requirement ? `\nRole requirement: ${message.guild.roles.cache.get(json.role_requirement).name}` : ""}${json.message_requirement ? `\nMessage requirement: ${json.message_requirement}` : ""}${json.voice_requirement ? `\nVoice requirement: ${json.voice_requirement}` : ""}`
        const multiplier = `${json.role_multiplier_role ? `\nRole multiplier: ${message.guild.roles.cache.get(json.role_multiplier_role).name}` : ""} x ${json.role_multiplier ? `${json.role_multiplier}` : ""}`
        if (json?.time_requirement === undefined) {
            startAs = 1
            const delta = new Date(Date.now() + ConvertDate(array[2]) * 1000)
            embed.setTitle(array[0])
                embed.setDescription(`React with 🎉 to enter!\n\n${requirements ? `**Requirements:** ${requirements}\n` : ""}${json.role_multiplier_role ? `**Multiplier:** ${multiplier}` : ""}\n**Winners:** ${array[1]} \n**Ends:** <t:${Math.round(delta.valueOf() / 1000)}:R>`)
                embed.setColor('WHITE')
                embed.setFooter(`Giveaway ID: ${id}`)
            const msg = await message.channel.send({embeds: [embed]})
            await msg.react("🎉")
            await db.query("INSERT INTO vote(guild, message, date, win, type, channel, id, options) VALUES($1, $2, $3, $4, $5, $6, $7, $8)", [message.guild.id, msg.id, delta, array[1], startAs, message.channel.id, id, json]);
        } else {
            const delta = new Date(Date.now() + (ConvertDate(array[2]) + json.time_requirement) * 1000)
            json.time_requirement = new Date(Date.now() + json.time_requirement * 1000)
            embed.setTitle(array[0])
            embed.setDescription(`${requirements ? `**Requirements:** ${requirements}\n` : ""}${json.role_multiplier_role ? `**Multiplier:** ${multiplier}` : ""}\n**Winners:** ${array[1]} \n**Starting:** <t:${Math.round(new Date(json.time_requirement).valueOf() / 1000)}:R>`)
            embed.setColor('WHITE')
            embed.setFooter(`Giveaway ID: ${id}`)
            const msg = await message.channel.send({embeds: [embed]});
            await db.query("INSERT INTO vote(guild, message, date, win, type, channel, id, options) VALUES($1, $2, $3, $4, $5, $6, $7, $8)", [message.guild.id, msg.id, delta, array[1], startAs, message.channel.id, id, json]);
        }
        await db.release()
        await new Giveaway().dispatch_giveaway(message.client)
        this.sent_message.delete()
    }
}

module.exports = {HelpMenu, GiveawayCreator};