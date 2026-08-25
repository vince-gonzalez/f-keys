/* ============================================================
   test-keymap — every key a person might bind must resolve
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   The map used to be transcribed by hand and quietly missed
   INSERT and =, which are the first two things somebody binding
   office shortcuts reaches for. This reads the shipped source
   and exercises the real table, without pressing anything.

   Run:  node test-keymap.js
   ============================================================ */
var fs = require('fs');
var nut = require('@nut-tree-fork/nut-js');
var Key = nut.Key;
var log = function () {};                       // the source calls log() on a miss

var src = fs.readFileSync(__dirname + '/remapwrap-server.js', 'utf8');
var block = src.slice(src.indexOf('var KEYS = (function'),
                      src.indexOf('/* ===== LAST STABLE'));
eval(block);                                    // exercises what ships, not a copy

var MUST = [
  ['ctrl+c', 2], ['ctrl+v', 2], ['insert', 1], ['=', 1], ['ctrl+=', 2],
  ['ctrl++', 2], ['+', 1], ['-', 1], ['ctrl+shift+m', 3], ['f13', 1],
  ['numpad0', 1], ['printscreen', 1], ['capslock', 1], ['ralt', 1],
  ['pgup', 1], ['[', 1], [']', 1], [';', 1], ["'", 1], [',', 1], ['.', 1],
  ['/', 1], ['`', 1], ['win+shift+s', 3], ['volumeup', 1], ['playpause', 1],
  ['ctrl+alt+delete', 3], ['menu', 1], ['numpadplus', 1], ['esc', 1]
];

var failed = [];
MUST.forEach(function (pair) {
  var combo = pair[0], want = pair[1];
  var keys = parseCombo(combo).map(resolveKey);
  var got = keys.filter(function (k) { return k !== null && k !== undefined; }).length;
  if (got !== want) { failed.push(combo + ': resolved ' + got + ' of ' + want); }
});

var total = Object.keys(KEYS).length;
console.log('  ' + total + ' tokens in the map');
console.log('  ' + MUST.length + ' bindings tested');
if (failed.length) {
  failed.forEach(function (f) { console.log('  FAIL  ' + f); });
  process.exit(1);
}
console.log('  every binding resolves');
