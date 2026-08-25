/* ============================================================
   test-commands — nothing may offer what nothing runs
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   The board this shipped with had five of its twelve keys bound
   to obs.* and stream.*, which nothing executes, so a person's
   first impression of RemapWrap was a surface where half the
   buttons did nothing and no way to tell which half.

   The set of commands that run is derived from the modules that
   run them, not from a list written by hand beside them. A list
   written by hand is how the last one drifted.

   Run:  node test-commands.js
   ============================================================ */
var fs = require('fs');
var path = require('path');
var audio = require('./audio');
var system = require('./system');

var fail = [];
function ok(name, cond, detail) {
  if (!cond) { fail.push(name); }
  console.log('  ' + (cond ? 'ok  ' : 'FAIL') + '  ' + name +
              (detail ? '  ' + detail : ''));
}

// What actually runs: whatever audio claims, whatever system claims, and
// keystrokes, which the server handles itself.
function runs(command) {
  return command === 'win.keystroke' ||
         audio.handles(command) || system.handles(command);
}

var html = fs.readFileSync(path.join(__dirname, 'dashboard.html'), 'utf8');

// ── the board it ships with ───────────────────────────────────
var block = html.slice(html.indexOf('  var layout = ['),
                       html.indexOf('  ];', html.indexOf('  var layout = [')));
var defaults = [];
var re = /command:\s*'([^']+)'/g;
var m;
while ((m = re.exec(block)) !== null) { defaults.push(m[1]); }

var deadDefaults = defaults.filter(function (c) { return !runs(c); });
ok('every key on the default board does something',
   deadDefaults.length === 0,
   deadDefaults.length ? '-> ' + deadDefaults.join(', ')
                       : '(' + defaults.length + ' keys)');

// ── the board it ships with has to fit the board it ships with ─
// The slider added to this default was 3x8 placed at y=11 on a 16 row
// board, so it hung off the bottom - and because applyGridConfig refuses
// any size that would strand a control, that one key jammed the board
// size boxes permanently. Nothing said so.
var geom = [];
var reKey = /\{[^{}]*?id:\s*'([^']+)'[^{}]*?x:\s*(\d+),\s*y:\s*(\d+),\s*w:\s*(\d+),\s*h:\s*(\d+)[^{}]*?\}/g;
while ((m = reKey.exec(block)) !== null) {
  geom.push({ id: m[1], x: +m[2], y: +m[3], w: +m[4], h: +m[5] });
}
var COLS = 24, ROWS = 16;
var offBoard = geom.filter(function (k) {
  return k.x + k.w > COLS || k.y + k.h > ROWS || k.x < 0 || k.y < 0;
});
ok('every default key fits a ' + COLS + 'x' + ROWS + ' board',
   offBoard.length === 0,
   offBoard.length
     ? '-> ' + offBoard.map(function (k) {
         return k.id + ' reaches ' + (k.x + k.w) + ',' + (k.y + k.h); }).join('; ')
     : '(' + geom.length + ' keys)');

var overlapping = [];
for (var a = 0; a < geom.length; a++) {
  for (var bIdx = a + 1; bIdx < geom.length; bIdx++) {
    var p = geom[a], q = geom[bIdx];
    if (p.x < q.x + q.w && p.x + p.w > q.x &&
        p.y < q.y + q.h && p.y + p.h > q.y) {
      overlapping.push(p.id + '/' + q.id);
    }
  }
}
ok('no two default keys overlap', overlapping.length === 0,
   overlapping.length ? '-> ' + overlapping.join(', ') : '');

// ── the phone's own starter board ─────────────────────────────
// controller.html carries a fallback layout so a phone shows something
// before the dashboard pushes anything. It was never checked. It happens
// to be twelve plain keystrokes and it happens to work, and "happens to"
// is not a standard.
var ctl = fs.readFileSync(path.join(__dirname, 'controller.html'), 'utf8');
var fb = ctl.slice(ctl.indexOf('var layout = {'), ctl.indexOf('};', ctl.indexOf('var layout = {')));
var actions = (fb.match(/action:\s*'([^']+)'/g) || [])
  .map(function (x) { return x.replace(/action:\s*'/, '').replace(/'$/, ''); });

