const {Permissions} = require("discord.js")
function userPermissions(message, permission) {
    if (message.user.id === '270848136006729728' || message.user.id === '508455796783317002' || message.user.id === '222492698236420099') {
        return true
    } else {
        const permissions = message.channel.permissionsFor(message.user);
        if (!permissions) {
            return (() => {
                throw {
                    identifier: "ClientPermissionsNoPermissions",
                    message: "I was unable to resolve the end-user's permissions in the command invocation channel!"
                }
            })()
        }
        const missing = permissions.missing(permission)
        console.log(missing)
        return missing.length === 0 ? true : (() => {
            throw {
                identifier: "MissingUserPermissions",
                message: `You are missing the following permission(s) to run this command: ${missing.join(', ')}`
            }
        })()
    }
}

function rolePermissions(message, role) {
    if (message.user.id === '270848136006729728' || message.user.id === '508455796783317002' || message.user.id === '222492698236420099') {
        return true
    } else {
        return message.member.roles.cache.has(role) ? true : (() => {
            throw {
                identifier: "MissingRolePermissions",
                message: `You are missing the following roles(s) to run this command: ${message.guild.roles.cache.get(role)?.name}`
            }
        })()
    }
}

function clientPermissions(message, permission) {
    const required = new Permissions(permission);
    const permissions = message.channel.permissionsFor(message.client.user.id)
    if (!permissions) {
        return (() => {
            throw {
                identifier: "ClientPermissionsNoPermissions",
                message: "I was unable to resolve my permissions in the command invocation channel!"
            }
        })()
    }
    const missing = permissions.missing(required.bitfield)
    return missing.length === 0 ? true : (() => {
        throw {
            identifier: "MissingClientPermissions",
            message: `I am missing the following permission(s) to run this command: ${missing.join(', ')}`
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