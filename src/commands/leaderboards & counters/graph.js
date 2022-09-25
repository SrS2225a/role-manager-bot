const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {MessageEmbed, MessageAttachment, PermissionsBitField, EmbedBuilder, Colors, AttachmentBuilder} = require("discord.js");
const {ChartJSNodeCanvas} = require("chartjs-node-canvas");
const {ConvertDate, display_time} = require("../../structures/converters");
const {clientPermissions} = require("../../structures/permissions");

function getDayDelta(value) {
    const date = (Date.now() - ConvertDate((value || 30).toString() + ' days') * 1000)
    return new Date(date)
}

module.exports = {
    data: new SlashCommandBuilder()
        .setName("graph")
        .setDescription("Displays a graph of a counter.")
        .addSubcommand(subcommand => subcommand
            .setName("members")
            .setDescription("Displays a graph of the number of members in the server."))
        .addSubcommand(subcommand => subcommand
            .setName("messages")
            .setDescription("Displays a graph of the number of messages sent in the server."))
        .addSubcommand(subcommand => subcommand
            .setName("voice")
            .setDescription("Displays a graph of the number of voice members in the server."))
        .addSubcommand(subcommand => subcommand
                .setName("invites")
                .setDescription("Shows someones invites over a period of time.")
            .addUserOption(option => option
                .setName("invite")
                .setDescription("The member to show the invites of.")
                .setRequired(false))),
    async execute(message) {
        const db = await pool.connect()
        clientPermissions(message, [PermissionsBitField.Flags.EmbedLinks, PermissionsBitField.Flags.AttachFiles]);
        if (message.options.getSubcommand() === "members") {
            const lookback = await db.query("SELECT lookback FROM settings WHERE guild = $1", [message.guild.id])
            const members = await db.query("SELECT sum(joins)::integer AS joins, sum(leaves)::integer AS leaves, day FROM member WHERE guild = $1 and day > $2 group by day order by day DESC", [message.guildId, getDayDelta(lookback.rows[0]?.lookback || 30)])
            let day = [0, 0]
            let week = [0, 0]
            let month = [0, 0]
            let x = []
            let y1 = []
            let y2 = []
            if (members.rows.length === 0) {
                message.reply("No data to display.")
                return
            }
            const max = Math.round(Date.parse(members.rows[0].day))
            for (const row of members.rows) {
                row.day = Math.round(Date.parse(row.day))
                month[0] += row.joins
                month[1] += row.leaves
                if (max === row.day) {
                    day[0] += row.joins
                    day[1] += row.leaves
                }
                else if (max - 24 * 60 * 60 * 1000 <= row.day) {
                    week[0] += row.joins
                    week[1] += row.leaves
                }
                x.push(row.day)
                y1.push(row.joins)
                y2.push(row.leaves)
            }
            const embed = new EmbedBuilder()
                .setTitle(`${message.guild.name} Member Graph`)
                .setDescription(`Showing the last ${lookback[0]?.lookback || 30} days.`)
                .setColor(Colors.White)
                .addFields({name: "Members Joined", value: `${month[0]}`, inline: true}, {name: "Members Left", value: `${month[1]}`, inline: true}, {name: "Total Members", value: `${message.guild.memberCount}`, inline: true}, {name: "Member Retention", value: `${Math.round(month[0] / (month[0] + month[1]) * 100)}%`, inline: true}, {name: "Average Change", value: `${Math.round((month[0] - month[1]) / (month[0] + month[1]) * 100)}%`, inline: true}, {name: "Net Change", value: `${month[0] - month[1]}`, inline: true}, {name: "Day", value: `${day[0]} joins, ${day[1]} leaves`, inline: true}, {name: "Week", value: `${week[0]} joins, ${week[1]} leaves`, inline: true}, {name: "Month", value: `${month[0]} joins, ${month[1]} leaves`, inline: true})
            const chart = new ChartJSNodeCanvas({width: 800, height: 600,  plugins: {
                    globalVariableLegacy: ['chartjs-adapter-moment']}})
            const chartData = {
                type: "line",
                data: {
                    labels: x,
                    datasets: [
                        {
                            label: "Joins",
                            data: y1,
                            backgroundColor: "rgba(0, 174, 134, 0.2)",
                            borderColor: "rgba(0, 174, 134, 1)",
                            borderWidth: 1,
                            fill: y1 < y2 ? 'origin' : '+1'
                        },
                        {
                            label: "Leaves",
                            data: y2,
                            backgroundColor: "rgba(255, 0, 0, 0.2)",
                            borderColor: "rgba(255, 0, 0, 1)",
                            borderWidth: 1,
                            fill: y1 < y2 ? '-1' : 'origin',
                        }
                    ]
                },
                options: {
                    scales: {
                        x: {
                            ticks: {
                                font: {
                                    size: 14,
                                    weight: "bold"
                                },
                                color: 'white'
                            },
                            grid: {
                                color: 'white'
                            },
                            type: "time",
                            time: {
                                unit: "day",
                                tooltipFormat: "MMM DD"
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: {
                                    size: 14,
                                    weight: "bold"
                                },
                                color: 'white'
                            },
                            grid: {
                                color: 'white'
                            }
                        },
                    },
                    plugins: {
                        legend: {
                            labels: {
                                font: {
                                    size: 18
                                },
                                color: 'white',
                                textDecoration: 'ltr'
                            }
                        }
                    }
                }
            }
            const attachment = new AttachmentBuilder(chart.renderToStream(chartData))
            embed.setImage("attachment://file.jpg")
            message.reply({embeds: [embed], files: [attachment]})

        } else if (message.options.getSubcommand() === "messages") {
            const date = await db.query("SELECT lookback FROM settings WHERE guild = $1", [message.guild.id])
            const messages = await db.query("SELECT sum(messages)::integer, day FROM message WHERE guild = $1 and day > $2 GROUP BY day ORDER BY day DESC", [message.guildId, getDayDelta(date.rows[0]?.lookback || 30)])
            const x = []
            const y = []
            let day = 0
            let week = 0
            let month = 0
            if (messages.rows.length === 0) {
                message.reply("No data to display.")
                return
            }
            
            const max = Math.round(Date.parse(messages.rows[0].day))
            for (const row of messages.rows) {
                row.day = Math.round(Date.parse(row.day))
                month += row.sum
                if (max === row.day) {
                    day += row.sum
                }
                else if (max - 24 * 60 * 60 * 1000 <= row.day) {
                    week += row.sum
                }
                x.push(row.day)
                y.push(row.sum)
            }
            let topUser = ''
            const members = await db.query("SELECT member, sum(messages)::integer FROM message WHERE guild = $1 and day > $2 GROUP BY member ORDER BY sum(messages) DESC LIMIT 5", [message.guildId, getDayDelta(date.rows[0]?.lookback || 30)])
            for (const row of members.rows) {
                topUser += `<@${row.member}> - ${row.sum}\n`
            }
            let topChannel = ''
            const channels = await db.query("SELECT channel, sum(messages)::integer FROM message WHERE guild = $1 and day > $2 GROUP BY channel ORDER BY sum(messages) DESC LIMIT 5", [message.guildId, getDayDelta(date.rows[0]?.lookback || 30)])
            for (const row of channels.rows) {
                topChannel += `<#${row.channel}> - ${row.sum}\n`
            }
            const embed = new EmbedBuilder()
                .setColor(Colors.White)
                .setTitle(`Messages in ${message.guild.name}`)
                .setDescription(`Showing the last ${date.rows[0]?.lookback || 30} days`)
                .addFields({name: "Day", value: `${day} messages`, inline: true}, {name: "Week", value: `${week} messages`, inline: true}, {name: "Month", value: `${month} messages`, inline: true}, {name: "Average Messages", value: `${Math.round(y.reduce((a, b) => a + b, 0) / y.length)} messages`, inline: true}, {name: "Top Users", value: topUser, inline: true}, {name: "Top Channels", value: topChannel, inline: true})
            const chart = new ChartJSNodeCanvas({width: 800, height: 600, plugins: {
                    globalVariableLegacy: ['chartjs-adapter-moment']}})
            const chartData = {
                type: "line",
                data: {
                    labels: x,
                    datasets: [{
                        data: y,
                        label: "Messages",
                        backgroundColor: "rgba(0, 174, 134, 0.2)",
                        borderColor: "rgba(0, 174, 134, 1)",
                        borderWidth: 1,
                        fill: 'origin'
                    }]
                },
                options: {
                    scales: {
                        x: {
                            ticks: {
                                font: {
                                    size: 14,
                                    weight: "bold"
                                },
                                color: 'white'
                            },
                            grid: {
                                color: 'white'
                            },
                            type: "time",
                            time: {
                                unit: "day",
                                tooltipFormat: "MMM DD"
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: {
                                    size: 14,
                                    weight: "bold"
                                },
                                color: 'white'
                            },
                            grid: {
                                color: 'white'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                font: {
                                    size: 18
                                },
                                color: 'white',
                                textDecoration: 'ltr'
                            }
                        }
                    }
                }
            }
            const attachment = new AttachmentBuilder(chart.renderToStream(chartData))
            embed.setImage("attachment://file.jpg")
            message.reply({embeds: [embed], files: [attachment]})
        } else if (message.options.getSubcommand() === "voice") {
            let day = [0, 0]
            let week = [0, 0]
            let month = [0, 0]
            let x = []
            let y1 = []
            let y2 = []
            const date = await db.query("SELECT lookback FROM settings WHERE guild= $1", [message.guildId])
            const voice = await db.query("SELECT sum(voice)::integer AS a, sum(voice2)::integer AS b, day FROM voice WHERE guild = $1 and day > $2 GROUP BY day ORDER BY day DESC", [message.guildId, getDayDelta(date.rows[0]?.lookback || 30)])
            if (voice.rows.length === 0) {
                message.reply("No data to display.")
                return
            }
            const max = Math.round(Date.parse(voice.rows[0].day))
            for (const row of voice.rows) {
                row.day = Math.round(Date.parse(row.day))
                x.push(row.day)
                y1.push(Math.round(row.a / 60))
                y2.push(Math.round(row.b / 60))
                if (row.day === max) {
                    day[0] += row.a
                    day[1] += row.b
                } else if (max - 24 * 60 * 60 * 1000 <= row.day)
                 {
                     week[0] += row.a
                     week[1] += row.b
                }
                month[0] += row.a
                month[1] += row.b
            }
            let topUser = ""
            let topChannel = ""

            const totalUserCount = await db.query("SELECT count(distinct member)::integer FROM voice WHERE guild=$1", [message.guildId])
            const voiceUser = await db.query("SELECT member, SUM(voice) + SUM(voice2)::integer AS a FROM voice WHERE guild = $1 and day > $2 GROUP BY member ORDER BY sum(voice) + sum(voice2) LIMIT 5", [message.guildId, getDayDelta(date.rows[0]?.lookback || 30)])
            const voiceChannel = await db.query("SELECT channel, SUM(voice) + SUM(voice2)::integer AS b FROM voice WHERE guild = $1 and day > $2 GROUP BY channel ORDER BY sum(voice) + sum(voice2) LIMIT 5", [message.guildId, getDayDelta(date.rows[0]?.lookback || 30)])
            for (const row of voiceUser.rows) {
                topUser += `<@${row.member}> - ${display_time(row.a, 6)} \n`
            }
            for (const row of voiceChannel.rows) {
                topChannel += `<#${row.channel}> - ${display_time(row.b, 6)} \n`
            }
            const embed = new EmbedBuilder()
                .setColor(Colors.White)
                .setTitle(`Voice Activity for ${message.guild.name}`)
                .setDescription(`Showing the last ${date.rows[0]?.lookback || 30} days`)
                .addFields({name: "Day", value: `${display_time(day[0], 6)} voice and ${display_time(day[1], 6)} stage`, inline: true}, {name: "Week", value: `${display_time(week[0], 6)} voice and ${display_time(week[1], 6)} stage`, inline: true}, {name: "Month", value: `${display_time(month[0], 6)} voice and ${display_time(month[1], 6)} stage`, inline: true}, {name: "Average per user", value: `${display_time(Math.round(month[0] / totalUserCount.rows[0].count), 6)} voice and ${display_time(Math.round(month[1] / totalUserCount.rows[0].count), 6)} stage`, inline: true}, {name: "Top users", value: topUser, inline: true}, {name: "Top channels", value: topChannel, inline: true})

            const chart = new ChartJSNodeCanvas({width: 800, height: 600,  plugins: {
                    globalVariableLegacy: ['chartjs-adapter-moment']}})
            const chartData = {
                type: "line",
                data: {
                    labels: x,
                    datasets: [
                        {
                            label: "Voice",
                            data: y1,
                            backgroundColor: "rgba(0, 174, 134, 0.2)",
                            borderColor: "rgba(0, 174, 134, 1)",
                            borderWidth: 1,
                            fill: y1 < y2 ? 'origin' : '+1'
                        },
                        {
                            label: "Stage",
                            data: y2,
                            backgroundColor: "rgba(255, 0, 0, 0.2)",
                            borderColor: "rgba(255, 0, 0, 1)",
                            borderWidth: 1,
                            fill: y1 < y2 ? '-1' : 'origin',
                        }
                    ]
                },
                options: {
                    scales: {
                        x: {
                            ticks: {
                                font: {
                                    size: 14,
                                    weight: "bold"
                                },
                                color: 'white'
                            },
                            grid: {
                                color: 'white'
                            },
                            type: "time",
                            time: {
                                unit: "day",
                                tooltipFormat: "MMM DD"
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: {
                                    size: 14,
                                    weight: "bold"
                                },
                                color: 'white'
                            },
                            grid: {
                                color: 'white'
                            }
                        },
                    },
                    plugins: {
                        legend: {
                            labels: {
                                font: {
                                    size: 18
                                },
                                color: 'white',
                                textDecoration: 'ltr'
                            }
                        }
                    }
                }
            }
            const attachment = new AttachmentBuilder(chart.renderToStream(chartData))
            embed.setImage("attachment://file.jpg")
            message.reply({embeds: [embed], files: [attachment]})
        }
        else if (message.options.getSubcommand() === "invites") {
            // Invite tracking as in
            // Graphically showing someone’s invites over time
            const invite = message.options.getUser("invite") || message.user
            const date = await db.query("SELECT lookback FROM settings WHERE guild = $1", [message.guild.id])
            const invites = await db.query("SELECT sum(amount)::integer AS a, sum(amount2)::integer AS b, sum(amount3)::integer AS c, day FROM invite WHERE guild = $1 and member = $2 and day > $3 GROUP BY day ORDER BY day DESC ", [message.guild.id, invite.id, getDayDelta(date.rows[0]?.lookback || 30)])

            let day = [0, 0]
            let week = [0, 0]
            let month = [0, 0]
            const x = []
            const y = []
            if (invites.rows.length === 0) {
                message.reply("Could not find that user!")
                return
            }

            const max = Math.round(Date.parse(invites.rows[0].day))
            for (const row of invites.rows) {
                row.day = Math.round(Date.parse(row.day))
                x.push(row.day)
                y.push(row.a + (row.b - row.c))

                if (row.day === max) {
                    day[0] += row.a
                    day[1] += row.b + row.c
                } else if (max - 24 * 60 * 60 * 1000 <= row.day) {
                    week[0] += row.a
                    week[1] += row.b + row.c
                }
                month[0] += row.a
                month[1] += row.b + row.c
            }

            const embed = new EmbedBuilder()
                .setColor(Colors.White)
                // invite joins over time
                .setTitle(`${invite.username + '#' + invite.discriminator} Invite Joins`)
                .setDescription(`Showing the last ${date.rows[0]?.lookback || 30} days.`)
                .addFields({name: "Day", value: `${day[0]} Joins, ${day[1]} False`, inline: true}, {name: "Week", value: `${week[0]} Joins, ${week[1]} False`, inline: true}, {name: "Month", value: `${month[0]} Joins, ${month[1]} False`, inline: true}, {name: "Average", value: `${Math.round(month[0] / (month[1] + week[1] + day[1]))} Joins, ${Math.round(month[1] / (month[1] + week[1] + day[1]))} Leaves`, inline: true}, {name: "Total", value: invites.rows.reduce((a, b) => a + b.a, 0).toString(), inline: true})

            const chart = new ChartJSNodeCanvas({width: 800, height: 600, plugins: {globalVariableLegacy: ['chartjs-adapter-moment']}})
            const chartData = {
                type: 'line',
                data: {
                    labels: x,
                    datasets: [
                        {
                            label: 'Invites',
                            backgroundColor: "rgba(0, 174, 134, 0.2)",
                            borderColor: "rgba(0, 174, 134, 1)",
                            data: y,
                            fill: 'origin',
                        }
                    ]
                },
                options: {
                    scales: {
                        x: {
                            ticks: {
                                font: {
                                    size: 14,
                                    weight: "bold"
                                },
                                color: 'white'
                            },
                            grid: {
                                color: 'white'
                            },
                            type: "time",
                            time: {
                                unit: "day",
                                tooltipFormat: "MMM DD"
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: {
                                    size: 14,
                                    weight: "bold"
                                },
                                color: 'white'
                            },
                            grid: {
                                color: 'white'
                            }
                        },
                    },
                    plugins: {
                        legend: {
                            labels: {
                                font: {
                                    size: 18,
                                },
                                color: 'white',
                                textDecoration: 'ltr'
                            }
                        }
                    }
                }
            }
            const attachment = new AttachmentBuilder(chart.renderToStream(chartData))
            embed.setImage("attachment://file.jpg")
            message.reply({embeds: [embed], files: [attachment]})
        }
        await db.release()
    }
}