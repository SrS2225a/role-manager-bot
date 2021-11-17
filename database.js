var json = require('./config.json');
const {Pool} = require("pg").native;

// pg.types.setTypeParser(20, (value) => {return parseInt(value)})
const p = new Pool({
    user: json['user'],
    host: 'localhost',
    database: 'postgres',
    password: json['password'],
    port: 5432
})

module.exports = {
    pool: p
}