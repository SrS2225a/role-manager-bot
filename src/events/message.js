const {pool} = require("../database");
const {Formatters, Util, MessageEmbed} = require("discord.js");
module.exports = {
    name: 'messageCreate',
    once: false,
    async execute(message) {
        if (message.guild && !message.author.bot) {
            const db = await pool.connect();
            try {
                // code for message graph
                // increment member messages by 1 else add on a new date and delete where the date is older than 120 days
                if (message.content.includes(`<@!${message.client.user.id}>` || message.content.includes(`<@${message.client.user.id}>`))) {
                    const embed = new MessageEmbed()
                        .setTitle('Moved To Discords Slash Command System')
                        .setDescription('Hi there, if you are wondering why your commands are no longer working the reason being is that we have moved to discords new `slash command system` which means that commands are now in the form of `/command` instead of `*command`.' +
                            'This is because message content will become a message intent in March of 2022, requiring bots to apply to use them. (See https://support.discord.com/hc/en-us/articles/4410940809111 for more information).' +
                            '\n\nYou can invite the bot with the new permission scope here: https://discord.com/api/oauth2/authorize?client_id=437447118127366154&permissions=8&scope=bot%20applications.commands')
                        .setColor('WHITE')
                    await message.channel.send({embeds: [embed]})
                }

                const graph = await db.query("SELECT messages, day, member, channel FROM message WHERE guild = $1 and member = $2 and channel = $3 and day = $4 LIMIT 1", [message.guild.id, message.author.id, message.channel.id, new Date()]);
                if (graph.rowCount === 0) {
                    await db.query("INSERT INTO message (guild, member, channel, messages, day) VALUES ($1, $2, $3, 1, $4)", [message.guild.id, message.author.id, message.channel.id, new Date()]);
                    await db.query("DELETE FROM message WHERE day < $1", [new Date(Date.now() - 8640000000)]);
                } else {
                    await db.query("UPDATE message SET messages = messages + 1 WHERE guild = $1 and member = $2 and channel = $3 and day = $4", [message.guild.id, message.author.id, message.channel.id, new Date()]);
                }
                // end of message graph
                // code for leveling
                // message rate limit no-query
                const leveling = await db.query("SELECT * FROM leveling WHERE guild = $1 and system = 'weight'", [message.guild.id]);
                if (leveling.rowCount > 0) {
                    const blacklist = await db.query("SELECT role FROM leveling WHERE guild = $1 and system = $2", [message.guild.id, 'blacklist']);
                    const no = blacklist.rows.map(row => row.role);
                    if (!no.includes(message.channel.id) && !message.member.roles.cache.some(role => no.includes(role.id))) {
                        const xp = await db.query("SELECT user_id, exp, lvl, last_message FROM levels WHERE guild_id = $1 and user_id = $2 LIMIT 1", [message.guild.id, message.author.id]);
                        if (xp.rowCount > 0) {
                            const lvl = xp.rows[0].lvl;
                            const exp = xp.rows[0].exp;
                            const nxtLvl = Math.floor(Math.pow(xp.rows[0].lvl, 1.5) * 100);
                            if (exp >= nxtLvl) {
                                await db.query("UPDATE levels SET lvl = lvl + 1, exp = 0 WHERE guild_id = $1 and user_id = $2", [message.guild.id, message.author.id]);
                                // gets level role and checks if we should replace the level role, or just add it. Including the users previous level role
                                const role = await db.query("SELECT role FROM leveling WHERE guild = $1 and system = $2 and level = $3", [message.guild.id, 'rank', lvl + 1]);
                                if (role.rowCount > 0) {
                                    const behavoir = await db.query("SELECT type FROM leveling WHERE guild = $1 and system = $2", [message.guild.id, 'behavior']);
                                    if (behavoir.rowCount > 0) {
                                        if (behavoir.rows[0].type === "true") {
                                            const member = message.guild.members.cache.get(message.author.id);
                                            if (member) {
                                                const role = message.guild.roles.cache.get(role.rows[0].role);
                                                if (role) {
                                                    await member.roles.add(role);
                                                }
                                            }
                                        } else {
                                            const member = message.guild.members.cache.get(message.author.id);
                                            if (member) {
                                                const role = message.guild.roles.cache.get(role.rows[0].role);
                                                if (role) {
                                                    const prevRole = await db.query("SELECT role FROM leveling WHERE guild = $1 and system = $2 and level < $3 LIMIT 1", [message.guild.id, 'rank', lvl + 1]);
                                                    if (prevRole.rowCount > 0) {
                                                        const prevRole = message.guild.roles.cache.get(prevRole.rows[0].role);
                                                        if (prevRole) {
                                                            member.roles.remove(prevRole);
                                                        }
                                                    }
                                                    await member.roles.add(role);
                                                }
                                            }
                                        }
                                    }
                                }
                                message.channel.send(`${message.author.username} has leveled up to level ${lvl + 1}!`);
                            } else if (Date.now() - xp.rows[0].last_message > 60000) {
                                let xp_gain = leveling.rows[0].difficulty
                                const multiplier = await db.query("SELECT role, difficulty FROM leveling WHERE guild = $1 and system = $2 and type = $3 LIMIT 1", [message.guild.id, 'multiplier', 'text']);
                                if (multiplier.rowCount > 0) {
                                    for (let i = 0; i < multiplier.rowCount; i++) {
                                        if (message.channel.id === multiplier.rows[i].role) {
                                            xp_gain += multiplier.rows[i].difficulty;
                                        }
                                    }
                                }
                                await db.query("UPDATE levels SET exp = exp + $1, last_message = $2 WHERE guild_id = $3 and user_id = $4", [Math.floor(Math.random() * xp_gain), message.createdAt, message.guild.id, message.author.id]);
                            }
                        } else {
                            await db.query("INSERT INTO levels VALUES ($1, $2, 1, 1, $3)", [message.guild.id, message.author.id, message.createdAt]);
                        }
                    }
                }
                // end of leveling
                // code for counting
                const count = await db.query("SELECT * FROM count WHERE guild = $1 and channel = $2", [message.guild.id, message.channel.id]);
                if (count.rowCount > 0) {
                    if (count.rows[0].member !== message.author.id) {
                        if (message.content.includes(count.rows[0].number)) {
                            await db.query("UPDATE count SET number = number + 1, member = $1 WHERE guild = $2", [message.author.id, message.guild.id]);
                            if (count.rows[0].count) {
                                await message.channel.edit({
                                    topic: `The next number is: ${count.rows[0].number + 1}`
                                })
                            }
                        } else {
                            const forgotSend = await message.channel.send({content: `${Formatters.userMention(message.author.id)} just forgot how to count!`,});
                            setTimeout(async () => {
                                await forgotSend.delete();
                            }, 5000);
                            if (count.rows[0].delay > 0) {
                                await message.member.roles.add({roles: [count.rows[0].role]});
                                setTimeout(async () => {
                                    await message.member.roles.remove({roles: [count.rows[0].role]});
                                }, count.rows[0].delay * 1000);
                            }
                        }
                    } else {
                        const lonelySend = await message.channel.send({content: `${Formatters.userMention(message.author.id)} is lonely and needs someone to count with!`});
                        setTimeout(async () => {
                            await lonelySend.delete();
                        }, 5000);
                    }
                }
                // end of counting
                // code for partnerships
                const partner = await db.query("SELECT * FROM leveling WHERE guild = $1 and system = 'partners'", [message.guild.id]);
                if (partner.rowCount > 0) {
                    const role = await message.guild.roles.cache.get(partner.rows[0].role);
                    if (message.member.roles.cache.has(role) && /.*[https://]?discord(.*(gg))\S?\w{7}.*\n?/.test(message.content)) {
                        const partner_id = await db.query("SELECT number FROM partner WHERE guild = $1 and user = $2", [message.guild.id, message.author.id]);
                        if (partner_id.rowCount > 0) {
                            await db.query("UPDATE partner SET number = number + 1 WHERE guild = $1 and member = $2", [message.guild.id, message.author.id]);
                            // if enabled congratulates the partner manager if they complete a number of partners
                            if (partner.rows[0].level) {
                                for (let i = 0; i < partner.rowCount; i++) {
                                    if (partner_id.rows[0].number === partner.rows[i].level) {
                                        const role = await message.guild.roles.cache.get(partner.rows[i].role);
                                        await message.member.roles.add({roles: [role]});
                                        const channel = await message.guild.channels.cache.get(partner.rows[i].channel);
                                        await channel.send({content: `Congratulations ${Formatters.userMention(message.author.id)}! You have completed ${partner.rows[0].level} partners!`});
                                    }
                                }
                            }
                        } else {
                            await db.query("INSERT INTO partner (guild, member, number) VALUES ($1, $2, 1)", [message.guild.id, message.author.id]);
                        }
                    }
                }
                // end of partnerships
                // code for afk
                const afk = await db.query("SELECT * FROM afk WHERE guild = $1", [message.guild.id]);
                for (const row of afk.rows) {
                    if (row.member === message.author.id) {
                        if (row.count > 4) {
                            // unmark the user as afk
                            await db.query("DELETE FROM afk WHERE guild = $1 and member = $2", [message.guild.id, message.author.id]);
                            // send a message to the channel
                            await message.channel.send({content: `${Formatters.userMention(message.author.id)} is no longer AFK!`});
                        } else {
                            await db.query("UPDATE afk SET count = count + 1 WHERE guild = $1 and member = $2", [message.guild.id, message.author.id]);
                        }
                    }
                    // check if the mentioned user is afk, and if they are, tell the member that mentioned them
                    else if (message.mentions.users.has(row.member)) {
                        const member = await message.guild.members.fetch(row.member);
                        await message.channel.send({content: `${Formatters.userMention(member.id)} is AFK! For the reason: ${Util.removeMentions(row.message)}`});
                    }
                }
                // end of afk
            } catch (e) {
                console.log(e);
            } finally {
                await db.release();
            }
        }
    }
}