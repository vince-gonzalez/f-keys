// ============================================================
// WORKFLOW STACK
// File:        remapwrap-server.js
// Product:     RemapWrap  (F-Keys Creative LLC)
// Author:      Vincent Gonzalez | (c) 2026 F-Keys Creative LLC | www.f-keys.com
// Version:     v0.1.0
// Description: RemapWrap bridge — relays phone button
//              presses to PC dashboard and fires keystrokes.
// Boot Order:
//   1. Load config
//   2. Start HTTP server (serves controller page + QR)
//   3. Start WebSocket server
//   4. Await connections from dashboard + controller
// External Deps:
//   - ws          (npm install ws)
//   - @nut-tree-fork/nut-js  (npm install @nut-tree-fork/nut-js)
//   - qrcode      (npm install qrcode)
//   - fs, http, os (built-in)
// Layout Target: CLI / headless
// Browser Target: N/A
// ============================================================

// ============================================================
// ASSET MANIFEST
// ws                   — WebSocket server
// @nut-tree-fork/nut-js — keystroke injection (cross-platform)
// qrcode               — QR code generation for pairing
// ============================================================

/* ===== CONFIG BLOCK ===== */
var CONFIG = {
  HTTP_PORT:       7331,   // serves controller.html + QR endpoint
  WS_PORT:         7332,   // WebSocket bridge port
  DEV_MODE:        true,   // verbose logging
  KEY_DELAY_MS:    30,     // ms between keydown/keyup
  MAX_CLIENTS:     8,      // max simultaneous connections
};
/* ===== END CONFIG BLOCK ===== */

var http    = require('http');
var fs      = require('fs');
var path    = require('path');
var os      = require('os');
var WebSocket = require('ws');
var QRCode  = require('qrcode');
var audio   = require('./audio');

var MIME = {
  '.css': 'text/css', '.png': 'image/png', '.ico': 'image/x-icon',
  '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
  '.woff': 'font/woff', '.js': 'text/javascript',
  '.json': 'application/json'
};

// ── Keystroke injection (optional — gracefully degrades) ──────
var keyboard = null;
var Key = null;
try {
  var nut = require('@nut-tree-fork/nut-js');
  keyboard = nut.keyboard;
  Key = nut.Key;
  log('Keystroke injection: ACTIVE (nut-js loaded)');
} catch (e) {
  log('Keystroke injection: INACTIVE (nut-js not found — install @nut-tree-fork/nut-js)');
  log('Running in relay-only mode. Dashboard will still receive all events.');
}

// ── Utility ───────────────────────────────────────────────────
function log(msg) {
  if (CONFIG.DEV_MODE) console.log('[RemapWrap ' + timestamp() + '] ' + msg);
}
function timestamp() {
  return new Date().toTimeString().slice(0,8);
}
function getLocalIP() {
  var interfaces = os.networkInterfaces();
  var candidates = [];
  for (var iface in interfaces) {
    interfaces[iface].forEach(function(addr) {
      if (addr.family === 'IPv4' && !addr.internal) candidates.push(addr.address);
    });
  }
  return candidates[0] || '127.0.0.1';
}

// ── HTTP Server (dashboard, controller, assets, QR) ───────────
var httpServer = http.createServer(function(req, res) {
  // READS: CONFIG.HTTP_PORT, local filesystem
  // WRITES: HTTP response

  if (req.url === '/qr' || req.url === '/qr.png') {
    var controllerURL = 'http://' + getLocalIP() + ':' + CONFIG.HTTP_PORT + '/controller';
    QRCode.toBuffer(controllerURL, { width: 300, margin: 2 }, function(err, buf) {
      if (err) { res.writeHead(500); res.end('QR error'); return; }
      res.writeHead(200, { 'Content-Type': 'image/png' });
      res.end(buf);
    });
    return;
  }

  if (req.url === '/ip') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ip: getLocalIP(), wsPort: CONFIG.WS_PORT, httpPort: CONFIG.HTTP_PORT }));
    return;
  }

  // Serve the assets both pages ask for: the mark, the icon, the fonts.
  // Nothing served these, so every page load fetched assets/fonts.css and
  // got the controller HTML back with a 200 on it.
  if (req.url.indexOf('/assets/') === 0) {
    var safe = path.normalize(req.url).replace(/^(\.\.[\/\\])+/, '');
    var assetPath = path.join(__dirname, safe);
    if (assetPath.indexOf(path.join(__dirname, 'assets')) !== 0) {
      res.writeHead(403); res.end('no'); return;
    }
    fs.readFile(assetPath, function(err, buf) {
      if (err) { res.writeHead(404); res.end('not found'); return; }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(assetPath)] ||
                                           'application/octet-stream' });
      res.end(buf);
    });
    return;
  }

  // The dashboard is the PC side and the controller is the phone side, and
  // until now every address served the phone side - including the one the
  // startup banner tells you to open. The layout builder, which is the
  // larger half of the product, could not be reached at all.
  var page = (req.url === '/controller' || req.url.indexOf('/controller?') === 0)
    ? 'controller.html'
    : (req.url === '/' || req.url === '/dashboard' ? 'dashboard.html' : null);

  if (!page) { res.writeHead(404); res.end('not found'); return; }

  fs.readFile(path.join(__dirname, page), function(err, data) {
    if (err) {
      res.writeHead(404);
      res.end(page + ' not found - it belongs beside remapwrap-server.js');
      return;
    }
    // The controller carries a marker for this; the dashboard asks /ip.
    var injected = data.toString().replace(
      '/* __SERVER_IP_INJECT__ */',
      'var SERVER_IP = "' + getLocalIP() + '"; var WS_PORT = ' + CONFIG.WS_PORT + ';'
    );
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(injected);
  });
});

