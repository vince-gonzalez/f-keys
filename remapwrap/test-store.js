/* ============================================================
   test-store — the folder is the interface, or it is not
   F-Keys | www.f-keys.com
   ============================================================ */
var fs = require('fs');
var path = require('path');
var store = require('./store');
var fail = [];
function ok(name, cond) { if (!cond) { fail.push(name); } 
  console.log('  ' + (cond ? 'ok  ' : 'FAIL') + '  ' + name); }

// 1. settings appear, with a secret and a six digit pin
var s = store.readSettings();
ok('settings has a 64 char secret', /^[0-9a-f]{64}$/.test(s.pairing.secret));
ok('settings has a six digit pin', /^[0-9]{6}$/.test(s.pairing.pin));
ok('settings carry a schema', s.schema === store.SCHEMA);

// 2. a bare board - what the Python package writes - reads as a profile
var fromPackage = JSON.parse(fs.readFileSync(
  process.env.T + '/board.oneline.json', 'utf8'));
var up = store.upgrade(fromPackage, 'Soundboard');
ok('package board upgrades to a profile', up && up.schema === 1);
ok('package board becomes one page', up.pages.length === 1);
ok('package keys survive intact', up.pages[0].keys.length === fromPackage.keys.length);
ok('package board size survives', up.pages[0].cols === fromPackage.cols &&
                                  up.pages[0].rows === fromPackage.rows);

// 3. dropping that file in the folder makes it show up, no import step
var dropped = path.join(store.profilesDir(), 'Dropped In.json');
fs.writeFileSync(dropped, JSON.stringify(fromPackage), 'utf8');
var listed = store.listProfiles().filter(function (p) { return p.file === 'Dropped In.json'; });
ok('a dropped file is listed', listed.length === 1);
ok('it reports its key count', listed[0] && listed[0].keys === fromPackage.keys.length);
ok('it loads back as a profile', (store.loadProfile('Dropped In.json') || {}).schema === 1);

// 4. names that would escape the folder do not
// The property that matters is not "the name contains no dots" - it is
// "the file cannot land outside the profiles folder". Test that.
var escapes = ['../../evil', '..', '...', 'a/../../b', 'C:evil',
               'nul', 'sub' + String.fromCharCode(92) + 'dir'];
ok('no name can escape the profiles folder', escapes.every(function (n) {
  var full = path.resolve(path.join(store.profilesDir(),
                                    store.safeName(n) + '.json'));
  return path.dirname(full) === path.resolve(store.profilesDir());
}));
ok('an empty name still yields a file', store.safeName('') === 'Untitled');

// 5. an unreadable profile does not hide the others
var bad = path.join(store.profilesDir(), 'Broken.json');
fs.writeFileSync(bad, '{ not json', 'utf8');
var all = store.listProfiles();
ok('a corrupt profile is flagged, not fatal',
   all.some(function (p) { return p.file === 'Broken.json' && p.unreadable; }) &&
   all.some(function (p) { return p.file === 'Dropped In.json'; }));

// 6. round trip through save
var saved = store.saveProfile({ name: 'Round Trip', cols: 8, rows: 16, keys: [] });
ok('save writes a named file', saved === 'Round Trip.json');
ok('saved profile has pages', (store.loadProfile(saved) || {}).pages.length === 1);

[dropped, bad, path.join(store.profilesDir(), saved)].forEach(function (f) {
  try { fs.unlinkSync(f); } catch (e) { /* already gone */ } });

console.log('  ---');
console.log('  ' + (fail.length ? fail.length + ' FAILED' : 'all pass') +
            '   store at ' + store.root());
process.exit(fail.length ? 1 : 0);
