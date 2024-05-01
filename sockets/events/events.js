import * as eventSystem from './eventSystem.js';
import * as tools from '../tools.js';
import { db } from '../db.js'
import * as querystring from 'querystring';
import * as config from '../config.js';
import {Crypt} from "../classes/crypt.js";





export function initEventHandlers() {
  eventSystem.on('auth', async ({ data, ws, wss }) => {
    if (ws.authorized) {
      ws.send(tools.resp("ERROR", "Вы уже авторизованы!")); return;
    }
    if (!data || !ws) {
      ws.send(tools.resp("ERROR", "data не указана!")); return;
    }

    let {username, password} = data;
    ({username, password} = {username: Crypt.d(username, ws.key), password: Crypt.d(password, ws.key)});

    if (!username || !password) {
      ws.send(tools.resp("ERROR", "Не указан логин или пароль.")); return;
    }

    const user = await db.get_user(username);

    if (!user) {
      ws.send(tools.resp("ERROR", "Пользователь не найден!")); return;
    }

    if (await user.checkPassword(password)) {
      ws.authorized = true;
      ws.user = user;
      await user.verify()
      await user.online(true)

      let friends = await user.getFriends()
      if (friends){
        friends.forEach(function(entry) {
          const friend = Object.values(entry)[0]

          wss.clients.forEach((fws) => {
            if (fws.user && fws.user.username === friend) {
              fws.send(tools.resp("ONLINE", {
                user: user.username
              }));
            }
          });

      });
      }
      
      ws.send(tools.resp("INFO", {message: "Успешный вход!"}));
    } else {
      ws.send(tools.resp("ERROR", "Неверный пароль!"));
    }
  });


  eventSystem.on('MESSAGE', async ({ data, ws, wss }) => {
    if (!ws.authorized) return ws.send(tools.resp("ERROR", "Вы не авторизованы!"));
    if (!data || !ws) return ws.send(tools.resp("ERROR", "data не указана!"));


    let { recipient, message } = data;
    if (!recipient || !message) return ws.send(tools.resp("ERROR", "Получатель или сообщение не указано!"));

    if (message.length > 4096) return ws.send(tools.resp("ERROR", "Ваше сообщение слишком длинное!"));

    let dmessage = Crypt.d(message, ws.key)
    if (dmessage.length > 1024) return ws.send(tools.resp("ERROR", "Ваше сообщение слишком длинное!"));


    const friend = await db.get_user(recipient);
    if (!friend) return ws.send(tools.resp("ERROR", "Получатель не существует!"));


    if (!await ws.user.isFriends(friend.username)) return ws.send(tools.resp("ERROR", "Вы не друзья!"));


    const mePubkey = await ws.user.getValue('pubkey');

    const options = {
      hostname: config.host,
      path: '/api/encrypt',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const encryptMessage = async (pubkey, data) => {
	  let postdata = {
	    "pubkey": pubkey,
	    "data": data
	  };
      const resp = await tools.performRequest(options, JSON.stringify(postdata));
      if (!resp) return ws.send(tools.resp("ERROR", "Не удалось зашифровать!"));

      return resp.substring(1, resp.length-1);
    };

    const meEnc = await encryptMessage(mePubkey, dmessage);


    const friendPubkey = await friend.getValue('pubkey');
    const friendEnc = await encryptMessage(friendPubkey, dmessage);

    const currentDate = new Date();
    await ws.user.sendMessage(friend, currentDate, meEnc, friendEnc);

    wss.clients.forEach((fws) => {
      if (fws.user && fws.user.username === friend.username) {
        fws.send(tools.resp("MESSAGE", {
          sender: ws.user.username,
          recipient: friend.username,
          message: Crypt.e(friendEnc, fws.key),
          sended: currentDate
        }));

      }
    });

    ws.send(tools.resp("MESSAGE", {
      sender: ws.user.username,
      recipient: friend.username,
      message: Crypt.e(meEnc, ws.key),
      sended: currentDate
    }));
  });



  eventSystem.on('FRIEND_REQUEST', async ({ data, ws, wss }) => {
    if (!ws.authorized) {
      return ws.send(tools.resp("ERROR", "Вы не авторизованы!"));
    }
    if (!data || !ws) {
      return ws.send(tools.resp("ERROR", "data не указана!"));
    }

    const { username } = data;
    if (!username) {
      return ws.send(tools.resp("ERROR", "Имя пользователя не указано!"));
    }

    if (ws.user.username === username) {
      return ws.send(tools.resp("ERROR", "Самому себе послать запрос нельзя!"));
    }

    const friend = await db.get_user(username);
    if (!friend) {
      return ws.send(tools.resp("ERROR", "Пользователь не существует!"));
    }

    if (await ws.user.isFriends(friend.username)) {
      return ws.send(tools.resp("ERROR", "Вы уже друзья!"));
    }
    if (await ws.user.isFRsended(friend.username)) {
      ws.send(tools.resp("ERROR", "Запрос уже отправлен!"));
      return;
    }


    const currentDate = new Date();

    await ws.user.sendFriendRequest(friend.username, currentDate)

    wss.clients.forEach((fws) => {
      if (fws.user && fws.user.username === friend.username) {
        fws.send(tools.resp("FRIEND_REQUEST", {
          sender: ws.user.username,
          sended: currentDate
        }));

      }
    });

    ws.send(tools.resp("INFO", "Запрос в друзья был отправлен!"));
  });



  eventSystem.on('ACCEPT_FR', async ({ data, ws, wss }) => {
    if (!ws.authorized) {
      return ws.send(tools.resp("ERROR", "Вы не авторизованы!"));
    }
    if (!data || !ws) {
      return ws.send(tools.resp("ERROR", "data не указана!"));
    }

    const {username} = data;
    if (!username) {
      return ws.send(tools.resp("ERROR", "Имя пользователя не указано!"));
    }

    const friend = await db.get_user(username);
    if (!friend) {
      return ws.send(tools.resp("ERROR", "Пользователь не существует!"));
    }

    if (!await ws.user.isFRfromHim(username)) {
      return ws.send(tools.resp("ERROR", "Пользователь не посылал вам запросов!"));
    }

    await ws.user.deleteFRfromHim(username);
    await ws.user.addFriend(username);

    wss.clients.forEach((fws) => {
      if (fws.user && fws.user.username === username) {
        fws.send(tools.resp("ACCEPT_FR", {
          friend: ws.user.username
        }));

      }
    });
    return ws.send(tools.resp("ACCEPT_FR", "Вы приняли запрос!"));


  })
}