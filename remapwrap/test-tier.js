/* ============================================================
   test-tier — free is generous, paid is what was paid for
   F-Keys | www.f-keys.com
   Run with the server up:  node test-tier.js
   ============================================================ */
var http = require('http'); var WebSocket = require('ws');
var fs = require('fs'); var lic = require('./licence'); var store = require('./store');
var fail = []; function ok(n,c){ if(!c){fail.push(n);} 
  console.log('  '+(c?'ok  ':'FAIL')+'  '+n); }
function call(m,p,b){ return new Promise(function(res){
  var d=b?JSON.stringify(b):null;
  var r=http.request({host:'127.0.0.1',port:7331,path:p,method:m,
    headers:d?{'Content-Type':'application/json','Content-Length':Buffer.byteLength(d)}:{}},
    function(x){var o='';x.on('data',function(c){o+=c;});x.on('end',function(){
      var j=null;try{j=JSON.parse(o);}catch(e){} res({status:x.statusCode,body:j});});});
  r.on('error',function(){res({status:0,body:null});}); if(d){r.write(d);} r.end();});}
function phone(token){ return new Promise(function(res){
  var ws=new WebSocket('ws://127.0.0.1:7332'); var done=false;
  var end=function(v,keep){ if(!done){done=true; if(!keep){try{ws.close();}catch(e){}} res({r:v,ws:ws});} };
  ws.on('open',function(){ws.send(JSON.stringify({type:'register',role:'controller',token:token}));});
  ws.on('message',function(raw){var m={};try{m=JSON.parse(raw);}catch(e){}
    if(m.type==='too_many_devices'){end('full');}
    if(m.type==='registered'){end('in',true);}
    if(m.type==='unpaired'){end('unpaired');}});
  ws.on('error',function(){end('error');});
  setTimeout(function(){end('timeout');},2500);});}

// The signing key lives outside this repository and is not on every
// machine. Without it these cases cannot run, and a test that cannot run
// must say so rather than fail as though the code were broken.
var KEY_PATH = process.env.REMAPWRAP_SIGNING_KEY ||
               'C:/Users/Admin/.remapwrap-signing/PRIVATE-KEY.txt';
if (!fs.existsSync(KEY_PATH)) {
  console.log('  skipped: no signing key at ' + KEY_PATH);
  console.log('  set REMAPWRAP_SIGNING_KEY to run these.');
  process.exit(0);
}

(async function(){
  var tok = store.readSettings().pairing.secret;

  // These cases describe a fresh install, so start from one. This also
  // exercises the path somebody uses when moving a licence to a new PC.
  await call('POST','/licence/remove');

  var free = await call('GET','/licence');
  ok('a fresh install is free', free.body && free.body.tier==='free');
  ok('free reports no auto switch', free.body.features.autoSwitch===false);
  ok('free reports a device ceiling of 2', free.body.features.devices===2);

  // two phones allowed, third refused
  var a = await phone(tok), b = await phone(tok);
  ok('the first phone connects', a.r==='in');
  ok('the second phone connects', b.r==='in');
  var c = await phone(tok);
  ok('the third is refused on free', c.r==='full');
  try{a.ws.close();b.ws.close();}catch(e){}

  var bad = await call('POST','/licence',{key:'not-a-key'});
  ok('a junk key is rejected', bad.status===400);
  ok('and the copy is still free', (await call('GET','/licence')).body.tier==='free');

  var t = fs.readFileSync(KEY_PATH,'utf8').trim().split('\n');
  var key = lic.sign({name:'Tier Test',tier:'pro',issued:'2026-08-25'}, t[t.length-1].trim());
  var up = await call('POST','/licence',{key:key});
  ok('a genuine key is accepted', up.status===200 && up.body.tier==='pro');

  var now = await call('GET','/licence');
  ok('the copy is pro without restarting', now.body.tier==='pro');
  ok('pro has no device ceiling', now.body.features.devices===null);
  ok('pro unlocks auto switching', now.body.features.autoSwitch===true);
  ok('the buyer is named', now.body.name==='Tier Test');

  var d=await phone(tok), e=await phone(tok), f=await phone(tok);
  ok('a third phone connects on pro', f.r==='in');
  try{d.ws.close();e.ws.close();f.ws.close();}catch(err){}

  ok('the licence survives on disk', store.readSettings().licence===key);

  console.log('  ---'); console.log('  '+(fail.length?fail.length+' FAILED':'all pass'));
  process.exit(fail.length?1:0);
})();
