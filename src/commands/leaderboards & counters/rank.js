const {SlashCommandBuilder, ContextMenuCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {MessageEmbed} = require("discord.js");
const {ProgressBar} = require("../../structures/converters");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("rank")
        .setDescription("Shows your current rank in the leaderboard.")
        .addUserOption(option => option
            .setName("user")
            .setDescription("The user to check the rank of.")
            .setRequired(false)),
    context: new ContextMenuCommandBuilder()
        .setName("Rank")
        .setType(2),
    async execute(message) {
        const db = await pool.connect();
        const user = await message.options.getUser("user") || message.user
        const userId = user ? user.id : message.author.id;
        const difficulty = await db.query("SELECT difficulty FROM leveling WHERE guild = $1 and system = $2", [message.guild.id, "weight"]);
        if (difficulty.rows.length) {
            const result = await db.query("SELECT exp, lvl FROM levels WHERE guild_id = $1 and user_id = $2", [message.guild.id, userId]);
            if (result.rows.length) {
                const exp = result.rows[0].exp;
                const lvl = result.rows[0].lvl;
                // await db.query("SELECT COUNT(*) FROM (SELECT member, SUM(voice)::integer AS a, SUM(voice2)::integer AS b FROM voice WHERE guild = $1 GROUP BY member ORDER BY sum(voice) DESC, sum(voice2) DESC) AS t WHERE member = $2"
                const place = await db.query("SELECT COUNT(*)::integer FROM (SELECT user_id, sum(exp)::integer AS a, sum(lvl)::integer AS b FROM levels WHERE guild_id = $1 GROUP BY user_id ORDER BY sum(exp) DESC , sum(lvl) DESC) AS t WHERE a >= $2 AND b >= $3", [message.guild.id, exp, lvl]);
                const rank = place.rows[0].count;
                const nextLvl = Math.floor(Math.pow(lvl, 1.5) * 100)
                // const nextLvl = Math.floor(Math.pow(lvl, difficulty.rows[0].difficulty) * 100);)
                const embed = new MessageEmbed()
                    .setTitle(`${user ? user.username : message.author.username}'s rank`)
                    .addFields(
                        {name: "Rank", value: rank.toString(), inline: true},
                        {name: "Level", value: lvl.toString(), inline: true},
                        {name: "Experience", value: exp.toString() + "/" + nextLvl.toString(), inline: true},
                        {name: "Progress", value: ProgressBar(nextLvl, exp), inline: true}
                    )
                await message.reply({embeds: [embed]});
            } else {
                const embed = new MessageEmbed()
                    .setTitle(`${user ? user.username : message.author.username}'s rank`)
                    .addFields(
                        {name: "Rank", value: "0", inline: true},
                        {name: "Level", value: "0", inline: true},
                        {name: "Experience", value: "0", inline: true},
                        {name: "Progress", value: ProgressBar(Math.floor(Math.pow(1, difficulty.rows[0].difficulty) * 100), 0), inline: true}
                    )
                await message.reply({embeds: [embed]});
            }
        } else {
            await message.reply("The leveling feature has not been set up by this server yet!")
        }
        await db.release();
    }
}