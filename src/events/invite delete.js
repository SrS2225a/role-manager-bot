module.exports = {
    name: 'inviteDelete',
    once: false,
    async execute(invite) {
        // Delete the invite from cache
        invite.client.invites.get(invite.guild.id).delete(invite.code);
    }
}