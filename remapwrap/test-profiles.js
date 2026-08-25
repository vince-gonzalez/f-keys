/* ============================================================
   test-profiles — a board has to be there tomorrow
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   Run with the server up:  node test-profiles.js
   ============================================================ */
var http = require('http');
var fs = require('fs');
var path = require('path');
var store = require('./store');
var fail = [];
function ok(n, c) { if (!c) { fail.push(n); }
  console.log('  ' + (c ? 'ok  ' : 'FAIL') + '  ' + n); }

function call(method, p, body) {
  return new Promise(function (resolve) {
    var data = body ? JSON.stringify(body) : null;
    var req = http.request({ host: '127.0.0.1', port: 7331, path: p, method: method,
      headers: data ? { 'Content-Type': 'application/json',
                        'Content-Length': Buffer.byteLength(data) } : {} },
      function (res) {
        var out = '';
        res.on('data', function (c) { out += c; });
        res.on('end', function () {
          var j = null; try { j = JSON.parse(out); } catch (e) {}
          resolve({ status: res.statusCode, body: j });
        });
      });
    req.on('error', function () { resolve({ status: 0, body: null }); });
    if (data) { req.write(data); }
    req.end();
  });
}

(async function () {
  // A board exactly as the Python package writes one.
  var board = { cols: 12, rows: 21, name: 'Test Deck', keys: [
    { id: 'k1', type: 'key', behaviour: 'press', command: 'win.keystroke',
      arg: 'ctrl+shift+m', label: 'MUTE', sub: 'ctrl+shift+m',
      color: '#2a1216', x: 0, y: 0, w: 4, h: 4, shape: 'rounded' }] };

  var saved = await call('POST', '/profile', board);
  ok('a board saves', saved.status === 200 && saved.body && saved.body.ok);
  var file = saved.body && saved.body.file;
  ok('it is named after the profile', file === 'Test Deck.json');

  var listed = await call('GET', '/profiles');
  ok('it appears in the list', listed.body && listed.body.profiles
     .some(function (x) { return x.file === file; }));
  ok('saving made it active', listed.body && listed.body.active === file);

  var got = await call('GET', '/profile?file=' + encodeURIComponent(file));
  ok('it loads back', got.status === 200 && got.body && got.body.ok);
  ok('the key survived intact',
     got.body.profile.pages[0].keys[0].arg === 'ctrl+shift+m');
  ok('a bare board became one page', got.body.profile.pages.length === 1);

  var act = await call('POST', '/profile/activate?file=' + encodeURIComponent(file));
  ok('it can be activated', act.status === 200 && act.body && act.body.ok);

  var missing = await call('GET', '/profile?file=Nope.json');
  ok('a missing profile is a 404', missing.status === 404);

  // This is the whole point: settings on disk must name it, so the next
  // start finds it without anyone doing anything.
  var onDisk = store.readSettings();
  ok('the active profile is recorded on disk', onDisk.activeProfile === file);
  ok('the file is really there',
     fs.existsSync(path.join(store.profilesDir(), file)));

  var del = await call('POST', '/profile/delete?file=' + encodeURIComponent(file));
  ok('it can be deleted', del.status === 200 && del.body && del.body.ok);
  ok('deleting clears active', store.readSettings().activeProfile === null);

  console.log('  ---');
  console.log('  ' + (fail.length ? fail.length + ' FAILED' : 'all pass'));
  process.exit(fail.length ? 1 : 0);
})();
