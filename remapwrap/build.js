#!/usr/bin/env node
/* ============================================================
   build — RemapWrap as something you double-click
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   Produces dist/RemapWrap/, which contains node.exe, the app,
   and a native RemapWrap.exe with a tray icon. Nothing has to
   be installed to run it and nothing has to be installed to
   build it: the C# compiler used here ships inside Windows.

     node build.js

   The result is a folder that can be zipped, or fed to an
   installer. It is deliberately not a single file: nut-js
   carries native binaries that have to sit on disk to be
   loaded, and pretending otherwise produces an executable that
   works on the machine that built it and nowhere else.
   ============================================================ */

var fs = require('fs');
var path = require('path');
var child = require('child_process');

var ROOT = __dirname;
var OUT = path.join(ROOT, 'dist', 'RemapWrap');
var APP = path.join(OUT, 'app');

// Built from the environment rather than written out, because a literal
// Windows path is one stray backslash away from silently pointing nowhere.
var CSC = path.join(process.env.SystemRoot || 'C:' + path.sep + 'Windows',
                    'Microsoft.NET', 'Framework64', 'v4.0.30319', 'csc.exe');

// Everything the server opens at runtime. Listed rather than globbed so a
// stray note or a test never ends up in what a customer downloads.
var FILES = [
  'remapwrap-server.js', 'audio.js', 'audio-host.ps1', 'store.js',
  'licence.js', 'system.js',
  'dashboard.html', 'controller.html', 'index.html',
  'manifest.webmanifest', 'package.json'
];

var DEPS = ['ws', 'qrcode', '@nut-tree-fork'];

// nut-js can also match images on screen, which drags in jimp and a whole
// image pipeline. RemapWrap presses keys and never looks at the screen, so
// twenty four megabytes of it went into every download for nothing.
// Verified by pruning and reloading: 137 key constants, all present.
var NEVER_LOADED = ['@types', '@jimp', 'jimp', 'gifwrap', 'pixelmatch',
                    'image-q', '@tokenizer', 'file-type'];

function say(m) { console.log('  ' + m); }

function copyDir(from, to) {
  fs.mkdirSync(to, { recursive: true });
  fs.readdirSync(from).forEach(function (entry) {
    var a = path.join(from, entry), b = path.join(to, entry);
    var st = fs.statSync(a);
    if (st.isDirectory()) { copyDir(a, b); } else { fs.copyFileSync(a, b); }
  });
}

function measure(dir) {
  var total = 0, count = 0;
  (function walk(d) {
    fs.readdirSync(d).forEach(function (e) {
      var p = path.join(d, e), st = fs.statSync(p);
      if (st.isDirectory()) { walk(p); } else { total += st.size; count++; }
    });
  })(dir);
  return { bytes: total, files: count };
}

// ── start clean ───────────────────────────────────────────────
if (fs.existsSync(OUT)) { fs.rmSync(OUT, { recursive: true, force: true }); }
fs.mkdirSync(APP, { recursive: true });

// ── the app ───────────────────────────────────────────────────
FILES.forEach(function (f) {
  var src = path.join(ROOT, f);
  if (!fs.existsSync(src)) { throw new Error('missing: ' + f); }
  fs.copyFileSync(src, path.join(APP, f));
});
copyDir(path.join(ROOT, 'assets'), path.join(APP, 'assets'));
if (fs.existsSync(path.join(ROOT, 'sounds'))) {
  copyDir(path.join(ROOT, 'sounds'), path.join(APP, 'sounds'));
}
say(FILES.length + ' app files + assets');

// ── only the dependencies that ship ───────────────────────────
// Copying node_modules wholesale meant 36MB of build tooling, most of it
// never loaded at runtime. These three are what require() reaches for.
DEPS.forEach(function (d) {
  var from = path.join(ROOT, 'node_modules', d);
  if (!fs.existsSync(from)) { throw new Error('dependency not installed: ' + d); }
  copyDir(from, path.join(APP, 'node_modules', d));
});
NEVER_LOADED.forEach(function (d) {
  var gone = path.join(APP, 'node_modules', d);
  if (fs.existsSync(gone)) { fs.rmSync(gone, { recursive: true, force: true }); }
});
// ws and qrcode pull a handful of their own; walk what they declare.
(function pullTransitive() {
  var seen = {};
  function follow(name) {
    if (seen[name]) { return; }
    seen[name] = true;
    var dir = path.join(ROOT, 'node_modules', name);
    var pkg = path.join(dir, 'package.json');
    if (!fs.existsSync(pkg)) { return; }
    if (NEVER_LOADED.some(function (skip) {
      return name === skip || name.indexOf(skip + '/') === 0;
    })) { return; }
    var dest = path.join(APP, 'node_modules', name);
    if (!fs.existsSync(dest)) { copyDir(dir, dest); }
    var deps = {};
    try { deps = JSON.parse(fs.readFileSync(pkg, 'utf8')).dependencies || {}; }
    catch (e) { deps = {}; }
    Object.keys(deps).forEach(follow);
  }
  DEPS.forEach(function (d) {
    if (d.charAt(0) === '@') {
      fs.readdirSync(path.join(ROOT, 'node_modules', d)).forEach(function (sub) {
        follow(d + '/' + sub);
      });
    } else { follow(d); }
  });
  say(Object.keys(seen).length + ' packages, dependencies included');
})();

// ── the runtime ───────────────────────────────────────────────
fs.copyFileSync(process.execPath, path.join(OUT, 'node.exe'));
say('node.exe ' + process.version + ' bundled');

// ── the launcher ──────────────────────────────────────────────
if (!fs.existsSync(CSC)) {
  throw new Error('No C# compiler at ' + CSC +
                  ' - this is normally part of Windows.');
}
var icon = path.join(ROOT, 'assets', 'icon.ico');
var args = [
  '/nologo', '/target:winexe', '/optimize+',
  '/out:' + path.join(OUT, 'RemapWrap.exe'),
  '/reference:System.dll', '/reference:System.Drawing.dll',
  '/reference:System.Windows.Forms.dll'
];
if (fs.existsSync(icon)) { args.push('/win32icon:' + icon); }
args.push(path.join(ROOT, 'launcher', 'RemapWrap.cs'));

var built = child.spawnSync(CSC, args, { encoding: 'utf8' });
if (built.status !== 0) {
  console.log(built.stdout || '');
  console.log(built.stderr || '');
  throw new Error('the launcher did not compile');
}
say('RemapWrap.exe compiled');

// ── does what came out actually work ──────────────────────────
// Pruning dependencies is only safe if the result still loads, and the
// place to find out is here rather than on a customer's machine.
var check = child.spawnSync(path.join(OUT, 'node.exe'),
  ['-e', "var n=require('@nut-tree-fork/nut-js');" +
         "require('./store');require('./licence');require('./system');" +
         "require('ws');require('qrcode');" +
         "if(typeof n.keyboard.pressKey!=='function')process.exit(1);" +
         "console.log(Object.keys(n.Key).filter(function(k){return isNaN(Number(k))}).length)"],
  { cwd: APP, encoding: 'utf8' });
if (check.status !== 0) {
  console.log(check.stdout || ''); console.log(check.stderr || '');
  throw new Error('the built app does not load - do not ship this');
}
say('built app loads: ' + String(check.stdout).trim() + ' key constants');

// ── what came out ─────────────────────────────────────────────
var m = measure(OUT);
say('---');
say('dist/RemapWrap/  ' + m.files + ' files, ' +
    (m.bytes / 1048576).toFixed(1) + ' MB');
say('run it by double-clicking RemapWrap.exe - nothing to install');
