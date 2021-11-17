module.exports = {
    name: 'inviteDelete',
    once: false,
    async execute(invite) {
        // Delete the invite from cache
        console.log(`Deleting invite ${invite.code}`);
        invite.client.invites.get(invite.guild.id).delete(invite.code);
    }
}