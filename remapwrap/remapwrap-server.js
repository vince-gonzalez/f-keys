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
var crypto  = require('crypto');
var url     = require('url');
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

// ── Pairing ───────────────────────────────────────────────────
// Until now anything that could reach the WebSocket port had a keyboard on
// this machine. On a home network that is a housemate; on hotel, campus or
// venue WiFi it is everyone in range. A phone now has to prove it was
// invited, in one of two ways:
//
//   scan the QR   the URL carries the secret, nothing to type
//   type the PIN  six digits shown on this screen, for a phone that
//                 reached the page some other way
//
// The dashboard is exempt only when it is this machine talking to itself.
var store = require('./store');
var licence = require('./licence');
var system  = require('./system');
var settings = store.readSettings();

// What this copy may do. Read once at start and again whenever a key is
// entered, so nothing has to restart to become paid.
var FEATURES = licence.features(settings.licence);
var PAIR_SECRET = settings.pairing.secret;
var PAIR_PIN = settings.pairing.pin;

var pinAttempts = {};        // ip -> { n, until }
var PIN_MAX = 5;
var PIN_LOCK_MS = 5 * 60 * 1000;

function sameSecret(given) {
  // Comparing with === leaks length and position through timing. The
  // amounts are tiny here, but this is the one comparison that matters.
  var a = Buffer.from(String(given || ''), 'utf8');
  var b = Buffer.from(PAIR_SECRET, 'utf8');
  if (a.length !== b.length) { return false; }
  return crypto.timingSafeEqual(a, b);
}

function isLocal(ip) {
  var v = String(ip || '');
  return v === '::1' || v === '127.0.0.1' || v === '::ffff:127.0.0.1';
}

function pinLocked(ip) {
  var rec = pinAttempts[ip];
  return !!(rec && rec.until && Date.now() < rec.until);
}

function pinFailed(ip) {
  var rec = pinAttempts[ip] || { n: 0, until: 0 };
  rec.n += 1;
  if (rec.n >= PIN_MAX) {
    rec.until = Date.now() + PIN_LOCK_MS;
    rec.n = 0;
    log('Pairing locked for ' + ip + ' after ' + PIN_MAX + ' wrong PINs');
  }
  pinAttempts[ip] = rec;
}


// ── The board that is live right now ──────────────────────────
// Held in memory so a phone that connects gets something immediately,
// rather than an empty grid until somebody touches the dashboard.
var activeProfile = null;
var activePage = 0;

function pushPage(index) {
  if (!activeProfile || !activeProfile.pages.length) { return; }
  activePage = Math.max(0, Math.min(index || 0, activeProfile.pages.length - 1));
  var page = activeProfile.pages[activePage];
  broadcastToControllers({
    type: 'layout',
    layout: { cols: page.cols, rows: page.rows, keys: page.keys },
    profile: activeProfile.name,
    page: activePage,
    pages: activeProfile.pages.length
  });
}

function loadActiveOnStart() {
  if (settings.autoLoad === false || !settings.activeProfile) { return; }
  activeProfile = store.loadProfile(settings.activeProfile);
  if (activeProfile) {
    log('Loaded profile "' + activeProfile.name + '" (' +
        activeProfile.pages.length + ' page(s))');
  } else {
    log('Last profile ' + settings.activeProfile + ' is gone; starting empty');
    settings.activeProfile = null;
    store.writeSettings(settings);
  }
}

// ── Telling the phone what is actually true ───────────────────
// Polled rather than pushed because Windows does not offer to tell us.
// Twice a second is under the threshold where a person notices a dial
// lagging, and it only runs while somebody is looking - a surface with no
// phone attached has nobody to be honest to.
var lastState = null;
var stateTimer = null;

function statesDiffer(a, b) {
  if (!a || !b) { return true; }
  return Object.keys(b).some(function (k) { return a[k] !== b[k]; });
}

