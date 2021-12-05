const {SlashCommandBuilder} = require("@discordjs/builders");
const {userPermissions, clientPermissions} = require("../../structures/permissions");
module.exports = {
    data: new SlashCommandBuilder()
        .setName("role")
        .setDescription("Allows you to create, edit, or delete a role")
        .addSubcommand(option => option
            .setName("create")
            .setDescription("Creates a role"))
        .addSubcommand(option => option
            .setName("color")
            .setDescription("Edits the role with the specified color")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to edit")
                .setRequired(true))
            .addStringOption(option => option
                .setName("color")
                .setDescription("The color of the role to edit")
                .setRequired(true)))
        .addSubcommand(option => option
            .setName("delete")
            .setDescription("Deletes the specified role")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to delete")
                .setRequired(true)))
        .addSubcommand(option => option
            .setName("position")
            .setDescription("Edits a roles current position")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to edit")
                .setRequired(true))
            .addNumberOption(option => option
                .setName("position")
                .setDescription("The position of the role to edit")
                .setRequired(true)))
        .addSubcommand(option => option
            .setName("name")
            .setDescription("Edits a roles current name")
            .addRoleOption(option => option
                .setName("role")
                .setDescription("The role to edit")
                .setRequired(true))
            .addStringOption(option => option
                .setName("name")
                .setDescription("The name of the role to edit")
                .setRequired(true))),
    execute: async (message) => {
        userPermissions(message, "MANAGE_ROLES");
        clientPermissions(message, "MANAGE_ROLES");
        if(message.options.getSubcommand() === "create") {
            const role = await message.guild.roles.create({
                data: {
                    color: "#000000",
                    permissions: 0
                }
            });
            message.reply(`Created role ${role.name}`);
        } else if (message.options.getSubcommand() === "color") {
            const role = message.options.getRole("role");
            const color = message.options.getString("color").toUpperCase();
            await role.setColor(color);
            message.reply(`Edited role ${role.name}`);
        } else if (message.options.getSubcommand() === "delete") {
            const role = message.options.getRole("role");
            await role.delete();
            message.reply(`Deleted role ${role.name}`);
        }
        else if(message.options.getSubcommand() === "position") {
            const role = message.options.getRole("role");
            const position = message.options.getNumber("position");
            await role.setPosition(position);
            message.reply(`Edited role ${role.name}`);
        }
        else if(message.options.getSubcommand() === "name") {
            const role = message.options.getRole("role");
            const name = message.options.getString("name");
            await role.setName(name);
            message.reply(`Edited role ${role.name}`);
        }
    }
};