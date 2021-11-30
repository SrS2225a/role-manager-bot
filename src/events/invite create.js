module.exports = {
    name: 'inviteCreate',
    once: false,
    async execute(invite) {
        // Update cache on new invites
        invite.client.invites?.get(invite.guild.id)?.set(invite.code, invite.uses);
    }
}