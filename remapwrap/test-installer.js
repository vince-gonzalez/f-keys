/* ============================================================
   test-installer — the promises the installer makes
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   An installer cannot be unit tested end to end without
   installing something, but the promises it makes are in its
   source and can be held to. The one that matters:

     Uninstalling leaves %APPDATA%\RemapWrap alone.

   For somebody whose communication board lives in that folder,
   deleting it on uninstall would be taking their words away.

   Run:  node test-installer.js
   ============================================================ */
var fs = require('fs');
var path = require('path');
var fail = [];
function ok(n, c, d) { if (!c) { fail.push(n); }
  console.log('  ' + (c ? 'ok  ' : 'FAIL') + '  ' + n + (d ? '  ' + d : '')); }

var src = fs.readFileSync(path.join(__dirname, 'installer', 'Setup.cs'), 'utf8');

// The removal script and every delete must be aimed at the program folder
// and nowhere else.
// LocalApplicationData is where the program goes and is correct. The one
// that must never appear is bare ApplicationData - the roaming folder,
// which is where somebody's boards live. Matching the substring flagged
// the right code as wrong, which is the test being wrong.
var roaming = (src.match(/SpecialFolder\.ApplicationData/g) || []).length;
ok('nothing reaches for the roaming AppData folder, where the boards live',
   roaming === 0,
   roaming ? roaming + ' reference(s)' : '');

ok('the only folder it deletes is the one it installed to',
   /rmdir \/s \/q "\s*\+\s*dir\s*\+\s*"/.test(src) ||
   src.indexOf('rmdir /s /q \\"" + dir + "\\"') !== -1,
   '');

// Per user. Asking for an administrator on a school or library machine is
// where somebody stops installing.
ok('it installs per user, not machine wide',
   src.indexOf('LocalApplicationData') !== -1 &&
   src.indexOf('ProgramFiles') === -1);
ok('and registers under the current user',
   src.indexOf('Registry.CurrentUser') !== -1 &&
   src.indexOf('Registry.LocalMachine') === -1);

// A zip is a file somebody downloaded off the internet.
ok('an archive entry cannot write outside the install folder',
   src.indexOf('StartsWith(Path.GetFullPath(dir)') !== -1);

// Silent means silent. An unhandled exception with no console attached
// raises a dialog nobody can see, and the process waits on it forever -
// which is exactly what happened, twice.
var silentBlock = src.slice(src.indexOf('if (silent) {'));
ok('a silent install cannot raise a dialog',
   /catch \(Exception ex\) \{[\s\S]{0,220}Environment\.Exit\(1\)/.test(silentBlock));
// Sliced to the first line of Main's silent branch rather than the first
// "if (silent) {" anywhere - the uninstall branch contains one of its own,
// so the slice stopped before the catch it was looking for.
var unStart = src.indexOf('if (uninstall) {');
var unEnd = src.indexOf('Application.EnableVisualStyles');
var unBlock = src.slice(unStart, unEnd);
ok('a silent uninstall cannot raise a dialog either',
   /catch \(Exception ex\) \{/.test(unBlock) &&
   /if \(!silent\)/.test(unBlock));

// Cleanup that cannot finish must not stop the thing it was cleaning for.
ok('stopping running copies is time bounded',
   /t\.Join\(\d+\)/.test(src));

ok('uninstall tells the person their boards are kept',
   /boards and your licence key are kept/i.test(src) ||
   /Your boards are still/i.test(src));

console.log('  ---');
console.log('  ' + (fail.length ? fail.length + ' FAILED' : 'all pass'));
process.exit(fail.length ? 1 : 0);
