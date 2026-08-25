/* ============================================================
   store — where RemapWrap keeps things
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   WHY THIS EXISTS

   Two separate problems turned out to be the same problem. A
   paired phone has to be remembered between runs, and a board
   somebody built has to survive closing the app. Both are "a
   file in a known place", so there is one module for it.

   THE FOLDER IS THE INTERFACE

     %APPDATA%\RemapWrap\settings.json    pairing + what is active
     %APPDATA%\RemapWrap\profiles\*.json  one file per profile

   A profile dropped into that folder appears in the app. That is
   deliberate: it makes the remapwrap Python package a first
   class citizen with no import UI at all, because writing a file
   there is the same as importing it.

   THE FORMAT IS VERSIONED FROM THE FIRST DAY

   A profile carries "schema": 1 and holds pages, even when there
   is only one. Both were cheap to decide now and expensive to
   retrofit once people have files they care about.

     { "schema": 1, "name": "Streaming",
       "pages": [ { "name": "Main", "cols": 12, "rows": 21,
                    "keys": [ ... ] } ] }

   No dependencies beyond node's own fs and crypto.
   ============================================================ */

var fs = require('fs');
var os = require('os');
var path = require('path');
var crypto = require('crypto');

var SCHEMA = 1;

function root() {
  // APPDATA is where a Windows application is supposed to put this. The
  // fallback is for running from a shell that does not export it.
  var base = process.env.APPDATA ||
             path.join(os.homedir(), 'AppData', 'Roaming');
  return path.join(base, 'RemapWrap');
}

function profilesDir() { return path.join(root(), 'profiles'); }
function settingsPath() { return path.join(root(), 'settings.json'); }

function ensure() {
  [root(), profilesDir()].forEach(function (dir) {
    if (!fs.existsSync(dir)) { fs.mkdirSync(dir, { recursive: true }); }
  });
}

// ── pairing ──────────────────────────────────────────────────

function newSecret() { return crypto.randomBytes(32).toString('hex'); }

function newPin() {
  // Six digits, read off a screen and typed on a phone. randomInt is
  // uniform; taking a modulus of random bytes is not.
  return String(crypto.randomInt(0, 1000000)).padStart(6, '0');
}

// ── settings ─────────────────────────────────────────────────

function defaults() {
  return {
    schema: SCHEMA,
    pairing: { secret: newSecret(), pin: newPin() },
    activeProfile: null,
    autoLoad: true
  };
}

function readSettings() {
  ensure();
  var file = settingsPath();
  if (!fs.existsSync(file)) {
    var fresh = defaults();
    writeSettings(fresh);
    return fresh;
  }
  try {
    var got = JSON.parse(fs.readFileSync(file, 'utf8'));
    // A settings file that lost its secret would silently unlock the
    // machine to anyone on the network, so it is repaired, not trusted.
    if (!got.pairing || !got.pairing.secret) {
      got.pairing = { secret: newSecret(), pin: newPin() };
      writeSettings(got);
    }
    if (!got.pairing.pin) { got.pairing.pin = newPin(); writeSettings(got); }
    return got;
  } catch (e) {
    // A corrupt settings file must not stop the app starting. The old one
    // is kept, because it is the only copy of a secret phones are using.
    try { fs.renameSync(file, file + '.broken'); } catch (e2) { /* best effort */ }
    var replacement = defaults();
    writeSettings(replacement);
    return replacement;
  }
}

function writeSettings(obj) {
  ensure();
  writeAtomic(settingsPath(), JSON.stringify(obj, null, 1) + '\n');
}

// ── profiles ─────────────────────────────────────────────────

function safeName(name) {
  // A profile name reaches the filesystem, so it cannot carry separators
  // or traversal. Everything else about it is the user's business.
  return String(name || 'Untitled')
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, " ")
    .replace(/\.+$/, '')
    .trim()
    .slice(0, 64) || 'Untitled';
}

function blank(name) {
  return {
    schema: SCHEMA,
    name: name || 'Untitled',
    pages: [{ name: 'Page 1', cols: 12, rows: 21, keys: [] }]
  };
}

function upgrade(doc, fallbackName) {
  // A bare board - cols, rows, keys - is what the dashboard wrote before
  // profiles existed and what the Python package still writes. Reading it
  // as a one page profile means neither has to change to be useful here.
  if (!doc || typeof doc !== 'object') { return null; }
  if (Array.isArray(doc.pages)) {
    doc.schema = doc.schema || SCHEMA;
    doc.name = doc.name || fallbackName || 'Untitled';
    // Optional: the programs this profile belongs to. Kept as written so
    // somebody editing the file by hand is not second-guessed.
    if (doc.match && !Array.isArray(doc.match)) { doc.match = [String(doc.match)]; }
    return doc;
  }
  if (Array.isArray(doc.keys)) {
    return {
      schema: SCHEMA,
      name: doc.name || fallbackName || 'Untitled',
      pages: [{
        name: 'Page 1',
        cols: doc.cols || 12, rows: doc.rows || 21,
        keys: doc.keys
      }]
    };
  }
  return null;
}

function listProfiles() {
  ensure();
  return fs.readdirSync(profilesDir())
    .filter(function (f) { return /\.json$/i.test(f); })
    .map(function (f) {
      var full = path.join(profilesDir(), f);
      try {
        var doc = upgrade(JSON.parse(fs.readFileSync(full, 'utf8')),
                          path.basename(f, '.json'));
        if (!doc) { return null; }
        return {
          file: f,
          name: doc.name,
          pages: doc.pages.length,
          keys: doc.pages.reduce(function (n, p) {
            return n + (p.keys ? p.keys.length : 0); }, 0)
        };
      } catch (e) {
        // One unreadable file must not hide every other profile.
        return { file: f, name: path.basename(f, '.json'),
                 pages: 0, keys: 0, unreadable: true };
      }
    })
    .filter(Boolean);
}

function loadProfile(file) {
  var full = path.join(profilesDir(), path.basename(String(file)));
  if (!fs.existsSync(full)) { return null; }
  try {
    return upgrade(JSON.parse(fs.readFileSync(full, 'utf8')),
                   path.basename(full, '.json'));
  } catch (e) { return null; }
}

function saveProfile(doc) {
  ensure();
  var out = upgrade(doc) || blank();
  out.schema = SCHEMA;
  var file = safeName(out.name) + '.json';
  writeAtomic(path.join(profilesDir(), file),
              JSON.stringify(out, null, 1) + '\n');
  return file;
}

function deleteProfile(file) {
  var full = path.join(profilesDir(), path.basename(String(file)));
  if (fs.existsSync(full)) { fs.unlinkSync(full); return true; }
  return false;
}

// ── writing ──────────────────────────────────────────────────

function writeAtomic(file, text) {
  // Losing a profile to a crash mid-write is the exact failure this whole
  // module exists to prevent, so the real file is only ever replaced by a
  // complete one.
  var tmp = file + '.tmp';
  fs.writeFileSync(tmp, text, 'utf8');
  fs.renameSync(tmp, file);
}

module.exports = {
  SCHEMA: SCHEMA,
  root: root, profilesDir: profilesDir,
  readSettings: readSettings, writeSettings: writeSettings,
  newPin: newPin, newSecret: newSecret,
  listProfiles: listProfiles, loadProfile: loadProfile,
  saveProfile: saveProfile, deleteProfile: deleteProfile,
  blank: blank, upgrade: upgrade, safeName: safeName
};
