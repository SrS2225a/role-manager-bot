const packageDetails = require("../../package.json");
const {Reminder, Giveaway, Poll, AutoRole, GlobalTasks} = require("../structures/tasks");
const {ownerPermissions} = require("../structures/permissions");
const {Collection} = require("discord.js");
const json = require('../config.json');
module.exports = {
    name: 'ready',
    once: true,
    async execute(bot) {
        console.log(`\n\nCreated by: Nyx#8614 and Vendron#2001\nLogged in as: ${bot.user.username} - ${bot.user.id}\ndiscord.js & postgres Version: ${packageDetails.dependencies["discord.js"]} - ${packageDetails.dependencies["pg"]}\n`)
        bot.user.setActivity("the greek multi-bot @ dionysus.gg", {type: "PLAYING"})
        // run tasks
        await new Reminder().dispatch_reminder(bot)
        await new Giveaway().dispatch_giveaway(bot)
        await new Poll().dispatch_poll(bot)
        await new AutoRole().dispatch_autorole(bot)
        await new GlobalTasks().dispatch_global_tasks(bot)

        // define bot.set for usage with .set
        bot.invites = new Collection()
        // noinspection ES6MissingAwait
        bot.guilds.cache.forEach(async (guild) => {
            // check if the bot can fetch the guilds invites
            if (!guild.me.permissions.has("MANAGE_GUILD")) return;
            const fetchedInvites = await guild.invites.fetch()
            bot.invites.set(guild.id, new Map(fetchedInvites?.map(invite => [invite.code, invite.uses])))
        })

        // set permissions
        if (!bot.application?.owner) await bot.application?.fetch();
        const command = await bot.guilds.cache.get("531247629649182750")?.commands.fetch(json['devCommand'])
        await command.permissions.add(ownerPermissions())
    },
};

