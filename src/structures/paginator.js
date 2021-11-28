const {MessageActionRow, MessageButton, Formatters, MessageEmbed} = require("discord.js");
var AsciiTable = require('ascii-table')
class paginator {
    constructor(context, entries) {
        this.bot = context.client.bot
        this.message = context
        this.author = context.user
        this.channel = context.channel
        this.entries = entries;
        this.per_page = 20
        this.lang = ''
        let pages = Math.floor(this.entries.length / this.per_page)
        let left_over = this.entries.length % this.per_page
        if (left_over) (pages += 1)
        this.maxium_pages = pages
        this.content = ''
        this.embed = new MessageEmbed().setColor('RANDOM')
        this.paginating = entries.length > this.per_page
        this.show_entry_count = true
        this.show_points = false
        this.show_embed = true
        this.title = undefined
        // show_embed=true, show_points=false, show_entry_count=true, per_page=20
    }

    #get_page(page) {
        const base = (page - 1) * this.per_page
        return this.entries.slice(base, base + this.per_page)
    }

    #prepare_embed(entries, page) {
        let p = []
        if (this.show_points) {
            let index = 1 + ((page - 1) * this.per_page)
            for (const entry of entries) {
                p.push(`${index}. ${entry}`)
                index += 1
            }
        } else {
            for (const entry of entries) {
                p.push(entry)
            }
        }
        if(this.title) (this.embed.setTitle(this.title))
        if (this.maxium_pages > 1) {
            if (this.show_entry_count) {
                const text = `Page ${page}/${this.maxium_pages} | Total Entries: ${this.entries.length}`
                this.embed.setFooter(text)
            } else {
                const text = `Page ${page}/${this.maxium_pages}`
                this.embed.setFooter(text)
            }
        }
        this.embed.setDescription(Formatters.codeBlock(this.lang, p.join('\n')))
    }

    #prepare_message(entries, page) {
        let p = []
        if (this.show_points) {
            let index = 1 + ((page - 1) * this.per_page)
            for (const entry of entries) {
                p.push(`${index}. ${entry}`)
                index += 1
            }
        } else {
            for (const entry of entries) {
                p.push(entry)
            }
        }
        let text
        if (this.show_entry_count) {
            text = `Page ${page}/${this.maxium_pages} | Total Entries: ${this.entries.length}`
        } else {
            text = `Page ${page}/${this.maxium_pages}`
        }
        this.content = Formatters.codeBlock(p.join('\n')) + '\n' + text
    }

    async #show_page(page, interaction) {
        this.current_page = page
        const components = this.#getButtons(page)
        const entries = this.#get_page(page)
        if (this.show_embed) {
            this.#prepare_embed(entries, page)
            if (interaction) {
                await this.message.editReply({embeds: [this.embed], components: [components]})
            } else {
                if (this.maxium_pages > 1) {
                    await this.message.reply({embeds: [this.embed], components: [components]})
                } else {
                    await this.message.reply({embeds: [this.embed]})
                }
            }
        } else {
            this.#prepare_message(entries, page)
            if (interaction) {
                await this.message.editReply({content: this.content, components: [components]})
            } else {
                if (this.maxium_pages > 1) {
                    await this.message.reply({content: this.content, components: [components]})
                } else {
                    await this.message.reply({content: this.content})
                }
            }
        }
    }

    #getButtons(page) {
        let disableButtons = [false, false]
        if (page === this.maxium_pages) {
            disableButtons = [false, true]
        } else if (page === 1) {
            disableButtons = [true, false]
        }
        if (this.maxium_pages === 2) {
            return new MessageActionRow()
                .addComponents(
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('back')
                        .setEmoji('◀')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setCustomId('stop')
                        .setEmoji('⏹')
                        .setStyle('DANGER'),
                    new MessageButton()
                        .setDisabled(disableButtons[1])
                        .setCustomId('next')
                        .setEmoji('▶')
                        .setStyle('PRIMARY')
                )
        } else {
            return new MessageActionRow()
                .addComponents(
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('firstPage')
                        .setEmoji('⏪')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('back')
                        .setEmoji('◀')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setCustomId('stop')
                        .setEmoji('⏹')
                        .setStyle('DANGER'),
                    new MessageButton()
                        .setCustomId('next')
                        .setEmoji('▶')
                        .setStyle('PRIMARY')
                        .setDisabled(disableButtons[1]),
                    new MessageButton()
                        .setCustomId('lastPage')
                        .setEmoji('⏩')
                        .setStyle('PRIMARY')
                        .setDisabled(disableButtons[1]),
                )
        }
    }

    async paginate() {
        const first_page = await this.#show_page(1, null)
        if (!first_page) {
            await first_page
        }
        const filter = i => i.user.id === this.author.id
        const collector = this.channel.createMessageComponentCollector({filter, time: 60000})
        collector.on('collect', async i => {
            if (i.customId === 'firstPage') {
                await this.#show_page(1, i)
            } else if (i.customId === 'back') {
                await this.#show_page(this.current_page - 1, i)
            } else if (i.customId === 'stop') {
                await this.message.deleteReply()
                this.paginating = false
            } else if (i.customId === 'next') {
                await this.#show_page(this.current_page + 1, i)
            } else if (i.customId === 'lastPage') {
                await this.#show_page(this.maxium_pages, i)
            }
            await i.deferUpdate();
        })
        collector.on('end', async i => {
            this.paginating = false
        })
    }
}

