import * as Buffer from 'buffer'
import crypto from 'crypto'
import NodeRSA from 'node-rsa';


export class Crypt {
    static xor_cypher(message, key) {
        let result = '';
        for (let i = 0; i < message.length; i++) {
            result += String.fromCharCode(message.charCodeAt(i) ^ key.charCodeAt(i % key.length));
        }
        return result;
    }


    static d(encrypted_base64, key) {
        const encryptedMessage = Buffer.Buffer.from(encrypted_base64, 'base64').toString('utf-8');
        return Crypt.xor_cypher(encryptedMessage, key).substring(1);
    }
    static e(message, key) {
        const randomChar = crypto.randomBytes(1).toString('hex').slice(1);
        message = randomChar + message;
        const encryptedMessage = Crypt.xor_cypher(message, key);
        return Buffer.Buffer.from(encryptedMessage).toString('base64');
    }

}