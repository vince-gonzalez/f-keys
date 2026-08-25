/* ============================================================
   test-pairing — an unpaired phone must not get a keyboard
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   Before pairing existed, reaching the WebSocket port was the
   entire qualification for typing on this machine. These are the
   cases that must stay closed.

   Run with the server up:  node test-pairing.js
   ============================================================ */
var WebSocket = require('ws');
var http = require('http');
var store = require('./store');

var HTTP = 7331, WS = 7332;
var fail = [];
function ok(name, cond) { if (!cond) { fail.push(name); }
  console.log('  ' + (cond ? 'ok  ' : 'FAIL') + '  ' + name); }

function post(path, body) {
  return new Promise(function (resolve) {
    var data = JSON.stringify(body);
    var req = http.request({ host: '127.0.0.1', port: HTTP, path: path,
      method: 'POST', headers: { 'Content-Type': 'application/json',
                                 'Content-Length': Buffer.byteLength(data) } },
      function (res) {
        var out = '';
        res.on('data', function (c) { out += c; });
        res.on('end', function () {
          var parsed = null; try { parsed = JSON.parse(out); } catch (e) {}
          resolve({ status: res.statusCode, body: parsed });
        });
      });
    req.on('error', function () { resolve({ status: 0, body: null }); });
    req.write(data); req.end();
  });
}

function register(token) {
  return new Promise(function (resolve) {
    var ws = new WebSocket('ws://127.0.0.1:' + WS);
    var settled = false;
    var done = function (v) { if (!settled) { settled = true; try { ws.close(); } catch (e) {} resolve(v); } };
    ws.on('open', function () {
      ws.send(JSON.stringify({ type: 'register', role: 'controller', token: token }));
    });
    ws.on('message', function (raw) {
      var m = {}; try { m = JSON.parse(raw); } catch (e) {}
      if (m.type === 'unpaired') { done('refused'); }
      if (m.type === 'registered') { done('accepted'); }
    });
    ws.on('error', function () { done('error'); });
    setTimeout(function () { done('timeout'); }, 2500);
  });
}

(async function () {
  var real = store.readSettings().pairing;

  ok('no token is refused',        (await register(undefined)) === 'refused');
  ok('an empty token is refused',  (await register('')) === 'refused');
  ok('a wrong token is refused',   (await register('f'.repeat(64))) === 'refused');
  ok('a short token is refused',   (await register('abc')) === 'refused');
  ok('the real secret is accepted',(await register(real.secret)) === 'accepted');

  var bad = await post('/pair', { pin: '000001' === real.pin ? '000002' : '000001' });
  ok('a wrong PIN is rejected', bad.status === 401 && bad.body && bad.body.ok === false);

  var good = await post('/pair', { pin: real.pin });
  ok('the right PIN returns the secret',
     good.status === 200 && good.body && good.body.token === real.secret);

  var paired = await register(good.body && good.body.token);
  ok('the PIN-issued token works', paired === 'accepted');

  // Five wrong tries in a row must close the door on this address.
  var wrong = real.pin === '111111' ? '222222' : '111111';
  var last = null;
  for (var i = 0; i < 6; i++) { last = await post('/pair', { pin: wrong }); }
  ok('repeated wrong PINs lock out', last.status === 429);

  console.log('  ---');
  console.log('  ' + (fail.length ? fail.length + ' FAILED' : 'all pass'));
  process.exit(fail.length ? 1 : 0);
})();
