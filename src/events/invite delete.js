module.exports = {
    name: 'inviteDelete',
    once: false,
    async execute(invite) {
        invite.client.invites.get(invite.guild.id)?.delete(invite.code);
    }
}