import { DiscordSDK } from "@discord/embedded-app-sdk";
import "./styles.css";

const state = {
  diceCount: 2,
  rolling: false,
  socket: null,
  room: "lobby",
  roller: localName(),
  history: [],
  latest: null,
  players: 1
};

document.querySelector("#app").innerHTML = `
  <main class="app">
    <section class="machine">
      <header>
        <div>
          <h1>DaisuPop</h1>
          <p id="room">room: lobby</p>
        </div>
        <div class="pill"><b id="players">1</b><span>online</span></div>
      </header>

      <button id="pop" class="popper" type="button" aria-label="Pop dice">
        <span class="glass">
          <span id="dice" class="dice"></span>
        </span>
        <span class="stem"></span>
      </button>

      <div class="counts" aria-label="Dice count">
        ${[1, 2, 3, 4, 5, 6].map((n) => `<button type="button" data-count="${n}">${n}</button>`).join("")}
      </div>

      <div class="read">
        <strong id="total">READY</strong>
        <span id="meta">Pick dice. Pop dice. That is game.</span>
      </div>
    </section>

    <aside>
      <h2>Session</h2>
      <ol id="log"><li>No rolls yet.</li></ol>
    </aside>
  </main>
`;

const el = {
  pop: document.querySelector("#pop"),
  dice: document.querySelector("#dice"),
  total: document.querySelector("#total"),
  meta: document.querySelector("#meta"),
  log: document.querySelector("#log"),
  room: document.querySelector("#room"),
  players: document.querySelector("#players"),
  counts: [...document.querySelectorAll("[data-count]")]
};

start();

async function start() {
  drawDice([1, 2]);
  bind();
  await setupDiscord();
  connect();
  render();
}

function bind() {
  el.pop.addEventListener("click", pop);
  for (const button of el.counts) {
    button.addEventListener("click", () => {
      state.diceCount = Number(button.dataset.count);
      clickSound();
      render();
    });
  }
}

async function setupDiscord() {
  const clientId = import.meta.env.VITE_DISCORD_CLIENT_ID;
  const params = new URLSearchParams(location.search);
  state.room = params.get("instance_id") || params.get("frame_id") || params.get("room") || "lobby";

  if (!clientId) return;

  try {
    const discord = new DiscordSDK(clientId);
    await discord.ready();
    state.room = discord.instanceId || state.room;
  } catch {
    state.room = params.get("room") || state.room;
  }
}

function connect() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  state.socket = new WebSocket(`${protocol}//${location.host}/ws?room=${encodeURIComponent(state.room)}`);

  state.socket.addEventListener("message", (message) => {
    const data = JSON.parse(message.data);
    if (data.type === "hello") {
      state.diceCount = data.diceCount || 2;
      state.latest = data.latest;
      state.history = data.history || [];
      state.players = data.players || 1;
      if (state.latest) drawDice(state.latest.values);
      render();
    }
    if (data.type === "presence") {
      state.players = data.players || 1;
      render();
    }
    if (data.type === "roll") {
      state.latest = data;
      state.history = data.history || [data, ...state.history].slice(0, 20);
      state.players = data.players || state.players;
      animateRoll(data.values);
    }
  });

  state.socket.addEventListener("close", () => {
    el.meta.textContent = "Disconnected. Refresh to rejoin.";
  });
}

function pop() {
  if (state.rolling || state.socket?.readyState !== WebSocket.OPEN) return;
  state.rolling = true;
  el.pop.classList.add("rolling");
  rattleSound();
  drawDice(randomFakeDice(state.diceCount));
  state.socket.send(JSON.stringify({
    type: "roll",
    diceCount: state.diceCount,
    roller: state.roller
  }));
}

function animateRoll(values) {
  let frame = 0;
  const timer = setInterval(() => {
    frame += 1;
    drawDice(frame < 8 ? randomFakeDice(values.length) : values);

    if (frame >= 8) {
      clearInterval(timer);
      state.rolling = false;
      el.pop.classList.remove("rolling");
      settleSound();
      render();
    }
  }, 60);
}

function render() {
  el.room.textContent = `room: ${state.room}`;
  el.players.textContent = String(Math.max(1, state.players));
  for (const button of el.counts) {
    button.classList.toggle("on", Number(button.dataset.count) === state.diceCount);
  }

  if (state.latest) {
    el.total.textContent = String(state.latest.total);
    el.meta.textContent = `${state.latest.roller} popped ${state.latest.values.join(" + ")}`;
  } else {
    el.total.textContent = "READY";
    el.meta.textContent = `${state.diceCount} ${state.diceCount === 1 ? "die" : "dice"} loaded.`;
  }

  el.log.innerHTML = state.history.length
    ? state.history.map((roll) => `<li><span>${roll.roller}</span><code>${roll.values.join(" ")}</code><b>${roll.total}</b></li>`).join("")
    : "<li>No rolls yet.</li>";
}

function drawDice(values) {
  el.dice.innerHTML = values.map((value) => `<span class="die">${pips(value)}</span>`).join("");
}

function pips(value) {
  const on = {
    1: [5],
    2: [1, 9],
    3: [1, 5, 9],
    4: [1, 3, 7, 9],
    5: [1, 3, 5, 7, 9],
    6: [1, 3, 4, 6, 7, 9]
  }[value];
  return Array.from({ length: 9 }, (_, i) => `<i class="${on.includes(i + 1) ? "on" : ""}"></i>`).join("");
}

function randomFakeDice(count) {
  return Array.from({ length: count }, () => Math.floor(Math.random() * 6) + 1);
}

function localName() {
  const saved = localStorage.getItem("daisupop.name");
  if (saved) return saved;
  const name = `Popper ${Math.floor(100 + Math.random() * 900)}`;
  localStorage.setItem("daisupop.name", name);
  return name;
}

function audio() {
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!window.daisuAudio && Ctx) window.daisuAudio = new Ctx();
  return window.daisuAudio;
}

function beep(freq, duration, type = "sine", gainValue = 0.05) {
  const ctx = audio();
  if (!ctx) return;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.value = gainValue;
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
  osc.connect(gain).connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + duration);
}

function clickSound() {
  beep(220, 0.035, "square", 0.04);
}

function rattleSound() {
  for (let i = 0; i < 12; i += 1) {
    setTimeout(() => beep(80 + Math.random() * 140, 0.025, "sawtooth", 0.035), i * 22);
  }
}

function settleSound() {
  beep(120, 0.07, "triangle", 0.06);
}
