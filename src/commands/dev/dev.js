const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const fs = require("fs");
const json = require("../../config.json");
const {paginator, PaginateWhileRunning} = require("../../structures/paginators");
const {MessageEmbed, MessageAttachment} = require("discord.js");
const {resolveCommands, resolveEvents} = require("../../structures/resolvers");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("dev")
        .setDescription("Developer commands")
        .setDefaultPermission(false)
        .addSubcommand(subcommand => subcommand
            .setName("eval")
            .setDescription("Evaluates code")
            .addStringOption(option => option
                .setName("argument")
                .setDescription("Code to evaluate")
                .setRequired(true)
            ))
        .addSubcommand(subcommand => subcommand
            .setName("shell")
            .setDescription("Runs a shell command")
            .addStringOption(option => option
                .setName("argument")
                .setDescription("Shell command to run")
                .setRequired(true)
            ))
        .addSubcommand(subcommand => subcommand
                .setName("sql")
                .setDescription("Runs a SQL query")
                .addStringOption(option => option
                    .setName("argument")
                    .setDescription("SQL query to run")
                    .setRequired(true)
                ))
        .addSubcommand(subcommand => subcommand
                .setName("source")
                .setDescription("Shows the source code of a command")
                .addStringOption(option => option
                    .setName("argument")
                    .setDescription("Command to show the source code of")
                    .setRequired(true)
                )
        )
        .addSubcommand(subcommand => subcommand
            .setName("load")
            .setDescription("Loads or reloads a slash command or event")
            .addStringOption(option => option
                .setName("argument")
                .setDescription("Slash command to load or event to reload")
                .setRequired(true)
            ))
        .addSubcommand(subcommand => subcommand
            .setName("unload")
            .setDescription("Unloads a slash command or event")
            .addStringOption(option => option
                .setName("argument")
                .setDescription("Slash command to unload or event to unload")
                .setRequired(true)
            ))
        .addSubcommand(subcommand => subcommand
            .setName("shutdown")
            .setDescription("Shuts down the bot")
            .addBooleanOption(option => option
                .setName("restart")
                .setDescription("Whether to restart the bot after shutdown")
            ))
        .addSubcommand(subcommand => subcommand
            .setName("rtt")
            .setDescription("Shows the bot's response time")
        )
        .addSubcommand(subcommand => subcommand
            .setName("log")
            .setDescription("Shows the bot's log")
        )
        .addSubcommand(subcommand => subcommand
            .setName("permtrace")
            .setDescription("Shows the bot's permission trace")
            .addStringOption(option => option
                .setName("guild")
                .setDescription("Guild to trace")
                .setRequired(true))
            .addUserOption(option => option
                .setName("user")
                .setDescription("User to trace")
                .setRequired(false)
            )
            .addRoleOption(option => option
                .setName("role")
                .setDescription("Role to trace")
                .setRequired(false)
            )
        )
        .addSubcommand(subcommand => subcommand
            .setName("block")
            .setDescription("Blocks a user from using the bot")
            .addUserOption(option => option
                .setName("argument")
                .setDescription("User to block")
                .setRequired(true)
            )
            .addStringOption(option => option
                .setName("reason")
                .setDescription("Reason for blocking")
            )),
    async execute(message) {
        const db = await pool.connect()
        if (message.options.getSubcommand() === "block") {
            const user = message.options.getUser("argument")
            const reason = message.options.getString("reason") || "No reason given"
            const result = await db.query("SELECT message FROM blacklist WHERE member = $1 and type = $2", [user.id, 'user'])
            if (result.rowCount === 0) {
                await db.query("INSERT INTO blacklist (member, message, type) VALUES ($1, $2, $3)", [user.id, reason, 'user'])
                const channel = message.guild.channels.cache.get("841455998542938143")
                await channel.send(`${user.username}#${user.discriminator} has been blocked from using the bot for ${reason}`)
                await message.reply(`Successfully blocked ${user.username}#${user.discriminator}`)
            } else {
                await db.query("DELETE FROM blacklist WHERE member = $1 and type = $2", [user.id, 'user'])
                await message.reply(`Successfully unblocked ${user.username}#${user.discriminator}`)
            }
        } else if (message.options.getSubcommand() === "load") {
            let pull = message.options.getString("argument")
            const commandFolders = fs.readdirSync(`./commands`)
            for (const folder of commandFolders) {
                const commandFiles = fs.readdirSync(`./commands/${folder}`).filter(file => file.endsWith('.js'))
                for (const file of commandFiles) {
                    const command = require(`../../commands/${folder}/${file}`)
                    if (command.data.name === pull) {
                        await message.client.commands.delete(command.data.name)
                        await message.client.commands.set(command.data.name, command)
                        resolveCommands(message.client)
                        await message.reply(`Successfully loaded ${command.data.name}`)
                        break
                    }
                }
            }
            const eventFiles = fs.readdirSync(`./events`).filter(file => file.endsWith('.js'))
            for (const file of eventFiles) {
                const event = require(`../../events/${file}`)
                if (event.name === pull) {
                    await message.client.events.delete(event.data.name)
                    await message.client.events.set(event.data.name, event)
                    resolveEvents(message.client)
                    await message.reply(`Successfully loaded ${event.data.name}`)
                    break
                }
            }
        } else if (message.options.getSubcommand() === "unload") {
            let pull = message.options.getString("argument")
            const commandFolders = fs.readdirSync(`./commands`)
            for (const folder of commandFolders) {
                const commandFiles = fs.readdirSync(`./commands/${folder}`).filter(file => file.endsWith('.js'))
                for (const file of commandFiles) {
                    const command = require(`../../commands/${folder}/${file}`)
                    if (command.data.name === pull) {
                        await message.client.commands.delete(command.data.name)
                        resolveCommands(message.client)
                        await message.reply(`Successfully unloaded ${command.data.name}`)
                        break
                    }
                }
            }
            const eventFiles = fs.readdirSync(`./events`).filter(file => file.endsWith('.js'))
            for (const file of eventFiles) {
                const event = require(`../../events/${file}`)
                if (event.name === pull) {
                    await message.client.events.delete(event.data.name)
                    resolveEvents(message.client)
                    await message.reply(`Successfully unloaded ${event.data.name}`)
                    break
                }
            }
        } else if (message.options.getSubcommand() === "shutdown") {
            const restart = message.options.getBoolean("restart")
            if (restart) {
                await message.reply("Restarting...")
                message.client.destroy()
                await message.client.login(json['token'])
            } else {
                await message.reply("Shutting down...")
                message.client.destroy()
                process.exit(0)
            }
        } else if (message.options.getSubcommand() === "rtt") {
            await message.reply(`Response time: ${message.client.ws.ping}ms`)
        } else if (message.options.getSubcommand() === "log") {
            const data = fs.readFileSync('./log')
            const pages = new paginator(message, data.split(/\r?\n/))
            pages.per_page = 140
            await pages.paginate()
        } else if (message.options.getSubcommand() === "permtrace") {
            const guild = message.options.getString("guild")
            const user = message.options.getUser("user")
            const role = message.options.getRole("user")
            const channel = user || role
            const permissions = guild.channel.permissionsFor(user || role) ?? guild.channel.permissionOverwrites.cache
            const embed = new MessageEmbed()
                .setTitle(`Permissions for ${channel.name}`)
                .setDescription(`${channel.name} has the following permissions:\n${permissions.toArray().join(', ')}`)
            await message.reply({embeds: [embed]})
        } else if (message.options.getSubcommand() === "source") {
            const pull = message.options.getString("argument")
            const commandFolders = fs.readdirSync(`./commands`)
            for (const folder of commandFolders) {
                const commandFiles = fs.readdirSync(`./commands/${folder}`).filter(file => file.endsWith('.js'))
                for (const file of commandFiles) {
                    const command = require(`../../commands/${folder}/${file}`)
                    if (command.data.name === pull) {
                        const attachment = new MessageAttachment(`./commands/${folder}/${file}`)
                        await message.reply({files: [attachment]})
                    }
                }
            }
        } else if (message.options.getSubcommand() === "eval") {
            const code = message.options.getString("argument")
            try {
                // eslint-disable-next-line no-eval
                const now = Date.now()
                const output = eval(`const discord = require('discord.js'); \nconst client = message.client \n${code}`)
                await message.deferReply()
                if (output instanceof Promise) {
                    await output.then(async (result) => {
                        // use generator functions to support async/await and send a response as it is executing
                        // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function*
                        const pages = new PaginateWhileRunning(message)
                        pages.per_page = 30
                        pages.show_embed = false
                        pages.show_entry_count = false
                        pages.lang = 'js'
                        const generator = function* (result) {
                            yield result
                        }
                        const res = generator(output)
                        for await (const value of res) {
                            // replace discord token with a placeholder
                            const output = value.toString().replace(json["token"], '<TOKEN>')
                            // if an object decode it

                            await pages.paginate(output)
                        }
                    })
                } else {
                    // use generator functions to send a response as it is executing
                    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function*
                    const pages = new PaginateWhileRunning(message)
                    pages.per_page = 30
                    pages.show_embed = false
                    pages.show_entry_count = false
                    pages.lang = 'js'
                    const generator = function* (result) {
                        yield result
                    }
                    const result = generator(output)
                    for await (const value of result) {
                        // replace discord token with a placeholder
                        const output = value.toString().replace(json["token"], '<TOKEN>')
                        await pages.paginate(output)
                    }
                }
                await message.channel.send(`Returned as type ${typeof output} and took ${(Date.now() - now)} milliseconds to execute`)
            } catch (error) {
                await message.channel.send(`\`\`\`js\n${error.stack}\`\`\``)
            }
        } else if (message.options.getSubcommand() === "shell") {
            const code = message.options.getString("argument")
            try {
                await message.deferReply()
                const now = Date.now()
                let shell = require('child_process').exec(code)
                setTimeout(() => {
                    shell.kill()
                }, 120000)
                const pages1 = new PaginateWhileRunning(message)
                pages1.per_page = 30
                pages1.show_entry_count = false
                pages1.lang = "bash"
                await shell.stdout.on('data', (data) => {
                    // replace color codes
                    const output = data.toString().replace(/\u001b\[(\d+)(;\d+)?m/g, '')
                    pages1.paginate(output)

                })
                await shell.stderr.on('data', (data) => {
                    const output = data.toString().replace(/\u001b\[(\d+)(;\d+)?m/g, '')
                    pages1.paginate(output)
                })
                shell.on('close', (code) => {
                    message.channel.send(`Shell exited with code ${code} and took ${(Date.now() - now)} milliseconds to execute`)
                })

            } catch (error) {
                await message.channel.send(`\`\`\`js\n${error.stack}\`\`\``)
            }
        } else if (message.options.getSubcommand() === "sql") {
            const query = message.options.getString("argument")
            try {
                await message.deferReply()
                const result = await db.query(query)
                if (result.rows.length === 0) {
                    await message.reply("The query did not return anything")
                } else {
                    const paginate = new paginator(message, JSON.stringify(result.rows, null, 2).split('\n'))
                    paginate.per_page = 40
                    paginate.show_entry_count = false
                    paginate.lang = "json"
                    await paginate.paginate()
                }
            } catch (error) {
                await message.channel.send(`\`\`\`js\n${error.stack}\`\`\``)
            }
        }
        await db.release()
    }
}