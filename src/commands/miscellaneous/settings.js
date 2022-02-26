const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {Formatters} = require("discord.js");
const {display_time} = require("../../structures/converters");
const AsciiTable = require("ascii-table")
module.exports = {
    data: new SlashCommandBuilder()
        .setName("settings")
        .setDescription("Lets you view your configured bot settings for your server or a specific one")
        .addStringOption(option =>
        option.setName("setting")
            .setDescription("Lets you view a specific setting")),
    async execute(message) {
        const db = await pool.connect()
        let ident_flag = false
        let sent = false
        const setting = await message.options.getString("setting") || null
        if (!setting) {
            ident_flag = true
            await message.reply("Sending all settings to your dm, please wait...")
        }
        if (setting === 'club' || ident_flag) {
            const clubs = await db.query("SELECT role, level, type, difficulty FROM leveling WHERE guild = $1 and system = $2", [message.guildId, 'points'])
            let clubs_table = []
            for (const club of clubs.rows) {
                const category = await message.guild.channels.fetch(club.role)
                const channel = await message.guild.channels.fetch(club.level)
                const role = await message.guild.roles.fetch(club.type)
                const give = await message.guild.roles.fetch(club.difficulty)
                clubs_table.push([category?.name, channel?.name, role?.name, give?.name])
            }

            if (!clubs_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Channel', 'Category', 'Role', 'Give')
                    .addRowMatrix(clubs_table)
                const clubsSend = `**Club Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(clubsSend)} else {await message.reply(clubsSend)}
            }
        }
        if (setting === 'custom' || ident_flag) {
            const custom = await db.query("SELECT * FROM custom WHERE guild = $1", [message.guildId])
            let custom_table = []
            for (const result of custom.rows) {
                const role = await message.guild.roles.fetch(result.role)
                const position = await message.guild.roles.fetch(result.position)
                custom_table.push([result?.system, role?.name, position?.name, result?.amount, result?.tag, result?.remove])
            }
            if (!custom_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Type', 'Role', 'Position', 'Amount', 'Tag', 'Remove')
                    .addRowMatrix(custom_table)
                const customSend = `**Custom Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(customSend)} else {await message.reply(customSend)}
            }
        }
        if (setting === 'count' || ident_flag) {
            const count = await db.query("SELECT channel, role, count, delay FROM count WHERE guild = $1", [message.guildId])
            let count_table = []
            for (const result of count.rows) {
                const channel = await message.guild.channels.fetch(result.channel)
                const role = await message.guild.roles.fetch(result.role)
                count_table.push([channel?.name, role?.name, result?.count, display_time(result?.delay)])
            }
            if (!count_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Channel', 'Role', 'Count', 'Delay')
                    .addRowMatrix(count_table)
                const countSend = `**Counter Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(countSend)} else {await message.reply(countSend)}
            }
        }
        if (setting === 'booster' || ident_flag) {
            const booster = await db.query("SELECT role, date FROM boost WHERE guild = $1 and type = $2", [message.guildId, 'boost'])
            let boost_table = []
            for (const result of booster.rows) {
                const role = await message.guild.roles.fetch(result.role)
                boost_table.push([role?.name, result?.date])
            }
            if (!boost_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Role', 'Day')
                    .addRowMatrix(boost_table)
                const boostSend = `**Booster Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(boostSend)} else {await message.reply(boostSend)}
            }
        }
        if (setting === 'invite' || ident_flag) {
            const invite = await db.query("SELECT role, date FROM boost WHERE guild= $1 and type= $2", [message.guildId, 'invite'])
            let invite_table = []
            for (const result of invite.rows) {
                const role = await message.guild.roles.fetch(result.role)
                invite_table.push([role?.name, result?.date])
            }
            if (!invite_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Role', 'Day')
                    .addRowMatrix(invite_table)
                const inviteSend = `**Invite Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(inviteSend)} else {await message.reply(inviteSend)}
            }
        }
        if (setting === 'overwrite' || ident_flag) {
            const overwrite = await db.query("SELECT member, role FROM roles WHERE guild= $1 and type= $2", [message.guildId, 'recover'])
            let overwrite_table = []
            for (const result of overwrite.rows) {
                const channel = await message.guild.channels.fetch(result.member)
                const role = await message.guild.roles.fetch(result.role)
                overwrite_table.push([channel?.name, role?.name])
            }
            if (!overwrite_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Channel', 'Role')
                    .addRowMatrix(overwrite_table)
                const overwriteSend = `**Channel Overwrite Settings \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(overwriteSend)} else {await message.reply(overwriteSend)}
            }
        }
        if (setting === 'position' || ident_flag) {
            const position_table = []
            const position = await db.query("SELECT type, role, member FROM roles WHERE guild = $1 and type = $2 or type = $3", [message.guildId, 'create', 'join'])
            for (const result of position.rows) {
                const role = await message.guild.roles.fetch(result.role)
                position_table.push([result?.type, role?.name, display_time(result?.member)])
            }
            const table = new AsciiTable()
                .setHeading('Type', 'Role', 'Time')
                .addRowMatrix(position_table)
            const positionTable = `**Auto Position Settings** ${Formatters.codeBlock(table.toString())}`
            if (ident_flag) {await message.user.send(positionTable)} else {await message.reply(positionTable)}
        }
        if (setting === 'autorole' || ident_flag) {
            const autorole = await db.query("SELECT type, role, member FROM roles WHERE guild = $1 and type = $2 or type = $3", [message.guildId, 'add', 'remove'])
            let autorole_table = []
            for (const result of autorole.rows) {
                const role = await message.guild.roles.fetch(result.role)
                autorole_table.push([result?.type, role?.name, display_time(result?.member)])
            }
            if(!autorole_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Type', 'Role', 'Time')
                    .addRowMatrix(autorole_table)
                const autoroleSend = `**Auto Role Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(autoroleSend)} else {await message.reply(autoroleSend)}
            }
        }
        if (setting === 'sticky' || ident_flag) {
            const sticky = await db.query("SELECT role FROM reward WHERE guild = $1 and type= $2", [message.guildId, 'sticky'])
            const sticky_table = []
            for (const result of sticky.rows) {
                const role = await message.guild.roles.fetch(result.role)
                sticky_table.push([role?.name])
            }
            if (!sticky_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('role')
                    .addRowMatrix(sticky_table)
                const stickySend = `**Sticky Role Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(stickySend)} else {await message.reply(stickySend)}
            }
        }
        if (setting === 'announce' || ident_flag) {
            const announce = await db.query("SELECT announce FROM settings WHERE guild= $1", [message.guildId])
            if (announce.rows[0].announce) {
                sent = true
                const channel = await message.guild.channels.fetch(announce.rows[0].announce)
                const announceSend = `**Announce Settings** \n${Formatters.codeBlock(channel.name)}`
                if (ident_flag) {await message.user.send(announceSend)} else {await message.reply(announceSend)}
            }
        }
        if (setting === 'suggest' || ident_flag) {
            const suggest = await db.query("SELECT suggest FROM settings WHERE guild= $1", [message.guildId])
            if (suggest.rows[0].suggest) {
                sent = true
                const channel = await message.guild.channels.fetch(suggest.rows[0].suggest)
                const suggeestSend = `**Suggest Settings** \n${Formatters.codeBlock(channel.name)}`
                if (ident_flag) {await message.user.send(suggeestSend)} else {await message.reply(suggeestSend)}
            }
        }
        if (setting === 'flags' || ident_flag) {
            const flags = await db.query("SELECT role, date FROM boost WHERE guild= $1 and type = $2", [message.guildId, 'flag'])
            const flag_table = []
            for (const result of flags.rows) {
                const role = await message.guild.roles.fetch(result.role)
                flag_table.push([role?.name, result?.date])
            }
            if(!flag_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Role', 'Flag')
                    .addRowMatrix(flag_table)
                const flagsSend = `**Flag Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(flagsSend)} else {await message.reply(flagsSend)}
            }
        }
        if (setting === 'partnership' || ident_flag) {
            const partnership = await db.query("SELECT level, difficulty, type, role FROM leveling WHERE guild= $1 and system = $2", [message.guildId, 'partners'])
            let partnership_table = []
            for (const result of partnership.rows) {
                const channel = await message.guild.channels.fetch(result.type)
                const role = await message.guild.roles.fetch(result.role)
                const reward = await message.guild.roles.fetch(result.difficulty)
                partnership_table.push([channel?.name, role?.name, reward?.name, result?.level])
            }
            if (!partnership_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Channel', 'Role', 'Reward', 'Amount')
                    .addRowMatrix(partnership_table)
                const partnershipSend = `**Partnership Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(partnershipSend)} else {await message.reply(partnershipSend)}
            }
        }
        if (setting === 'leveling' || ident_flag) {
            const leveling = await db.query("SELECT system, difficulty, role, level FROM leveling WHERE guild = $1 and not system = $2 and not system = $3", [message.guildId, 'partners', 'points'])
            let leveling_table = []
            for (const result of leveling.rows) {
                const role = await message.guild.roles.fetch(result.role)
                const channel = await message.guild.channels.fetch(result.level)
                leveling_table.push([result?.system, channel?.name, role?.name, result?.difficulty])
            }
            if (!leveling_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('Type', 'Channel', 'Role', 'Value')
                    .addRowMatrix(leveling_table)
                const levelingSend = `**Leveling Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(levelingSend)} else {await message.reply(levelingSend)}
            }
        }
        if(setting === 'reaction' || ident_flag) {
            const reaction = await db.query("SELECT * FROM reaction WHERE guild = $1", [message.guildId])
            let reaction_table = []
            for (const result of reaction.rows) {
                const role = await message.guild.roles.fetch(result.role)
                const channel = await message.guild.channels.fetch(result.channel)
                const blacklist = await message.guild.roles.fetch(result.blacklist)
                reaction_table.push([role?.name, channel?.name, blacklist?.name, result?.message, result?.emote, result?.type])
            }
            if (!reaction_table.length === 0) {
                sent = true
                const table = new AsciiTable()
                    .setHeading('role', 'channel', 'blacklist', 'message', 'emote', 'type')
                    .addRowMatrix(reaction_table)
                const reactionSend = `**Reaction Settings** \n${Formatters.codeBlock(table.toString())}`
                if (ident_flag) {await message.user.send(reactionSend)} else {await message.reply(reactionSend)}
            }
            if (sent && ident_flag) {
                await message.editReply("The list of current settings has been sent to your dm!")
            }
        }
    }
}