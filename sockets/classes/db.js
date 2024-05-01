import pkg from 'pg';
const { Pool } = pkg;
import { User } from './user.js';

export class DB {
	constructor (config) {
		this.pool = new Pool({
		  user: config.db['user'],
		  host: config.db['host'],
		  database: config.db['database'],
		  password: config.db['password'],
		  port: config.db['port'],
		});
	}

	async connect() {
		return;
		await this.client.connect(); 
	}


	async sql(q, params, callback) {
		const client = await this.pool.connect();
		let resp = await client.query(q, params, callback);
		client.release();
		console.log("Запрос в бд: " + q)
		return (resp && resp.rows && resp.rows[0]) ? resp.rows : undefined
	}


	async get_user(username) {
		const resp = await this.sql("SELECT username FROM users WHERE username = $1", [username]);
		return resp ? new User(resp[0]['username'], this) : undefined
	}
	


}