// events.js
import * as tools from '../tools.js';

const eventHandlers = {};

export function on(event, handler) {
  if (!eventHandlers[event]) {
    eventHandlers[event] = [];
  }

  eventHandlers[event].push(handler);
}

export function handleEvent(event, payload) {
  const handlers = eventHandlers[event];
  if (handlers) {
    handlers.forEach(handler => handler(payload));
  } else {
    payload['ws'].send(tools.resp("ERROR", "Ивент не существует!"))
  }
}

