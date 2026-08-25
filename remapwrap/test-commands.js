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