class PaginatorAsTable {
    constructor(context, entries) {
        this.bot = context.client.bot
        this.message = context
        this.author = context.user
        this.channel = context.channel
        this.entries = entries;
        this.per_page = 20
        let pages = Math.floor(this.entries.length / this.per_page)
        let left_over = this.entries.length % this.per_page
        if (left_over) (pages += 1)
        this.maxium_pages = pages
        this.embed = new MessageEmbed().setColor('RANDOM')
        this.paginating = entries.length > this.per_page
        this.show_entry_count = true
        this.heading = []
        this.title = undefined
    }

    #get_page(page) {
        const base = (page - 1) * this.per_page
        return this.entries.slice(base, base + this.per_page)
    }

    #prepare_table(entries, page) {
        const table = new AsciiTable()
            .setHeading(this.heading)
            .addRowMatrix(entries)
            .setBorder('|', '-')
        table.__border = false
        if(this.title) (this.embed.setTitle(this.title))
        if (this.show_entry_count) {
            const text = `Page ${page}/${this.maxium_pages} | Total Entries: ${this.entries.length}`
            this.embed.setFooter(text)
        } else {
            const text = `Page ${page}/${this.maxium_pages}`
            this.embed.setFooter(text)
        }
        this.embed.setDescription(Formatters.codeBlock(table.toString()))
    }

    async #show_page(page, interaction) {
        this.current_page = page
        const components = this.#getButtons(page)
        const entries = this.#get_page(page)
        this.#prepare_table(entries, page)
        if (interaction) {
            await this.message.editReply({embeds: [this.embed], components: [components]})
        } else {
            if (this.maxium_pages > 1) {
                await this.message.reply({embeds: [this.embed], components: [components]})
            } else {
                await this.message.reply({embeds: [this.embed]})
            }
        }
    }

    #getButtons(page) {
        let disableButtons = [false, false]
        if (page === this.maxium_pages) {
            disableButtons = [false, true]
        } else if (page === 1) {
            disableButtons = [true, false]
        }
        if (this.maxium_pages === 2) {
            return new MessageActionRow()
                .addComponents(
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('back')
                        .setEmoji('◀')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setCustomId('stop')
                        .setEmoji('⏹')
                        .setStyle('DANGER'),
                    new MessageButton()
                        .setDisabled(disableButtons[1])
                        .setCustomId('next')
                        .setEmoji('▶')
                        .setStyle('PRIMARY')
                )
        } else {
            return new MessageActionRow()
                .addComponents(
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('firstPage')
                        .setEmoji('⏪')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('back')
                        .setEmoji('◀')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setCustomId('stop')
                        .setEmoji('⏹')
                        .setStyle('DANGER'),
                    new MessageButton()
                        .setCustomId('next')
                        .setEmoji('▶')
                        .setStyle('PRIMARY')
                        .setDisabled(disableButtons[1]),
                    new MessageButton()
                        .setCustomId('lastPage')
                        .setEmoji('⏩')
                        .setStyle('PRIMARY')
                        .setDisabled(disableButtons[1]),
                )
        }
    }

    async paginate() {
        const first_page = await this.#show_page(1, null)
        if (!first_page) {
            await first_page
        }
        const filter = i => i.user.id === this.author.id
        const collector = this.channel.createMessageComponentCollector({filter, time: 128000})
        collector.on('collect', async i => {
            if (i.customId === 'firstPage') {
                await this.#show_page(1, i)
            } else if (i.customId === 'back') {
                await this.#show_page(this.current_page - 1, i)
            } else if (i.customId === 'stop') {
                await i.message.delete()
                this.paginating = false
            } else if (i.customId === 'next') {
                await this.#show_page(this.current_page + 1, i)
            } else if (i.customId === 'lastPage') {
                await this.#show_page(this.maxium_pages, i)
            }
            await i.deferUpdate();
        })
        collector.on('end', async i => {
            this.paginating = false
        })
    }
}


