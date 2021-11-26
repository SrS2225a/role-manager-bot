const {Permissions} = require("discord.js")
function userPermissions(message, permission) {
    if (message.user.id === '270848136006729728' || '508455796783317002' || '222492698236420099') {
        return true
    } else {
        var _a;
        var required = (_a = permission) !== null && _a !== void 0 ? _a : new Permissions();
        const permissions = message.channel.permissionsFor(message.user);
        if (!permissions) {
            return (() => {
                throw {
                    identifier: "ClientPermissionsNoPermissions",
                    message: "I was unable to resolve the end-user's permissions in the command invocation channel!"
                }
            })()
        }
        const missing = permissions.missing(required)
        return missing.length === 0 ? true : (() => {
            throw {
                identifier: "MissingUserPermissions",
                message: `You are missing the following permission(s) to run this command: ${permission.join(', ')}`
            }
        })()
    }
}

function rolePermissions(message, role) {
    if (message.user.id === '270848136006729728' || '508455796783317002' || '222492698236420099') {
        return true
    } else {
        return message.member.roles.cache.has(role) ? true : (() => {
            throw {
                identifier: "MissingRolePermissions",
                message: `You are missing the following roles(s) to run this command: ${message.guild.roles.cache.get(role).name}`
            }
        })()
    }
}

function clientPermissions(message, permission) {
    var _a;
    var required = (_a = permission) !== null && _a !== void 0 ? _a : new Permissions();
    const permissions = message.channel.permissionsFor(message.client.id)
    if (!permissions) {
        return (() => {
            throw {
                identifier: "ClientPermissionsNoPermissions",
                message: "I was unable to resolve my permissions in the command invocation channel!"
            }
        })()
    }
    const missing = permissions.missing(required)
    return missing.length === 0 ? true : (() => {
        throw {
            identifier: "MissingClientPermissions",
            message: `I am missing the following permission(s) to run this command: ${permission.join(', ')}`
        }
    })()
}

function ownerPermissions() {
    const permissions = [
        {
            id: '270848136006729728',
            type: 'USER',
            permission: true
        }, {
            id: '508455796783317002',
            type: 'USER',
            permission: true
        }, {
            id: "222492698236420099",
            type: "USER",
            permission: true
        }
    ]
    return {permissions}
}

module.exports = {userPermissions, rolePermissions, clientPermissions, ownerPermissions}