/*
  A port already in use is the commonest way to start this twice, and it
  ended the process with an unhandled 'error' event and eleven lines of
  stack. The person reading that is the person who left it running in
  another window.
*/
function portTaken(which, port) {
  return function(err) {
    if (err && err.code === 'EADDRINUSE') {
      log('Port ' + port + ' (' + which + ') is already in use.');
      log('RemapWrap is probably already running - open ' +
          'http://' + getLocalIP() + ':' + CONFIG.HTTP_PORT + '/ and use that one.');
      log('If it is not, close whatever holds port ' + port + ' and start again.');
    } else if (err && err.code === 'EACCES') {
      log('Not allowed to open port ' + port + '. Try a port above 1024.');
    } else {
      log('Could not start the ' + which + ' server: ' + (err && err.message));
    }
    process.exit(1);
  };
}

httpServer.on('error', portTaken('HTTP', CONFIG.HTTP_PORT));
httpServer.listen(CONFIG.HTTP_PORT, function() {
  log('HTTP server listening on port ' + CONFIG.HTTP_PORT);
  // Started here rather than on first use, so the compile cost is paid
  // while the QR code is still being scanned instead of on the first
  // turn of a dial.
  audio.start(log);
});

// ── WebSocket Server ──────────────────────────────────────────
var wss = new WebSocket.Server({ port: CONFIG.WS_PORT });
wss.on('error', portTaken('WebSocket', CONFIG.WS_PORT));
var dashboardClients = [];   // PC dashboard connections
var controllerClients = [];  // Phone controller connections

wss.on('connection', function(ws, req) {
  // READS:  dashboardClients, controllerClients
  // WRITES: dashboardClients, controllerClients

  var clientIP = req.socket.remoteAddress;
  var clientType = 'unknown';
  log('New connection from ' + clientIP);

  ws.on('message', function(raw) {
    // READS:  raw message, keyboard, Key
    // WRITES: dashboardClients (relay), keyboard state
    try {
      var msg = JSON.parse(raw);

      // ── Registration handshake ──────────────────────────────
      if (msg.type === 'register') {
        clientType = msg.role; // 'dashboard' or 'controller'
        if (clientType === 'dashboard') {
          dashboardClients.push(ws);
          log('Dashboard registered (' + dashboardClients.length + ' active)');
        } else if (clientType === 'controller') {
          controllerClients.push(ws);
          log('Controller registered (' + controllerClients.length + ' active)');
          // Send controller the current layout if dashboard is connected
          broadcastToDashboards({ type: 'controller_connected', ip: clientIP });
        }
        ws.send(JSON.stringify({ type: 'registered', role: clientType, serverTime: Date.now() }));
        return;
      }

      // ── Button press from controller ────────────────────────
      if (msg.type === 'keypress') {
        log('KEYPRESS: id=' + msg.id + ' label=' + msg.label + ' action=' + msg.action);

        // Relay to all dashboards for visual feedback
        broadcastToDashboards({ type: 'keypress', id: msg.id, label: msg.label, action: msg.action, ts: Date.now() });

        // Audio owns some of the catalogue now. Anything it claims goes
        // there; the rest is still a key combination.
        if (fireCommand(msg)) { return; }

        // Fire keystroke if nut-js is loaded and action is mapped
        if (keyboard && msg.action && msg.action !== 'none') {
          fireKeystroke(msg.action);
        }
        return;
      }

      // ── Layout push from dashboard to controllers ───────────
      if (msg.type === 'layout_push') {
        log('Layout push from dashboard → controllers');
        broadcastToControllers({ type: 'layout', layout: msg.layout });
        return;
      }

      // ── A dial or a slider reporting where it was left ──────
      if (msg.type === 'value') {
        if (audio.handles(msg.command)) {
          audio.apply(msg).then(function (r) {
            if (!r.ok) { log('Audio: ' + msg.command + ' - ' + r.result); }
          });
          broadcastToDashboards({ type: 'feed', label: msg.label,
                                  action: msg.command + ' = ' + msg.value,
                                  id: msg.id, ts: Date.now() });
        } else {
          log('No handler yet for ' + msg.command + ' (value)');
        }
        return;
      }

      // ── A toggle reporting what it became ───────────────────
      if (msg.type === 'toggle') {
        if (audio.handles(msg.command)) {
          audio.apply(msg).then(function (r) {
            if (!r.ok) { log('Audio: ' + msg.command + ' - ' + r.result); }
          });
        } else {
          log('No handler yet for ' + msg.command + ' (toggle)');
        }
        broadcastToDashboards({ type: 'feed', label: msg.label,
                                action: msg.command + ' ' +
                                        (msg.state ? 'on' : 'off'),
                                id: msg.id, ts: Date.now() });
        return;
      }

      // ── Ping/pong ───────────────────────────────────────────
      if (msg.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', ts: Date.now() }));
        return;
      }

      log('Unknown message type: ' + msg.type);

    } catch (e) {
      console.error('[RemapWrap] Message parse error:', e.message);
    }
  });

  ws.on('close', function() {
    // READS:  dashboardClients, controllerClients
    // WRITES: dashboardClients, controllerClients
    dashboardClients = dashboardClients.filter(function(c) { return c !== ws; });
    controllerClients = controllerClients.filter(function(c) { return c !== ws; });
    log('Client disconnected (' + clientType + ') — ' + clientIP);
    broadcastToDashboards({ type: 'controller_disconnected', ip: clientIP });
  });

  ws.on('error', function(err) {
    console.error('[RemapWrap] WebSocket error:', err.message);
  });
});