class PaginateWhileRunning {
    constructor(message) {
        this.message = message
        this.collect = true
        this.lang = ''
        this.channel = message.channel
        this.per_page = 20
        this.author = message.user
        this.show_entry_count = true
        this.entries = []
    }

    async paginate(entries) {
        // add array of entries
        this.entries = this.entries.concat(entries.split(/\r?\n/))
        this.maxium_pages = Math.ceil(this.entries.length / this.per_page)
        let pages = Math.floor(this.entries.length / this.per_page)
        let left_over = this.entries.length % this.per_page
        if (left_over) (pages += 1)
        this.maxium_pages = pages
        const first_page = await this.show_page(pages, null)
        if (!first_page) {
            await first_page
        }
    }

    get_page(page) {
        const base = (page - 1) * this.per_page
        return this.entries.slice(base, base + this.per_page)
    }

    getButtons(page) {
        let disableButtons = [false, false]
        if (page === this.maxium_pages) {
            disableButtons = [false, true]
        } else if (page === 1) {
            disableButtons = [true, false]
        }
        if (this.maxium_pages === 2) {
            return new MessageActionRow()
                .addComponents(
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('back')
                        .setEmoji('◀')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setCustomId('stop')
                        .setEmoji('⏹')
                        .setStyle('DANGER'),
                    new MessageButton()
                        .setDisabled(disableButtons[1])
                        .setCustomId('next')
                        .setEmoji('▶')
                        .setStyle('PRIMARY')
                )
        } else {
            return new MessageActionRow()
                .addComponents(
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('firstPage')
                        .setEmoji('⏪')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setDisabled(disableButtons[0])
                        .setCustomId('back')
                        .setEmoji('◀')
                        .setStyle('PRIMARY'),
                    new MessageButton()
                        .setCustomId('stop')
                        .setEmoji('⏹')
                        .setStyle('DANGER'),
                    new MessageButton()
                        .setCustomId('next')
                        .setEmoji('▶')
                        .setStyle('PRIMARY')
                        .setDisabled(disableButtons[1]),
                    new MessageButton()
                        .setCustomId('lastPage')
                        .setEmoji('⏩')
                        .setStyle('PRIMARY')
                        .setDisabled(disableButtons[1]),
                )
        }
    }

    prepare_message(entries, page) {
        let p = []
        if (this.show_points) {
            let index = 1 + ((page - 1) * this.per_page)
            for (const entry of entries) {
                p.push(`${index}. ${entry}`)
                index += 1
            }
        } else {
            for (const entry of entries) {
                p.push(entry)
            }
        }
        let text
        if (this.show_entry_count) {
            text = `Page ${page}/${this.maxium_pages} | Total Entries: ${this.entries.length}`
        } else {
            text = `Page ${page}/${this.maxium_pages}`
        }
        this.content = Formatters.codeBlock(this.lang, p.join('\n')) + '\n' + text
    }

    async show_page(page, interaction) {
        this.current_page = page
        const components = this.getButtons(page)
        const entries = this.get_page(page)
        this.prepare_message(entries, page)
        if (interaction) {
            await this.message.editReply({content: this.content, components: [components]})
        } else {
            if (this.maxium_pages > 1) {
                await this.message.editReply({content: this.content, components: [components]})
                if (this.collect) {
                    await this.collector()
                }
            } else {
                await this.message.editReply({content: this.content})
            }
        }
    }

    async collector() {
        this.collect = false
        const filter = i => i.user.id === this.author.id
        const collector = this.channel.createMessageComponentCollector({filter, time: 128000})
        collector.on('collect', async i => {
            if (i.customId === 'firstPage') {
                await this.show_page(1, i)
            } else if (i.customId === 'back') {
                await this.show_page(this.current_page - 1, i)
            } else if (i.customId === 'stop') {
                await i.message.delete()
            } else if (i.customId === 'next') {
                await this.show_page(this.current_page + 1, i)
            } else if (i.customId === 'lastPage') {
                await this.show_page(this.maxium_pages, i)
            }
            await i.deferUpdate();
        })
        collector.on('end', async i => {
            this.paginating = false
        })
    }
}

module.exports = {paginator, PaginatorAsTable, PaginateWhileRunning}