// Resolved against the real table in the real server file, the same way
// test-keymap does, rather than a list written here.
var src = fs.readFileSync(path.join(__dirname, 'remapwrap-server.js'), 'utf8');
var Key = require('@nut-tree-fork/nut-js').Key;
var log = function () {};
eval(src.slice(src.indexOf('var KEYS = (function'), src.indexOf('/* ===== LAST STABLE')));

var deadFallback = actions.filter(function (a) {
  return parseCombo(a).some(function (t) { return KEYS[t] === undefined; });
});
ok('every key on the phone starter board resolves',
   deadFallback.length === 0,
   deadFallback.length ? '-> ' + deadFallback.join(', ')
                       : '(' + actions.length + ' keys)');

// ── what the editor offers ────────────────────────────────────
var offered = [];
var re2 = /\['([a-z]+\.[a-z.]+)',\s*'/g;
while ((m = re2.exec(html)) !== null) {
  if (offered.indexOf(m[1]) === -1) { offered.push(m[1]); }
}
var deadOffers = offered.filter(function (c) { return !runs(c); });
ok('every command the editor offers does something',
   deadOffers.length === 0,
   deadOffers.length ? '-> ' + deadOffers.join(', ')
                     : '(' + offered.length + ' offered)');

// ── and the other direction ───────────────────────────────────
// Everything offered must run, which is checked above. The inverse is just
// as important and was missing: a command that runs and that nothing
// exposes is work nobody can reach. speak.text was built, worked, and was
// invisible in both the editor and the package, and this file passed.
var runnable = ['win.keystroke']
  .concat(system.HANDLED)
  .concat(Object.keys(audio.CONTINUOUS || {}))
  .concat(Object.keys(audio.SWITCHED || {}))
  .concat(['sound.play', 'sound.stop', 'audio.mic.ptt']);
runnable = runnable.filter(function (c, i) { return runnable.indexOf(c) === i; });

var unreachable = runnable.filter(function (c) { return offered.indexOf(c) === -1; });
ok('every command that runs is offered somewhere',
   unreachable.length === 0,
   unreachable.length ? '-> ' + unreachable.join(', ')
                      : '(' + runnable.length + ' runnable)');

// ── the Python package must agree ─────────────────────────────
// Two implementations of one catalogue disagree exactly where one of them
// is wrong, which is the whole reason there are two.
var layoutPy = path.join(__dirname, '..', 'remapwrap-cli', 'src',
                         'remapwrap', 'layout.py');
if (fs.existsSync(layoutPy)) {
  var py = fs.readFileSync(layoutPy, 'utf8');
  var pyBlock = py.slice(py.indexOf('COMMANDS = {'), py.indexOf('}', py.indexOf('COMMANDS = {')));
  var pyCommands = (pyBlock.match(/"([a-z]+\.[a-z.]+)"/g) || [])
    .map(function (x) { return x.replace(/"/g, ''); });

  var pyDead = pyCommands.filter(function (c) { return !runs(c); });
  ok('the Python catalogue contains only commands that run',
     pyDead.length === 0,
     pyDead.length ? '-> ' + pyDead.join(', ') : '(' + pyCommands.length + ')');

  var missingFromPy = offered.filter(function (c) {
    return pyCommands.indexOf(c) === -1;
  });
  ok('the editor offers nothing the package rejects',
     missingFromPy.length === 0,
     missingFromPy.length ? '-> ' + missingFromPy.join(', ') : '');
} else {
  console.log('  --    remapwrap-cli not beside this checkout; skipped');
}

console.log('  ---');
console.log('  ' + (fail.length ? fail.length + ' FAILED' : 'all pass'));
process.exit(fail.length ? 1 : 0);
