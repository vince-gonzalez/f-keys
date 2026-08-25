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

var KEY_PATH = process.env.REMAPWRAP_SIGNING_KEY ||
               'C:/tmp/remapwrap-signing/PRIVATE-KEY.txt';
if (!fs.existsSync(KEY_PATH)) {
  console.log('  skipped: no signing key at ' + KEY_PATH); process.exit(0);
}

(async function(){
  await call('POST','/licence/remove');

  // A profile that claims this very window. Whatever is in front while the
  // test runs is what the server will see, so match on it deliberately.
  var mine = { schema:1, name:'Autoswitch Probe', match:['claude','node','cmd','powershell'],
               pages:[{name:'Page 1',cols:8,rows:16,keys:[]}] };
  await call('POST','/profile', mine);
  // saving makes it active, so move off it to prove the switch happens
  var other = { schema:1, name:'Autoswitch Other',
                pages:[{name:'Page 1',cols:8,rows:16,keys:[]}] };
  await call('POST','/profile', other);
  var before = (await call('GET','/profiles')).body.active;
  ok('starting on the other profile', before === 'Autoswitch Other.json');

  await wait(2500);
  var stillFree = (await call('GET','/profiles')).body.active;
  ok('free does not follow the window', stillFree === 'Autoswitch Other.json');

  var t = fs.readFileSync(KEY_PATH,'utf8').trim().split('\n');
  var key = lic.sign({name:'Switch Test',tier:'pro'}, t[t.length-1].trim());
  await call('POST','/licence',{key:key});
  ok('now licensed', (await call('GET','/licence')).body.tier === 'pro');

  await wait(2500);
  var after = (await call('GET','/profiles')).body.active;
  ok('pro switched to the matching profile', after === 'Autoswitch Probe.json');

  // tidy up so the machine is left as it was
  await call('POST','/licence/remove');
  await call('POST','/profile/delete?file=' + encodeURIComponent('Autoswitch Probe.json'));
  await call('POST','/profile/delete?file=' + encodeURIComponent('Autoswitch Other.json'));

  console.log('  ---'); console.log('  '+(fail.length?fail.length+' FAILED':'all pass'));
  process.exit(fail.length?1:0);
})();
