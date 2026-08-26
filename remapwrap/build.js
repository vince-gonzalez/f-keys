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
var os = require('os');

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

// nut-js can also match images on screen, and it requires that machinery at
// load time whether or not anything asks for it. Pruning jimp looked fine
// for a whole day because Node walked UP out of dist/ and found the
// development node_modules - the build's own check passed for the same
// reason and proved nothing. The moment the installer put the app somewhere
// with no parent to fall back on, it could not start at all.
//
// So only what is genuinely never reached is removed. TypeScript
// definitions are the whole list.
var NEVER_LOADED = ['@types'];

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
// Before the payload is packed, or the copy inside the installer is the
// unsigned one and only the installer itself would carry a signature.
sign([path.join(OUT, 'RemapWrap.exe')]);

// ── does what came out actually work ──────────────────────────
// Pruning dependencies is only safe if the result still loads, and the
// place to find out is here rather than on a customer's machine.
// Run from a copy OUTSIDE this repository. Checking it in place lets Node
// resolve anything missing from the development tree above it, which is
// exactly how a broken build passed this check for a day.
var proving = path.join(os.tmpdir(), 'rw-prove-' + process.pid);
fs.rmSync(proving, { recursive: true, force: true });
copyDir(OUT, proving);
var check = child.spawnSync(path.join(proving, 'node.exe'),
  ['-e', "var n=require('@nut-tree-fork/nut-js');" +
         "require('./store');require('./licence');require('./system');" +
         "require('ws');require('qrcode');" +
         "if(typeof n.keyboard.pressKey!=='function')process.exit(1);" +
         "console.log(Object.keys(n.Key).filter(function(k){return isNaN(Number(k))}).length)"],
  { cwd: path.join(proving, 'app'), encoding: 'utf8' });
fs.rmSync(proving, { recursive: true, force: true });
if (check.status !== 0) {
  console.log(check.stdout || ''); console.log(check.stderr || '');
  throw new Error('the built app does not load on its own - do not ship this');
}
say('built app loads: ' + String(check.stdout).trim() + ' key constants');

// ── Signing ───────────────────────────────────────────────────
// Windows 11's Smart App Control blocks unsigned executables outright, and
// a keystroke injector is the exact shape of thing SmartScreen exists to
// warn about, so this is not optional for anything a stranger downloads.
//
// What signing does NOT do, and it is worth being straight about: it does
// not remove the first-run warning. Microsoft's own guidance says an EV
// certificate stopped bypassing SmartScreen years ago and paying the
// premium for that reason is no longer justified. What it buys is the
// publisher name in the dialog instead of "Unknown publisher", and
// reputation that accumulates on the certificate and carries to the next
// version rather than starting from nothing every release.
//
// Configured by a file that is NOT in this repository:
//
//   %APPDATA%\RemapWrap\signing.json
//   { "endpoint": "https://wus2.codesigning.azure.net",
//     "account":  "fkeys",
//     "profile":  "remapwrap" }
//
// Until that file exists this is a no-op that says so. It never fails the
// build - an unsigned local build is the normal case while developing -
// but it never pretends either.
function signingConfig() {
  var where = path.join(process.env.APPDATA || os.tmpdir(),
                        'RemapWrap', 'signing.json');
  if (!fs.existsSync(where)) { return null; }
  try {
    var cfg = JSON.parse(fs.readFileSync(where, 'utf8'));
    if (!cfg.endpoint || !cfg.account || !cfg.profile) {
      say('signing.json is missing endpoint, account or profile - not signing');
      return null;
    }
    cfg._from = where;
    return cfg;
  } catch (e) {
    say('signing.json could not be read (' + e.message + ') - not signing');
    return null;
  }
}

function findSigntool() {
  // The newest one wins. Older signtool builds predate the /v2 dlib flag
  // this needs.
  var base = path.join(process.env['ProgramFiles(x86)'] ||
                       'C:' + path.sep + 'Program Files (x86)',
                       'Windows Kits', '10', 'bin');
  if (!fs.existsSync(base)) { return null; }
  var found = [];
  fs.readdirSync(base).forEach(function (v) {
    var candidate = path.join(base, v, 'x64', 'signtool.exe');
    if (fs.existsSync(candidate)) { found.push({ v: v, p: candidate }); }
  });
  if (!found.length) { return null; }
  found.sort(function (a, b) { return a.v < b.v ? 1 : -1; });
  return found[0].p;
}