wss.on('listening', function() {
  var ip = getLocalIP();
  log('WebSocket server listening on port ' + CONFIG.WS_PORT);
  console.log('\n╔══════════════════════════════════════════════╗');
  console.log('║        RemapWrap  SERVER  v0.1.0  RUNNING    ║');
  console.log('╠══════════════════════════════════════════════╣');
  console.log('║  Dashboard:  http://' + ip + ':' + CONFIG.HTTP_PORT + '/        ');
  console.log('║  Controller: http://' + ip + ':' + CONFIG.HTTP_PORT + '/controller');
  console.log('║  QR Code:    http://' + ip + ':' + CONFIG.HTTP_PORT + '/qr      ');
  console.log('║  WebSocket:  ws://' + ip + ':' + CONFIG.WS_PORT + '           ');
  console.log('╚══════════════════════════════════════════════╝');
  console.log('\nOpen the Dashboard URL in your PC browser.');
  console.log('Scan the QR code with your phone to launch the controller.\n');
});

wss.on('error', function(err) {
  console.error('[RemapWrap] WSS error:', err.message);
});

// ── Broadcast helpers ─────────────────────────────────────────
function broadcastToDashboards(obj) {
  // READS: dashboardClients
  var str = JSON.stringify(obj);
  dashboardClients.forEach(function(ws) {
    if (ws.readyState === WebSocket.OPEN) ws.send(str);
  });
}

function broadcastToControllers(obj) {
  // READS: controllerClients
  var str = JSON.stringify(obj);
  controllerClients.forEach(function(ws) {
    if (ws.readyState === WebSocket.OPEN) ws.send(str);
  });
}

// ── Keystroke injection ───────────────────────────────────────
function fireCommand(msg) {
  // The catalogue has grown past keystrokes. Anything audio owns goes to
  // the audio host; everything else is still a key combination, which is
  // what this started as and what most commands still are.
  if (audio.handles(msg.command)) {
    audio.apply(msg).then(function (r) {
      if (!r.ok) { log('Audio: ' + msg.command + ' - ' + r.result); }
    });
    return true;
  }
  return false;
}

function fireKeystroke(action) {
  // READS: keyboard, Key, action string
  // WRITES: OS keyboard state via nut-js
  // DEPENDS ON: keyboard (nut-js), Key enum
  try {
    // action format examples: "ctrl+c", "f5", "ctrl+shift+t", "volumeup"
    var keys = parseCombo(action)
                 .map(resolveKey)
                 .filter(function (k) { return k !== null; });

    if (keys.length === 0) { log('No valid keys resolved for action: ' + action); return; }

    keyboard.pressKey.apply(keyboard, keys).then(function() {
      return keyboard.releaseKey.apply(keyboard, keys);
    }).catch(function(e) {
      console.error('[RemapWrap] fireKeystroke error:', e.message);
    });
  } catch(e) {
    console.error('[RemapWrap] fireKeystroke error:', e.message);
  }
}

