export class DaisuPopRoom {
  constructor() {
    this.sockets = new Set();
    this.history = [];
    this.latest = null;
    this.diceCount = 2;
  }

  async fetch(request) {
    if (request.headers.get("Upgrade") !== "websocket") {
      return new Response("DaisuPop room expects WebSocket.", { status: 426 });
    }

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    this.connect(server);
    return new Response(null, { status: 101, webSocket: client });
  }

  connect(socket) {
    socket.accept();
    this.sockets.add(socket);

    this.send(socket, {
      type: "hello",
      diceCount: this.diceCount,
      latest: this.latest,
      history: this.history,
      players: this.sockets.size
    });
    this.broadcast({ type: "presence", players: this.sockets.size });

    socket.addEventListener("message", (message) => {
      try {
        const data = JSON.parse(message.data);
        if (data.type === "roll") {
          this.roll(data);
        }
      } catch {
        this.send(socket, { type: "error", message: "Bad pop." });
      }
    });

    const close = () => {
      this.sockets.delete(socket);
      this.broadcast({ type: "presence", players: this.sockets.size });
    };
    socket.addEventListener("close", close);
    socket.addEventListener("error", close);
  }

  roll(data) {
    const diceCount = clampDiceCount(data.diceCount);
    const values = Array.from({ length: diceCount }, () => secureDie(6));
    const total = values.reduce((sum, value) => sum + value, 0);
    const event = {
      id: crypto.randomUUID(),
      type: "roll",
      diceCount,
      values,
      total,
      roller: cleanName(data.roller),
      at: new Date().toISOString()
    };

    this.diceCount = diceCount;
    this.latest = event;
    this.history = [event, ...this.history].slice(0, 20);
    this.broadcast({
      ...event,
      history: this.history,
      players: this.sockets.size
    });
  }

  broadcast(payload) {
    for (const socket of this.sockets) {
      this.send(socket, payload);
    }
  }

  send(socket, payload) {
    try {
      socket.send(JSON.stringify(payload));
    } catch {
      this.sockets.delete(socket);
    }
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/ws") {
      const room = cleanRoom(url.searchParams.get("room"));
      const id = env.ROOM.idFromName(room);
      return env.ROOM.get(id).fetch(request);
    }

    return env.ASSETS.fetch(request);
  }
};

function clampDiceCount(value) {
  const number = Number(value);
  if (!Number.isInteger(number)) return 2;
  return Math.max(1, Math.min(6, number));
}

function secureDie(sides) {
  const range = 0x100000000;
  const max = Math.floor(range / sides) * sides;
  const buffer = new Uint32Array(1);
  let value;

  do {
    crypto.getRandomValues(buffer);
    value = buffer[0];
  } while (value >= max);

  return (value % sides) + 1;
}

function cleanRoom(room) {
  return String(room || "lobby").replace(/[^\w.-]/g, "").slice(0, 80) || "lobby";
}

function cleanName(name) {
  return String(name || "Popper").replace(/\s+/g, " ").trim().slice(0, 24) || "Popper";
}
