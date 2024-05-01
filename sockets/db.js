import { DB } from './classes/db.js';
import * as config from './config.js';


export const db = new DB(config)
await db.connect()

 