// ── The keyboard, all of it ───────────────────────────────────
// Hand-typing this map got about seventy of the hundred and thirty-seven
// keys nut-js can press, and the ones it missed were not exotic: INSERT and
// = were both absent, which is what somebody binding "copy, paste, insert"
// at a desk reaches for first. So the table is built from the enum rather
// than transcribed from it, and it cannot fall behind the library again.
var KEYS = (function () {
  var table = {};
  Object.keys(Key).forEach(function (name) {
    if (!isNaN(Number(name))) { return; }          // reverse numeric entries
    table[name.toLowerCase()] = Key[name];
  });

  // What people actually type, mapped onto what the enum calls it.
  var alias = {
    'control': 'leftcontrol', 'ctrl': 'leftcontrol', 'lctrl': 'leftcontrol',
    'rctrl': 'rightcontrol', 'shift': 'leftshift', 'lshift': 'leftshift',
    'rshift': 'rightshift', 'alt': 'leftalt', 'lalt': 'leftalt',
    'ralt': 'rightalt', 'altgr': 'rightalt',
    'win': 'leftsuper', 'cmd': 'leftsuper', 'super': 'leftsuper',
    'meta': 'leftsuper', 'windows': 'leftsuper',
    'esc': 'escape', 'enter': 'return', 'ins': 'insert', 'del': 'delete',
    'pgup': 'pageup', 'pgdn': 'pagedown', 'pgdown': 'pagedown',
    'caps': 'capslock', 'printscreen': 'print', 'prtsc': 'print',
    'menu': 'menu', 'apps': 'menu', 'break': 'pause',
    'volumeup': 'audiovolup', 'volup': 'audiovolup',
    'volumedown': 'audiovoldown', 'voldown': 'audiovoldown',
    'mute': 'audiomute', 'playpause': 'audioplay', 'play': 'audioplay',
    'next': 'audionext', 'prev': 'audioprev', 'previous': 'audioprev',
    'stop': 'audiostop',
    // Punctuation, by the character somebody would print on the key.
    '=': 'equal', 'plus': 'add', '-': 'minus', '_': 'minus',
    ',': 'comma', '.': 'period', '/': 'slash', ';': 'semicolon',
    "'": 'quote', '[': 'leftbracket', ']': 'rightbracket',
    '\\': 'backslash', '`': 'grave', '~': 'grave',
    'space': 'space', 'spacebar': 'space',
    // Numpad, written the way a label reads.
    'numpadplus': 'add', 'numpadminus': 'subtract',
    'numpadtimes': 'multiply', 'numpaddivide': 'divide',
    'numpaddot': 'decimal', 'numpadenter': 'enter'
  };
  Object.keys(alias).forEach(function (from) {
    var to = table[alias[from]];
    if (to !== undefined) { table[from] = to; }
  });
  return table;
})();

function parseCombo(action) {
  // Splitting on "+" loses the plus key itself: "ctrl++" became ctrl and two
  // empty tokens. A trailing separator is the key, not a separator.
  var s = String(action || '').trim().toLowerCase();
  if (!s) { return []; }
  if (s === '+') { return ['plus']; }
  var tail = null;
  if (s.charAt(s.length - 1) === '+') {
    tail = 'plus';
    s = s.slice(0, -1);
    if (s.charAt(s.length - 1) === '+') { s = s.slice(0, -1); }
  }
  var parts = s.split('+')
               .map(function (t) { return t.trim(); })
               .filter(function (t) { return t !== ''; });
  if (tail) { parts.push(tail); }
  return parts;
}

function resolveKey(part) {
  var resolved = KEYS[part];
  if (resolved === undefined) { log('WARN: unresolved key token "' + part + '"'); }
  return resolved === undefined ? null : resolved;
}

/* ===== LAST STABLE: none — initial build ===== */

/*
CHANGE LOG v0.1.0
- Initial build. HTTP server serves controller.html with injected IP.
- WebSocket server relays keypresses from controller → dashboard.
- nut-js keystroke injection with graceful degradation if not installed.
- QR code endpoint at /qr for phone pairing.
- /ip endpoint returns server metadata for dashboard auto-connect.
- Register handshake distinguishes dashboard vs controller clients.

NEXT STEPS
- Add layout persistence (save/load JSON from disk)
- Add reconnection logic (controller auto-reconnects on drop)
- Explore robotjs as alternate injector (simpler install on some systems)
- Add UDP fast-path for dial/slider real-time inputs
*/

// The audio host is a child process; it goes when this does.
process.on('exit', function () { audio.stop(); });
process.on('SIGINT', function () { audio.stop(); process.exit(0); });
