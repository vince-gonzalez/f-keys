// ============================================================
// WORKFLOW STACK
// File:        remapwrap-server.js
// Brand:       F-Keys
// Author:      Vincent Gonzalez | (c) 2026 F-Keys Creative LLC | www.f-keys.com
// Version:     v0.1.0
// Description: F-Keys WebSocket bridge — relays phone button
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
  if (CONFIG.DEV_MODE) console.log('[F-KEYS ' + timestamp() + '] ' + msg);
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

httpServer.listen(CONFIG.HTTP_PORT, function() {
  log('HTTP server listening on port ' + CONFIG.HTTP_PORT);
});

// ── WebSocket Server ──────────────────────────────────────────
var wss = new WebSocket.Server({ port: CONFIG.WS_PORT });
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

      // ── Ping/pong ───────────────────────────────────────────
      if (msg.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', ts: Date.now() }));
        return;
      }

      log('Unknown message type: ' + msg.type);

    } catch (e) {
      console.error('[F-KEYS] Message parse error:', e.message);
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
    console.error('[F-KEYS] WebSocket error:', err.message);
  });
});

wss.on('listening', function() {
  var ip = getLocalIP();
  log('WebSocket server listening on port ' + CONFIG.WS_PORT);
  console.log('\n╔══════════════════════════════════════════════╗');
  console.log('║         F-KEYS SERVER v0.1.0 RUNNING         ║');
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
  console.error('[F-KEYS] WSS error:', err.message);
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
function fireKeystroke(action) {
  // READS: keyboard, Key, action string
  // WRITES: OS keyboard state via nut-js
  // DEPENDS ON: keyboard (nut-js), Key enum
  try {
    // action format examples: "ctrl+c", "f5", "ctrl+shift+t", "volumeup"
    var parts = action.toLowerCase().split('+');
    var keys = parts.map(function(part) {
      return resolveKey(part);
    }).filter(Boolean);

    if (keys.length === 0) { log('No valid keys resolved for action: ' + action); return; }

    keyboard.pressKey.apply(keyboard, keys).then(function() {
      return keyboard.releaseKey.apply(keyboard, keys);
    }).catch(function(e) {
      console.error('[F-KEYS] fireKeystroke error:', e.message);
    });
  } catch(e) {
    console.error('[F-KEYS] fireKeystroke error:', e.message);
  }
}

function resolveKey(part) {
  // READS: Key enum from nut-js
  // Maps common string names to nut-js Key constants
  var map = {
    'ctrl': Key.LeftControl, 'control': Key.LeftControl,
    'shift': Key.LeftShift,
    'alt': Key.LeftAlt,
    'win': Key.LeftSuper, 'cmd': Key.LeftSuper, 'super': Key.LeftSuper,
    'enter': Key.Return, 'return': Key.Return,
    'space': Key.Space,
    'tab': Key.Tab,
    'esc': Key.Escape, 'escape': Key.Escape,
    'backspace': Key.Backspace,
    'delete': Key.Delete,
    'up': Key.Up, 'down': Key.Down, 'left': Key.Left, 'right': Key.Right,
    'f1': Key.F1, 'f2': Key.F2, 'f3': Key.F3, 'f4': Key.F4,
    'f5': Key.F5, 'f6': Key.F6, 'f7': Key.F7, 'f8': Key.F8,
    'f9': Key.F9, 'f10': Key.F10, 'f11': Key.F11, 'f12': Key.F12,
    'volumeup': Key.AudioVolUp, 'volumedown': Key.AudioVolDown,
    'mute': Key.AudioMute, 'playpause': Key.AudioPlay,
    'home': Key.Home, 'end': Key.End, 'pageup': Key.PageUp, 'pagedown': Key.PageDown,
    'a': Key.A, 'b': Key.B, 'c': Key.C, 'd': Key.D, 'e': Key.E,
    'f': Key.F, 'g': Key.G, 'h': Key.H, 'i': Key.I, 'j': Key.J,
    'k': Key.K, 'l': Key.L, 'm': Key.M, 'n': Key.N, 'o': Key.O,
    'p': Key.P, 'q': Key.Q, 'r': Key.R, 's': Key.S, 't': Key.T,
    'u': Key.U, 'v': Key.V, 'w': Key.W, 'x': Key.X, 'y': Key.Y, 'z': Key.Z,
    '0': Key.Num0, '1': Key.Num1, '2': Key.Num2, '3': Key.Num3, '4': Key.Num4,
    '5': Key.Num5, '6': Key.Num6, '7': Key.Num7, '8': Key.Num8, '9': Key.Num9,
  };
  var resolved = map[part];
  if (!resolved) log('WARN: unresolved key token "' + part + '"');
  return resolved || null;
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
