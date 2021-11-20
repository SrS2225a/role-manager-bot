var json = require('./config.json');
const {Pool} = require("pg").native;

// pg.types.setTypeParser(20, (value) => {return parseInt(value)})
const p = new Pool({
    user: json['user'],
    host: 'localhost',
    database: 'postgres',
    password: json['password'],
    port: 5432,
    connectionTimeoutMillis: 5000,
    max: 1000
})

// automatically release the pool if it has been active for more than 10 seconds
p.on('error', async (err, client) => {
    await client.release()
    console.error('Unexpected error on idle client', err);
})

// automatically release the pool if it has been active for more than 10 seconds

module.exports = {
    pool: p
}