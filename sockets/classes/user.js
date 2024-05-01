import * as tools from '../tools.js';

export class User {
    constructor (username, db) {
        this.username = username;
        this.db = db;
    }

    async setValue(value, data) {
        await this.db.sql(`UPDATE users SET ${value} = $1  WHERE username = $2`, [data, this.username]);
    }


    async getValue(value) {
        let resp = await this.db.sql(`SELECT ${value} FROM users WHERE username = $1`, [this.username]);
        return resp ? resp[0][value] : undefined;
    }

    async checkPassword(password) {
        let dbpassword = await this.getValue('passhash');
        password = tools.hashPassword(password)

        return (dbpassword == password)
    }


    async verify() {
        await this.setValue('verified', true)
    }

    async online(val) {
        await this.setValue('online', val)
    }

    async isFriends(friend) {
        const res = await this.db.sql("SELECT 1 FROM friends WHERE (fuser = $1 AND suser = $2) OR (fuser = $3 AND suser = $4)", [this.username, friend, friend, this.username]);
        console.log(res)
        return res && (res[0]['?column?']) ? true : false;
    }

    async getFriends() {
        const res = await this.db.sql("SELECT suser FROM friends WHERE fuser = $1 UNION SELECT fuser FROM friends WHERE suser = $2", [this.username, this.username]);
        return res && res[0] ? res : undefined;
    }

    async sendFriendRequest(username, date) {
        const sql_query = "INSERT INTO friend_requests (sender, recipient, sended) VALUES ($1, $2, $3)"
        await this.db.sql(sql_query, [this.username, username, date]);
    }

    async isFRsended(username) {
        const res = await this.db.sql("SELECT 1 FROM friend_requests WHERE (sender = $1 AND recipient = $2) OR (sender = $3 AND recipient = $4)", [this.username, username, username, this.username]);
        return res && (res[0]['?column?']) ? true : false;
    }

    async isFRfromHim(username) {
        const res = await this.db.sql("SELECT 1 FROM friend_requests WHERE sender = $1 AND recipient = $2", [username, this.username]);
        console.log(res)
        return res && (res[0]['?column?']) ? true : false;
    }

    async deleteFRfromHim(username) {
        const res = await this.db.sql("DELETE FROM friend_requests WHERE sender = $1 AND recipient = $2", [username, this.username]);
    }

    async addFriend(username) {
        await this.db.sql("INSERT INTO friends (fuser, suser) VALUES ($1, $2)", [username, this.username]);
    }


    async sendMessage(recipient, sended, meEnc, friendEnc) {
        await this.db.sql("INSERT INTO messages (sender, recipient, senderEnc, recipientEnc, sended) VALUES ($1, $2, $3, $4, $5)", [this.username, recipient.username, meEnc, friendEnc, sended]);
    }

}

