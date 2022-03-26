var json = require('./config.json');
const {Pool} = require("pg");

const p = new Pool({
    user: json['user'],
    host: 'localhost',
    database: 'postgres',
    password: json['password'],
    port: 5432,
    connectionTimeoutMillis: 5000,
    max: 1000,
    idleTimeoutMillis: 30000,
})


p.on('error', async (err, client) => {
    await client.release()
    console.error('Unexpected error on idle client', err);
})

module.exports = {
    pool: p
}