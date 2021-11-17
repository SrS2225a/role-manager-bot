module.exports = {
    name: 'guildCreate',
    once: false,
    async execute(guild) {
        await guild.invites.fetch().then(invites => {
            guild.client.invites.set(guild.id, new Map(invites.map(invite => [invite.code, invite.uses])))
        })

        const channel = guild.channels.cache.get('844387430743801896')
        await channel.send(`Dionysus was added into guild **${guild.name} (${guild.id})**. We now have ${guild.client.guilds.cache.size} guilds!`)
    }
}