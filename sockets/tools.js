import * as crypto from 'crypto';
import * as config from './config.js';
import * as  https from  'https'

export function resp(event, data) {
	return JSON.stringify({event: event, data: data})
}

export function hashPassword(password) {
  // Создаем объект хеширования с использованием алгоритма SHA-256
  const sha256 = crypto.createHash('sha256');

  // Обновляем хеш объект с байтами пароля и соли
  sha256.update((password + config.salt).toString('utf-8'));

  // Получаем закодированный хеш в виде строки
  const hashedPassword = sha256.digest('hex');

  return hashedPassword;
}



export function performRequest(options, postData) {
	return new Promise((resolve, reject) => {
	  const req = https.request(options, res => {
		let data = '';
  
		res.on('data', chunk => {
		  data += chunk;
		});
  
		res.on('end', () => {
		  let responseData = data;
  
		  resolve(responseData);
		});
	  });
  
	  req.on('error', error => {
		reject(error);
	  });
  
	  if (postData) {
		req.write(postData);
	  }
  
	  req.end();
	});
  }
  