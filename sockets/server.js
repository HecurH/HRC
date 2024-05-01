import * as WebSocket from 'ws';
const wss = new WebSocket.WebSocketServer({ port: 5000 });
import * as eventSystem from './events/eventSystem.js';
import * as events from './events/events.js';
import * as tools from './tools.js';


events.initEventHandlers();

function randomString(len, charSet) {
  charSet = charSet || 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;":,.<>/?';
  var randomString = '';
  for (var i = 0; i < len; i++) {
    var randomPoz = Math.floor(Math.random() * charSet.length);
    randomString += charSet.substring(randomPoz,randomPoz+1);
  }
  return randomString;
}

wss.on('connection', function connection(ws) {
  const key = randomString(16);
  ws.send(tools.resp("INFO", {message: "Подключен. Ожидаю запрос auth с рег. информацией",
                                        key: key}))
  ws.key = key
  ws.isAlive = true;
  ws.authorized = false;

  ws.on('error', console.error);
  ws.on('close', async function onClose() {
	if (ws.user) {
		ws.user.online(false);
		const friends = await ws.user.getFriends()
		if (friends) {
		  friends.forEach(function (entry) {
			const friend = Object.values(entry)[0]

			wss.clients.forEach((fws) => {
			  if (fws.user && fws.user.username === friend) {
				fws.send(tools.resp("OFFLINE", {
				  user: ws.user.username
				}));
				return;
			  }
			});

		  });
		};
	}
	
    
  });
  ws.on('pong', function heartbeat() {this.isAlive = true;});

  // прастите что я делаю костыль и не использую emit, просто питоновская шедевробибла их не поддерживает((
  ws.on('message', function message(data) {
    data = JSON.parse(data)
    const event = data["event"]
    data = data["data"]

    if (event && data){
      eventSystem.handleEvent(event, { data: data, ws: ws, wss: wss});
    } else {
      ws.send(tools.resp("ERROR", "event или data не указаны!"))
    }
    
  });

  setTimeout(function authCheck() {
    if (!ws.authorized){
      ws.close(1000, "Не авторизован.")
      ws.terminate();
    }
  }, 60000);
});


// Тут интервал на проверку alive'a
const interval = setInterval(function ping() {
  wss.clients.forEach(function each(ws) {
    if (ws.isAlive === false) {
      if (ws.user) ws.user.online(false);
      return ws.terminate();
    }

    ws.isAlive = false;
    ws.ping();
  });
}, 30000);

wss.on('close', function close() {
  clearInterval(interval);
  wss.clients.forEach(function each(ws) {
    if (ws.user) ws.user.online(false);
    
  });
});