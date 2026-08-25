/* ============================================================
   RemapWrap - audio
   F-Keys Creative LLC | www.f-keys.com
   ------------------------------------------------------------
   Talks to audio-host.ps1, which is started once and kept, so a
   dial can report a value many times a second without paying to
   start a process each time.

   WHY THIS IS THE FIRST BACKEND

   It is the part that needs no other application. Scene
   switching is an OBS idea and only exists where OBS is
   running; volume is the operating system's, and a control
   surface that cannot change the volume is not a control
   surface. Everything here works on a machine with nothing else
   installed.

   IF THE HOST WILL NOT START

   Every call resolves to {ok:false} with a reason rather than
   hanging or throwing. A missing audio host should cost the
   audio commands and nothing else - the keystroke path is
   unrelated and has to keep working.
   ============================================================ */

var path = require('path');
var spawn = require('child_process').spawn;

var host = null;
var ready = false;
var nextId = 1;
var waiting = {};
var startError = null;

function start(log) {
  var script = path.join(__dirname, 'audio-host.ps1');
  try {
    host = spawn('powershell', [
      '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
      '-File', script
    ], { stdio: ['pipe', 'pipe', 'pipe'] });
  } catch (err) {
    startError = err.message;
    log('Audio: could not start the host - ' + err.message);
    return;
  }

  var buffer = '';
  host.stdout.on('data', function (chunk) {
    buffer += chunk.toString();
    var lines = buffer.split('\n');
    buffer = lines.pop();
    lines.forEach(function (line) {
      line = line.trim();
      if (!line) { return; }
      var msg;
      try { msg = JSON.parse(line); } catch (e) { return; }

      if (msg.id === 0) {
        ready = true;
        log('Audio: ready (Windows Core Audio, nothing installed)');
        return;
      }
      var pending = waiting[msg.id];
      if (!pending) { return; }
      delete waiting[msg.id];
      clearTimeout(pending.timer);
      pending.resolve({ ok: !!msg.ok, result: msg.result });
    });
  });

  host.stderr.on('data', function (chunk) {
    var text = chunk.toString().trim();
    if (text) { log('Audio host: ' + text.split('\n')[0]); }
  });

  host.on('exit', function (code) {
    ready = false;
    startError = 'the audio host stopped (code ' + code + ')';
    log('Audio: host exited (' + code + ')');
    // Anything still waiting is answered rather than left hanging.
    Object.keys(waiting).forEach(function (id) {
      waiting[id].resolve({ ok: false, result: startError });
      delete waiting[id];
    });
  });
}

function send(cmd, extra) {
  return new Promise(function (resolve) {
    if (!host || !ready) {
      resolve({ ok: false, result: startError || 'the audio host is not ready' });
      return;
    }
    var id = nextId++;
    var msg = Object.assign({ id: id, cmd: cmd }, extra || {});
    waiting[id] = {
      resolve: resolve,
      // A reply that never comes must not become a promise that never
      // settles; the caller gets an answer either way.
      timer: setTimeout(function () {
        delete waiting[id];
        resolve({ ok: false, result: 'the audio host did not answer' });
      }, 4000)
    };
    try {
      host.stdin.write(JSON.stringify(msg) + '\n');
    } catch (err) {
      clearTimeout(waiting[id].timer);
      delete waiting[id];
      resolve({ ok: false, result: err.message });
    }
  });
}

/* ── what a command means ─────────────────────────────────────
   The catalogue in the dashboard names these; this is where each
   one becomes something Windows does. A command with no case
   here is reported as unhandled rather than silently ignored. */
var CONTINUOUS = {
  'audio.master':   function (v) { return send('master.set', { value: v }); },
  'audio.mic.gain': function (v) { return send('mic.gain',   { value: v }); },
  'audio.desktop':  function (v) { return send('master.set', { value: v }); },
  // The application is named by whoever builds the layout. Hardcoding
  // "Discord" and "game" meant the two most useful dials on the board only
  // worked for people running exactly what I guessed they were running.
  'audio.app':      function (v, arg) { return send('session.set',
                                    { name: arg || '', value: v }); }
};

var SWITCHED = {
  'audio.mic.mute': function (on) { return send('mic.mute',    { value: on }); },
  'audio.duck':     function (on, arg) { return send('session.set',
                                     { name: arg || '', value: on ? 20 : 100 }); }
};

function handles(command) {
  return !!(CONTINUOUS[command] || SWITCHED[command] ||
            command === 'sound.play' || command === 'sound.stop' ||
            command === 'audio.mic.ptt');
}

function apply(msg) {
  var command = msg.command;

  if (msg.type === 'value' && CONTINUOUS[command]) {
    return CONTINUOUS[command](Number(msg.value), msg.arg);
  }
  if (msg.type === 'toggle' && SWITCHED[command]) {
    return SWITCHED[command](!!msg.state, msg.arg);
  }
  // Push to talk is a mute held open, which is the inverse of the state
  // the phone reports: pressed means unmuted.
  if (command === 'audio.mic.ptt') {
    return send('mic.mute', { value: !(msg.state === true || msg.down === true) });
  }
  if (command === 'sound.play') {
    var file = msg.arg || '';
    if (!file) { return Promise.resolve({ ok: false, result: 'no sound named' }); }
    return send('sound.play', {
      path: path.isAbsolute(file) ? file : path.join(__dirname, 'sounds', file)
    });
  }
  if (command === 'sound.stop') { return send('sound.stop', {}); }

  return Promise.resolve({ ok: false, result: 'not an audio command' });
}

// ── Reading the machine, not guessing at it ──────────────────
// The host has been able to answer these since it was written and nothing
// ever asked. A dial that only remembers where it was last dragged is
// wrong the moment somebody touches the volume keys on their keyboard,
// and a mute button that does not know it is muted is worse than no
// button. This is the difference between a remote control and a control
// surface.
function readState() {
  // One round trip, not four. The host answers serially, so four requests
  // twice a second was twenty four a second in the queue, and the
  // foreground check waited behind every one of them.
  return send('state', {}).then(function (r) {
    if (!r || !r.ok || !r.result) { return null; }
    var v = r.result;
    var num = function (x) {
      var n = Number(x);
      return isFinite(n) ? Math.max(0, Math.min(100, Math.round(n))) : null;
    };
    var bool = function (x) {
      return x === true || x === 'True' || x === 'true';
    };
    return {
      'audio.master':   num(v.master),
      'audio.desktop':  num(v.master),
      'audio.mic.gain': num(v.mic),
      'audio.mic.mute': bool(v.micmuted),
      masterMuted:      bool(v.mmuted),
      foreground:       typeof v.fore === 'string' ? v.fore : null
    };
  }).catch(function () { return null; });
}

function stop() {
  if (host) { try { host.stdin.end(); } catch (e) { /* already gone */ } }
}

module.exports = { start: start, send: send, apply: apply,
                   handles: handles, stop: stop, readState: readState,
                   isReady: function () { return ready; } };
