const {SlashCommandBuilder} = require("@discordjs/builders");
const {pool} = require("../../database");
const {clientPermissions, userPermissions} = require("../../structures/permissions");

async function resolveMember(member, message) {
    async function resolveById(member, message) {
        const memberId = member.replace(/[<@!>]/g, "");
        const memberObj = message.members.cache.get(memberId);
        if (memberObj) return memberObj;
        const memberObj2 = message.members.cache.find(m => m.user.id === memberId);
        if (memberObj2) return memberObj2;
    }

    async function resolveByQuery(member, message) {
        const query = member.length > 5 && member.at(-5) === '#' ? member.slice(0, -5) : member
        const members = await message.members.fetch({query: query})
        return members.first()
    }

    const mem = (await resolveById(member, message)) ?? (await resolveByQuery(member, message))
    if (mem) {return mem} else {(() => {throw {identifier: "ArgumentMemberError", message: `I could not resolve that current member from the string!`}})()}
    
}
module.exports = {
    data: new SlashCommandBuilder()
        .setName("giverole")
        .setDescription("Allows you to add or remove a role from a member; members, bots, or everyone")
        .addSubcommand(subcommand => subcommand
            .setName("add")
            .setDescription("Adds a role to a member; members, bots, or everyone")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to add")
                .setRequired(true))
            .addStringOption(option => option
                .setName("member")
                .setDescription("The member to add the role to")
                .setRequired(true)))
        .addSubcommand(subcommand => subcommand
            .setName("remove")
            .setDescription("Removes a role to a member; members, bots, or everyone")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to remove")
                .setRequired(true))
            .addStringOption(option => option
                .setName("member")
                .setDescription("The member to add the role to")
                .setRequired(true))),
    async execute(message) {
        const db = await pool.connect()
        userPermissions(message, ["MANAGE_ROLES"]);
        clientPermissions(message, ["MANAGE_ROLES"])
        if (message.options.getSubcommand() === "add") {
            const role = message.options.getRole("role")
            const to = message.options.getString("member")
            await message.reply(`Changing role ${role.name} for ${to}`)
            if(to === "everyone".toLowerCase()) {
                await message.guild.members.cache.forEach((member) => member.roles.add(role))
            } else if (to === 'bots'.toLowerCase()) {
                await message.guild.members.cache.filter((member) => member.user.bot).forEach((member) => member.roles.add(role))
            } else if (to === 'members'.toLowerCase()) {
                await message.guild.members.cache.filter((member) => !member.user.bot).forEach((member) => member.roles.add(role))
            } else {
                const member = await resolveMember(to, message.guild)
                if (member) {
                    await member.roles.add(role)
                }
            }
            await message.editReply(`Successfully added role ${role.name} for ${to}`)
        } else if (message.options.getSubcommand() === "remove") {
            const role = message.options.getRole("role")
            const to = message.options.getString("member")
            await message.reply(`Changing ${role.name} for ${to}`)
            if(to === "everyone".toLowerCase()) {
                await message.guild.members.cache.forEach((member) => member.roles.remove(role))
            } else if (to === 'bots'.toLowerCase()) {
                await message.guild.members.cache.filter((member) => member.user.bot).forEach((member) => member.roles.remove(role))
            } else if (to === 'members'.toLowerCase()) {
                await message.guild.members.cache.filter((member) => !member.user.bot).forEach((member) => member.roles.remove(role))
            } else {
                const member = await resolveMember(to, message.guild)
                if (member) {
                    await member.roles.remove(role)
                }
            }
            await message.editReply({content: `Successfully removed role ${role.name} for ${to}`})
        }
        await db.release()
    }
}