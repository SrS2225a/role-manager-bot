module.exports = {
    name: 'guildDelete',
    once: false,
    async execute(guild) {
        await guild.client.invites?.delete(guild.id)

        const channel = guild.client.channels.cache.get("844387430743801896")
        await channel.send(`Dionysus was removed from guild **${guild.name} (${guild.id})**. We now have ${guild.client.guilds.cache.size} guilds!`)
    }
}