function pollState() {
  audio.readState().then(function (state) {
    if (!state) { return; }
    // The same reading carries the foreground, so the watcher costs
    // nothing extra and can never queue behind the audio polling.
    considerForeground(state.foreground);
    if (!controllerClients.length) { return; }
    // Only speak when something changed. A phone does not need the same
    // sentence twice a second for an hour.
    if (statesDiffer(lastState, state)) {
      lastState = state;
      // The foreground reading rides along for the profile watcher and is
      // this machine's business. A window title carries document names,
      // email subjects and client names, and a phone has no use for any of
      // it, so it does not leave the PC.
      var forPhone = {};
      Object.keys(state).forEach(function (k) {
        if (k !== 'foreground') { forPhone[k] = state[k]; }
      });
      broadcastToControllers({ type: 'state', state: forPhone });
    }
  });
}

function startStatePolling() {
  if (stateTimer) { return; }
  // Twice a second: the reading is one round trip now, and the
  // foreground watcher rides on it.
  stateTimer = setInterval(pollState, 500);
  if (stateTimer.unref) { stateTimer.unref(); }
}

// ── Following the foreground window ───────────────────────────
// Open Photoshop, the surface becomes Photoshop. This is the paid half's
// reason to exist: it needs the service running and cannot be had by
// exporting a file, which is what makes it a fair thing to charge for.
//
// A profile opts in by naming programs:
//   { "name": "Photoshop", "match": ["photoshop", "Adobe Photoshop"], ... }
// matched against the executable name and the window title, so both ways
// of thinking about "which app is this" work.
var lastForeground = null;
var switchTimer = null;

// Built once and kept, because the old version opened, read and parsed
// every profile on disk on each foreground change - inside a timer running
// twice a second. At a dozen profiles nobody notices; at two hundred it is
// a stutter, and it was doing the work whether or not anything matched.
var matchTable = null;

function buildMatchTable() {
  matchTable = [];
  store.listProfiles().forEach(function (entry) {
    if (entry.unreadable) { return; }
    var doc = store.loadProfile(entry.file);
    if (!doc || !Array.isArray(doc.match) || !doc.match.length) { return; }
    matchTable.push({
      file: entry.file,
      needles: doc.match.filter(Boolean).map(function (m) {
        return String(m).toLowerCase();
      })
    });
  });
  return matchTable;
}

function profileMatching(exe, title) {
  var hay = (exe + ' ' + title).toLowerCase();
  var table = matchTable || buildMatchTable();
  for (var i = 0; i < table.length; i++) {
    for (var j = 0; j < table[i].needles.length; j++) {
      if (hay.indexOf(table[i].needles[j]) !== -1) {
        // The document itself is only loaded once something matched.
        var doc = store.loadProfile(table[i].file);
        if (doc) { return { file: table[i].file, doc: doc }; }
      }
    }
  }
  return null;
}

function considerForeground(reading) {
  if (!FEATURES.autoSwitch || typeof reading !== 'string') { return; }
  if (reading === lastForeground && !matchDirty) { return; }   // nothing moved
  lastForeground = reading;
  matchDirty = false;

  var split = reading.split('|');
  var hit = profileMatching(split[0] || '', split.slice(1).join('|') || '');
  if (!hit || hit.file === settings.activeProfile) { return; }

  settings.activeProfile = hit.file;
  store.writeSettings(settings);
  activeProfile = hit.doc;
  activePage = 0;
  pushPage(0);
  log('Foreground is ' + (split[0] || '?') + ' - switched to "' + hit.doc.name + '"');
  broadcastToDashboards({ type: 'profile_switched', file: hit.file,
                          name: hit.doc.name, reason: split[0] });
}