function sign(files) {
  var cfg = signingConfig();
  if (!cfg) {
    say('not signed - no signing.json, see SIGNING.md');
    return false;
  }
  var signtool = findSigntool();
  if (!signtool) {
    say('not signed - no signtool.exe; install the Windows SDK signing tools');
    return false;
  }
  var dlib = path.join(ROOT, 'signing', 'Azure.CodeSigning.Dlib.dll');
  if (!fs.existsSync(dlib)) {
    say('not signed - the Azure signing library is not in signing/, see SIGNING.md');
    return false;
  }

  // The metadata signtool hands to the library.
  var meta = path.join(ROOT, 'dist', 'signing-metadata.json');
  fs.writeFileSync(meta, JSON.stringify({
    Endpoint: cfg.endpoint,
    CodeSigningAccountName: cfg.account,
    CertificateProfileName: cfg.profile
  }, null, 1));

  var allOk = true;
  files.forEach(function (file) {
    var run = child.spawnSync(signtool, [
      'sign', '/v', '/debug', '/fd', 'SHA256',
      '/tr', 'http://timestamp.acs.microsoft.com',
      '/td', 'SHA256',
      '/dlib', dlib, '/dmdf', meta,
      file
    ], { encoding: 'utf8' });
    if (run.status !== 0) {
      console.log(run.stdout || ''); console.log(run.stderr || '');
      say('SIGNING FAILED for ' + path.basename(file));
      allOk = false;
      return;
    }
    // Signed is not the same as verifiable. Checking is the whole point.
    var check = child.spawnSync(signtool, ['verify', '/pa', '/v', file],
                                { encoding: 'utf8' });
    if (check.status !== 0) {
      console.log(check.stdout || '');
      say('SIGNED BUT DOES NOT VERIFY: ' + path.basename(file));
      allOk = false;
      return;
    }
    say('signed and verified: ' + path.basename(file));
  });
  try { fs.rmSync(meta); } catch (e) { /* nothing depends on it */ }
  return allOk;
}

// ── The installer ─────────────────────────────────────────────
// One file a stranger downloads and double-clicks. The application is
// carried inside it as an embedded resource, so building an installer
// needs no installer-building tool - the same reason the launcher is
// compiled with the C# compiler that ships inside Windows.
//
// installer.iss is still in this repository for the day Inno Setup is on
// the build machine. This exists so that day is not a blocker.
function buildInstaller() {
  var zip = path.join(ROOT, 'dist', 'payload.zip');
  if (fs.existsSync(zip)) { fs.rmSync(zip); }

  // .NET's own zip, through PowerShell, because Compress-Archive is slow on
  // eight hundred files and produces a larger file.
  var ps = "Add-Type -AssemblyName System.IO.Compression.FileSystem; " +
    "[System.IO.Compression.ZipFile]::CreateFromDirectory(" +
    "'" + OUT.replace(/'/g, "''") + "','" + zip.replace(/'/g, "''") + "'," +
    "[System.IO.Compression.CompressionLevel]::Optimal,$false)";
  var packed = child.spawnSync('powershell', ['-NoProfile', '-Command', ps],
                               { encoding: 'utf8' });
  if (packed.status !== 0 || !fs.existsSync(zip)) {
    console.log(packed.stderr || '');
    throw new Error('could not pack the payload');
  }
  say('payload.zip  ' + (fs.statSync(zip).size / 1048576).toFixed(1) + ' MB');

  var setupExe = path.join(ROOT, 'dist', 'RemapWrap-Setup.exe');
  var args = [
    '/nologo', '/target:winexe', '/optimize+',
    '/out:' + setupExe,
    '/reference:System.dll', '/reference:System.Drawing.dll',
    '/reference:System.Windows.Forms.dll',
    '/reference:System.IO.Compression.dll',
    '/reference:System.IO.Compression.FileSystem.dll',
    // Named, because the code asks for it by name rather than by position.
    '/resource:' + zip + ',payload.zip'
  ];
  var icon = path.join(ROOT, 'assets', 'icon.ico');
  if (fs.existsSync(icon)) { args.push('/win32icon:' + icon); }
  args.push(path.join(ROOT, 'installer', 'Setup.cs'));

  var built = child.spawnSync(CSC, args, { encoding: 'utf8' });
  if (built.status !== 0) {
    console.log(built.stdout || ''); console.log(built.stderr || '');
    throw new Error('the installer did not compile');
  }
  fs.rmSync(zip);            // it lives inside the exe now
  sign([setupExe]);
  say('RemapWrap-Setup.exe  ' +
      (fs.statSync(setupExe).size / 1048576).toFixed(1) + ' MB, one file');
}

// ── what came out ─────────────────────────────────────────────
buildInstaller();

var m = measure(OUT);
say('---');
say('dist/RemapWrap/  ' + m.files + ' files, ' +
    (m.bytes / 1048576).toFixed(1) + ' MB');
say('run it by double-clicking RemapWrap.exe - nothing to install');
