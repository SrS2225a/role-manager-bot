module.exports = {
    name: 'inviteCreate',
    once: false,
    async execute(invite) {
        invite.client.invites?.get(invite.guild.id)?.set(invite.code, invite.uses);
    }
}