const {SlashCommandBuilder} = require("@discordjs/builders");
const {paginator} = require("../../structures/paginator");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("apply")
        .setDescription("Allows you to create an application")
        .addSubcommand(subcommand =>
        subcommand
            .setName("list")
            .setDescription("Lets you view the current application questions")),
    async execute(message) {
        const db = await pool.connect()
        if (message.options.getSubcommand() === "list") {
            const list = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'question'])
            if (!list.rows.length) {
                await message.channel.send("No results!")
            } else {
                const pages = new paginator(message, list.rows.map(obj => obj.text), true, true, false)
                pages.embed.setTitle(`${message.guild.name} Current Questions`)
                await pages.paginate()
            }
        } else {
            const check = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'require'])
            const channel = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'channel'])
            const role = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'role'])
            if (!channel.rows.length) {
                await message.channel.send("Applications currently not have been set up yet by this guild!")
            } else if (!check.rows.find(obj => message.member._roles.includes(obj.text))) {
                await message.channel.send("You are not allowed to create an application!")
            } else {
                // try {
                //     await message.author.send("Respond with `start` to start the application! This will expire in 2 minutes")
                // } catch {
                //     await message.channel.send("The Application could not be sent in your dm's! Ensure Dionysus can send you dm's, then try again.")
                //     await db.release()
                //     return
                // }
                await message.channel.send("The application is ready to be started in your dm!")
                const questions = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'question'])
                let responses = []
                let send = false
                const filter = msg => msg.author.id === message.author.id
                // const confirm = await message.member.createDM().createMessageCollector({max: 1, time: 120000})
                const dmChannel = await message.author.createDM()
                const confirm = new MessagePrompterMessageStrategy('Respond with `start` to start the application! This will expire in 2 minutes', {timeout: 120000})
                console.log(await confirm.run(dmChannel, message.author))
                // confirm.on('collect', async (collected) => {
                //     console.log(collected)
                //     if (collected.content.toLowerCase() === 'start') {
                //         send = true
                //         await message.author.send(`Question ${index+1}. ${questions.rows[0].text}`)
                //     } else if(send) {
                //         await message.author.send(`Question ${index+1}. ${questions.rows[0].text}`)
                //     }
                // })
                // confirm.on('end', async (collected) => {
                //     await message.author.send("Canceled, you took too long to respond!")
                //     send = false
                // })
                if (send) {
                    const yes = db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'accept'])
                    const no = db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", 'deny')
                    const complete = message.guild.channels.fetch(channel.rows[0].text)
                    const give = message.guild.roles.fetch(role.rows.length ? role.rows[0].text : undefined)
                    await message.author.send("Your response has been recorded! You will receive a response soon letting you know if you have been accepted or not")
                    await new PaginateWithConfirm(message, responses, [`Your application has been accepted from ${this.guild.name}!`, `Your application has been denied from ${this.guild.name}!`], yes.rows.length ? yes.rows[0].text : "Congrats! You been accepted", no.rows.length ? no.rows[0].text : "Oh no! You been denied", complete, give).paginate()
                }
                await db.release()
            }
        }
    }
}

// const {SubCommandPluginCommand} = require("@sapphire/plugin-subcommands");
// const {pool} = require("../../database");
// const paginator = require('../../src/structures/paginator');
// const {MessagePrompterMessageStrategy} = require("@sapphire/discord.js-utilities");
// module.exports = class extends SubCommandPluginCommand {
//     constructor(context) {
//         super(context, {
//             name: 'apply',
//             description: "Allows you to create an application",
//             subcommandDescriptions: [{
//                 name: 'list',
//                 aliases: ['view', 'questions'],
//                 description: 'allows you to view current application questions'
//             }],
//             subCommands: [{input: 'apply', default: true}, {input: 'view', output: 'list'}, {input: 'questions', output: 'list'}, 'list']
//         });
//     }
//
//     async apply(message) {
//         const db = await pool.connect()
//         const check = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'require'])
//         const channel = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'channel'])
//         const role = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'role'])
//         if (!channel.rows.length) {
//             await message.channel.send("Applications currently not have been set up yet by this guild!")
//         } else if (!check.rows.find(obj => message.member._roles.includes(obj.text))) {
//             await message.channel.send("You are not allowed to create an application!")
//         } else {
//             // try {
//             //     await message.author.send("Respond with `start` to start the application! This will expire in 2 minutes")
//             // } catch {
//             //     await message.channel.send("The Application could not be sent in your dm's! Ensure Dionysus can send you dm's, then try again.")
//             //     await db.release()
//             //     return
//             // }
//             await message.channel.send("The application is ready to be started in your dm!")
//             const questions = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'question'])
//             let responses = []
//             let send = false
//             const filter = msg => msg.author.id === message.author.id
//             // const confirm = await message.member.createDM().createMessageCollector({max: 1, time: 120000})
//             const dmChannel = await message.author.createDM()
//             const confirm = new MessagePrompterMessageStrategy('Respond with `start` to start the application! This will expire in 2 minutes', {timeout: 120000})
//             console.log(await confirm.run(dmChannel, message.author))
//             // confirm.on('collect', async (collected) => {
//             //     console.log(collected)
//             //     if (collected.content.toLowerCase() === 'start') {
//             //         send = true
//             //         await message.author.send(`Question ${index+1}. ${questions.rows[0].text}`)
//             //     } else if(send) {
//             //         await message.author.send(`Question ${index+1}. ${questions.rows[0].text}`)
//             //     }
//             // })
//             // confirm.on('end', async (collected) => {
//             //     await message.author.send("Canceled, you took too long to respond!")
//             //     send = false
//             // })
//             if (send) {
//                 const yes = db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'accept'])
//                 const no = db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", 'deny')
//                 const complete = message.guild.channels.fetch(channel.rows[0].text)
//                 const give = message.guild.roles.fetch(role.rows.length ? role.rows[0].text : undefined)
//                 await message.author.send("Your response has been recorded! You will receive a response soon letting you know if you have been accepted or not")
//                 await new Paginator.PaginateWithConfirm(message, responses, [`Your application has been accepted from ${this.guild.name}!`, `Your application has been denied from ${this.guild.name}!`], yes.rows.length ? yes.rows[0].text : "Congrats! You been accepted", no.rows.length ? no.rows[0].text : "Oh no! You been denied", complete, give).paginate()
//             }
//         }
//         await db.release()
//     }
//
//     async list(message) {
//         const db = await pool.connect()
//         const list = await db.query("SELECT text FROM questions WHERE guild = $1 and type = $2", [message.guildId, 'question'])
//         if (!list.rows.length) {
//             await message.channel.send("No results!")
//         } else {
//             const pages = new Paginator.paginator(message, list.rows.map(obj => obj.text), true, true, false)
//             pages.embed.setTitle(`${message.guild.name} Current Questions`)
//             await pages.paginate()
//         }
//         await db.release()
//     }
// }