// ── HTTP Server (dashboard, controller, assets, QR) ───────────
var httpServer = http.createServer(function(req, res) {
  // READS: CONFIG.HTTP_PORT, local filesystem
  // WRITES: HTTP response

  if (req.url === '/qr' || req.url === '/qr.png') {
    // The QR is the invitation, so it carries the secret. A phone that
    // scans it is paired without typing anything.
    var controllerURL = 'http://' + getLocalIP() + ':' + CONFIG.HTTP_PORT +
                        '/controller?k=' + PAIR_SECRET;
    QRCode.toBuffer(controllerURL, { width: 300, margin: 2 }, function(err, buf) {
      if (err) { res.writeHead(500); res.end('QR error'); return; }
      res.writeHead(200, { 'Content-Type': 'image/png' });
      res.end(buf);
    });
    return;
  }

  // A phone that reached this page without scanning types the six digits
  // shown on the PC. Five wrong tries locks that address out for five
  // minutes, so the six digit space cannot simply be walked.
  if (req.url === '/pair' && req.method === 'POST') {
    var ip = req.socket.remoteAddress;
    var body = '';
    req.on('data', function (chunk) {
      body += chunk;
      if (body.length > 512) { req.destroy(); }   // nothing legitimate is bigger
    });
    req.on('end', function () {
      res.setHeader('Content-Type', 'application/json');
      if (pinLocked(ip)) {
        res.writeHead(429);
        res.end(JSON.stringify({ ok: false, error: 'Too many tries. Wait five minutes.' }));
        return;
      }
      var given = '';
      try { given = String((JSON.parse(body) || {}).pin || ''); } catch (e) { given = ''; }
      if (given.length === 6 && given === PAIR_PIN) {
        pinAttempts[ip] = { n: 0, until: 0 };
        log('Paired ' + ip + ' by PIN');
        res.writeHead(200);
        res.end(JSON.stringify({ ok: true, token: PAIR_SECRET }));
      } else {
        pinFailed(ip);
        res.writeHead(401);
        res.end(JSON.stringify({ ok: false, error: 'That PIN is not right.' }));
      }
    });
    return;
  }

  // The PIN is only ever readable by this machine. Handing it out over the
  // network would make it exactly as useful as no PIN at all.
  if (req.url === '/pin') {
    if (!isLocal(req.socket.remoteAddress)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false }));
      return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, pin: PAIR_PIN }));
    return;
  }

  // ── Licence ─────────────────────────────────────────────────
  // Local only. The paid half of the product is unlocked by a signed key
  // and never by a call to us, so a paid copy works with no internet.
  if (req.url === '/licence' && req.method === 'GET') {
    if (!isLocal(req.socket.remoteAddress)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false })); return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      ok: true, tier: FEATURES.tier, name: FEATURES.name,
      licensed: FEATURES.licensed, reason: FEATURES.reason,
      features: {
        autoSwitch: FEATURES.autoSwitch, imageKeys: FEATURES.imageKeys,
        meters: FEATURES.meters,
        devices: FEATURES.devices === Infinity ? null : FEATURES.devices
      }
    }));
    return;
  }

  if (req.url === '/licence' && req.method === 'POST') {
    if (!isLocal(req.socket.remoteAddress)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false })); return;
    }
    var lbody = '';
    req.on('data', function (c) { lbody += c; if (lbody.length > 8192) { req.destroy(); } });
    req.on('end', function () {
      var given = '';
      try { given = String((JSON.parse(lbody) || {}).key || '').trim(); } catch (e) { given = ''; }
      var seen = licence.features(given);
      res.setHeader('Content-Type', 'application/json');
      if (!seen.licensed) {
        res.writeHead(400);
        res.end(JSON.stringify({ ok: false, error: seen.reason }));
        return;
      }
      settings.licence = given;
      store.writeSettings(settings);
      FEATURES = seen;
      matchDirty = true; matchTable = null;
      log('Licensed to ' + (seen.name || 'unnamed') + ' (' + seen.tier + ')');
      res.writeHead(200);
      res.end(JSON.stringify({ ok: true, tier: seen.tier, name: seen.name }));
    });
    return;
  }

  // Taking a licence off a machine is the other half of putting one on:
  // somebody replacing a PC needs the key back, not stranded here.
  if (req.url === '/licence/remove' && req.method === 'POST') {
    if (!isLocal(req.socket.remoteAddress)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false })); return;
    }
    delete settings.licence;
    store.writeSettings(settings);
    FEATURES = licence.features(null);
    matchDirty = true; matchTable = null;
    log('Licence removed; this copy is free again');
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, tier: FEATURES.tier }));
    return;
  }

  // ── Profiles ────────────────────────────────────────────────
  // Everything here is this machine's own business: the dashboard runs on
  // localhost and phones never touch profiles, they are sent a board.
  if (req.url.indexOf('/profiles') === 0 || req.url.indexOf('/profile') === 0) {
    if (!isLocal(req.socket.remoteAddress)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false }));
      return;
    }
    res.setHeader('Content-Type', 'application/json');

    if (req.url === '/profiles') {
      res.writeHead(200);
      res.end(JSON.stringify({ ok: true, active: settings.activeProfile,
                               autoLoad: settings.autoLoad !== false,
                               profiles: store.listProfiles() }));
      return;
    }

    var q = url.parse(req.url, true).query;

    if (req.method === 'GET' && q.file) {
      var doc = store.loadProfile(q.file);
      res.writeHead(doc ? 200 : 404);
      res.end(JSON.stringify(doc ? { ok: true, profile: doc }
                                 : { ok: false, error: 'No such profile.' }));
      return;
    }

    if (req.method === 'POST' && req.url.indexOf('/profile/delete') === 0) {
      matchDirty = true; matchTable = null;
      var gone = store.deleteProfile(q.file || '');
      if (gone && settings.activeProfile === q.file) {
        settings.activeProfile = null;
        store.writeSettings(settings);
      }
      res.writeHead(gone ? 200 : 404);
      res.end(JSON.stringify({ ok: gone }));
      return;
    }

    if (req.method === 'POST' && req.url.indexOf('/profile/activate') === 0) {
      var chosen = store.loadProfile(q.file || '');
      if (!chosen) { res.writeHead(404); res.end(JSON.stringify({ ok: false })); return; }
      settings.activeProfile = q.file;
      store.writeSettings(settings);
      activeProfile = chosen;
      pushPage(0);
      res.writeHead(200);
      res.end(JSON.stringify({ ok: true, profile: chosen }));
      return;
    }

    if (req.method === 'POST') {
      var body = '';
      req.on('data', function (c) {
        body += c;
        if (body.length > 4 * 1024 * 1024) { req.destroy(); }
      });
      req.on('end', function () {
        var doc = null;
        try { doc = JSON.parse(body); } catch (e) { doc = null; }
        if (!doc) { res.writeHead(400); res.end(JSON.stringify({ ok: false, error: 'Not a profile.' })); return; }
        matchDirty = true; matchTable = null;
        var file = store.saveProfile(doc);
        settings.activeProfile = file;
        store.writeSettings(settings);
        activeProfile = store.loadProfile(file);
        log('Saved profile ' + file);
        res.writeHead(200);
        res.end(JSON.stringify({ ok: true, file: file }));
      });
      return;
    }

    res.writeHead(405);
    res.end(JSON.stringify({ ok: false }));
    return;
  }

  if (req.url === '/manifest.webmanifest') {
    fs.readFile(path.join(__dirname, 'manifest.webmanifest'), function (err, buf) {
      if (err) { res.writeHead(404); res.end('no manifest'); return; }
      // Android will not offer to install without this content type.
      res.writeHead(200, { 'Content-Type': 'application/manifest+json' });
      res.end(buf);
    });
    return;
  }

  // The editor needs to know what a real key is called, and there must be
  // exactly one answer to that. Shipping a second list in the dashboard is
  // how the first one drifted seventy keys behind the library.
  if (req.url === '/keys') {
    if (!isLocal(req.socket.remoteAddress)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false })); return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, keys: Object.keys(KEYS).sort() }));
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

  // The dashboard builds boards and hands out the pairing PIN, so it is
  // only ever this machine. Asking for it from another device gets the
  // controller instead, which is what that device actually wanted.
  if (page === 'dashboard.html' && !isLocal(req.socket.remoteAddress)) {
    res.writeHead(302, { Location: '/controller' });
    res.end();
    return;
  }

  fs.readFile(path.join(__dirname, page), function(err, data) {
    if (err) {
      res.writeHead(404);
      res.end(page + ' not found - it belongs beside remapwrap-server.js');
      return;
    }
    // The controller carries a marker for this; the dashboard asks /ip.
    var injected = data.toString().replace(
      '/* __SERVER_IP_INJECT__ */',
      'var SERVER_IP = "' + getLocalIP() + '"; var WS_PORT = ' + CONFIG.WS_PORT + ';' +
      (page === 'dashboard.html'
        ? ' var PAIR_TOKEN = "' + PAIR_SECRET + '"; var PAIR_PIN = "' + PAIR_PIN + '";'
        : '')
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
  loadActiveOnStart();
  startStatePolling();
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
          if (!isLocal(clientIP) && !sameSecret(msg.token)) {
            log('Refused a remote dashboard from ' + clientIP);
            ws.send(JSON.stringify({ type: 'unpaired' }));
            ws.close();
            return;
          }
          dashboardClients.push(ws);
          log('Dashboard registered (' + dashboardClients.length + ' active)');
        } else if (clientType === 'controller') {
          // The gate. Without this, reaching the port was the whole
          // qualification for having a keyboard on this machine.
          if (!sameSecret(msg.token)) {
            log('Refused an unpaired controller from ' + clientIP);
            ws.send(JSON.stringify({ type: 'unpaired' }));
            ws.close();
            return;
          }
          // The only ceiling the free tier has. Everything that makes
          // this a control surface - keys, profiles, pages, placement -
          // is unlimited and stays unlimited.
          if (controllerClients.length >= FEATURES.devices) {
            log('Refused a phone: ' + FEATURES.devices +
                ' already connected on the ' + FEATURES.tier + ' tier');
            ws.send(JSON.stringify({ type: 'too_many_devices',
                                     limit: FEATURES.devices }));
            ws.close();
            return;
          }
          controllerClients.push(ws);
          log('Controller registered (' + controllerClients.length + ' active)');
          // Send controller the current layout if dashboard is connected
          broadcastToDashboards({ type: 'controller_connected', ip: clientIP });
          // Hand it the live board straight away instead of an empty
          // grid it keeps until somebody touches the dashboard.
          if (activeProfile) { setTimeout(function () { pushPage(activePage); }, 60); }
          // A phone that just arrived has no idea where anything is.
          lastState = null;
          setTimeout(pollState, 120);
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
        if (fireCommand(msg)) { ackTo(ws, msg.id, true); return; }

        // Fire keystroke if nut-js is loaded and action is mapped
        if (keyboard && msg.action && msg.action !== 'none') {
          fireKeystroke(msg.action);
          ackTo(ws, msg.id, true);
        } else {
          // Nothing ran. Saying so is the difference between a button that
          // feels broken and a button that tells you it is not wired up.
          ackTo(ws, msg.id, false);
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

      // ── A phone asking for another page ────────────────────
      // pushPage has always sent the page number and the count; nothing
      // could ask for a different one, so a profile with four pages showed
      // its first one forever.
      if (msg.type === 'page') {
        var want = parseInt(msg.index, 10);
        if (!activeProfile || isNaN(want)) { return; }
        pushPage(want);
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
// A phone gets no feedback of its own worth having: navigator.vibrate does
// not exist on iOS at all, so a press on an iPhone was silent in every
// sense. The PC now answers every press, and the key confirms on screen -
// which works on every phone, and says whether anything actually ran.
function ackTo(ws, id, ok) {
  if (!id || ws.readyState !== WebSocket.OPEN) { return; }
  try { ws.send(JSON.stringify({ type: 'ack', id: id, ok: !!ok })); }
  catch (e) { /* the phone left mid-press */ }
}

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
// What a command may use to make something happen. Passed in rather than
// imported so system.js never has to know what a keyboard is.
var FIRE = {
  combo: function (action) { return fireKeystroke(action); },
  type: function (text) {
    if (!keyboard) { return Promise.reject(new Error('no keyboard')); }
    return keyboard.type(text);
  }
};

function fireCommand(msg) {
  // Three layers now: sound, the things Windows can do on its own, and
  // plain key combinations, which is what this started as.
  if (audio.handles(msg.command)) {
    audio.apply(msg).then(function (r) {
      if (!r.ok) { log('Audio: ' + msg.command + ' - ' + r.result); }
    });
    return true;
  }
  if (system.handles(msg.command)) {
    system.apply(msg, FIRE, log).then(function (r) {
      if (!r.ok) { log('System: ' + msg.command + ' - ' + r.result); }
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

    if (keys.length === 0) {
      log('No valid keys resolved for action: ' + action);
      return Promise.resolve();
    }

    // Returned rather than fired and forgotten, so a macro can wait for
    // one step to finish before starting the next.
    return keyboard.pressKey.apply(keyboard, keys).then(function() {
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
