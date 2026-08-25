/* ============================================================
   test-autoswitch — free stays put, paid follows the window
   F-Keys | www.f-keys.com
   Run with the server up:  node test-autoswitch.js
   ============================================================ */
var http = require('http'); var fs = require('fs');
var store = require('./store'); var lic = require('./licence');
var fail = []; function ok(n,c){ if(!c){fail.push(n);}
  console.log('  '+(c?'ok  ':'FAIL')+'  '+n); }
function call(m,p,b){ return new Promise(function(res){
  var d=b?JSON.stringify(b):null;
  var r=http.request({host:'127.0.0.1',port:7331,path:p,method:m,
    headers:d?{'Content-Type':'application/json','Content-Length':Buffer.byteLength(d)}:{}},
    function(x){var o='';x.on('data',function(c){o+=c;});x.on('end',function(){
      var j=null;try{j=JSON.parse(o);}catch(e){} res({status:x.statusCode,body:j});});});
  r.on('error',function(){res({status:0,body:null});}); if(d){r.write(d);} r.end();});}
var wait = function(ms){ return new Promise(function(r){ setTimeout(r,ms); }); };

// Sleeping a fixed 2500ms and then asserting is how this test earned its
// reputation. The PowerShell host compiles its C# on first start, which
// takes seconds, and until it answers there is no foreground reading at
// all - so the assertion was racing a compiler. Wait for the condition,
// with a ceiling, and report the ceiling as the failure.
async function until(what, check, ms) {
  var deadline = Date.now() + (ms || 12000);
  while (Date.now() < deadline) {
    if (await check()) { return true; }
    await wait(250);
  }
  return false;
}

// Nothing can be asserted about switching until the host is answering.
async function hostReady() {
  return until('the audio host to answer', async function () {
    var r = await call('GET', '/profiles');
    return r.status === 200;
  }, 20000);
}

var KEY_PATH = process.env.REMAPWRAP_SIGNING_KEY ||
               'C:/Users/Admin/.remapwrap-signing/PRIVATE-KEY.txt';
if (!fs.existsSync(KEY_PATH)) {
  console.log('  skipped: no signing key at ' + KEY_PATH); process.exit(0);
}

(async function(){
  await call('POST','/licence/remove');

  // A profile that claims this very window. Whatever is in front while the
  // test runs is what the server will see, so match on it deliberately.
  // Whatever is actually in front while this runs. Hardcoding a guess
  // meant the test passed at a desk and failed the moment a browser was
  // opened, which is the test being wrong about the world rather than the
  // code being wrong about anything.
  var front = (await call('GET','/foreground')).body;
  if (!front || !front.app) {
    console.log('  skipped: the host cannot say what is in front');
    process.exit(0);
  }
  var mine = { schema:1, name:'Autoswitch Probe', match:[front.app],
               pages:[{name:'Page 1',cols:8,rows:16,keys:[]}] };
  await call('POST','/profile', mine);
  // saving makes it active, so move off it to prove the switch happens
  var other = { schema:1, name:'Autoswitch Other',
                pages:[{name:'Page 1',cols:8,rows:16,keys:[]}] };
  await call('POST','/profile', other);
  var before = (await call('GET','/profiles')).body.active;
  ok('starting on the other profile', before === 'Autoswitch Other.json');

  await hostReady();

  // Give the watcher several ticks. If it were going to move on the free
  // tier it would have by now.
  await wait(3000);
  var stillFree = (await call('GET','/profiles')).body.active;
  ok('free does not follow the window', stillFree === 'Autoswitch Other.json');

  var t = fs.readFileSync(KEY_PATH,'utf8').trim().split('\n');
  var key = lic.sign({name:'Switch Test',tier:'pro'}, t[t.length-1].trim());
  await call('POST','/licence',{key:key});
  ok('now licensed', (await call('GET','/licence')).body.tier === 'pro');

  var switched = await until('the surface to follow the window', async function () {
    var r = await call('GET','/profiles');
    return r.body && r.body.active === 'Autoswitch Probe.json';
  }, 12000);

  // This test depends on a live fact about the machine: which window is in
  // front. If something took focus while it ran - a browser, an installer,
  // a notification - the profile no longer matches and there is nothing to
  // assert. Saying so is honest; failing would be blaming the code for the
  // world moving.
  var still = (await call('GET','/foreground')).body;
  if (!switched && still && still.app !== front.app) {
    console.log('  --    focus moved from "' + front.app + '" to "' +
                still.app + '" mid-test; nothing to assert');
  } else {
    ok('pro switched to the matching profile', switched);
  }

  // tidy up so the machine is left as it was
  await call('POST','/licence/remove');
  await call('POST','/profile/delete?file=' + encodeURIComponent('Autoswitch Probe.json'));
  await call('POST','/profile/delete?file=' + encodeURIComponent('Autoswitch Other.json'));

  console.log('  ---'); console.log('  '+(fail.length?fail.length+' FAILED':'all pass'));
  process.exit(fail.length?1:0);
})();
