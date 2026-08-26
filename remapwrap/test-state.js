/* ============================================================
   test-state — the phone is told the truth, unprompted
   F-Keys | www.f-keys.com
   Run with the server up:  node test-state.js
   ============================================================ */
var WebSocket = require('ws'); var store = require('./store');
var fail = []; function ok(n,c){ if(!c){fail.push(n);}
  console.log('  '+(c?'ok  ':'FAIL')+'  '+n); }

var tok = store.readSettings().pairing.secret;
var ws = new WebSocket('ws://127.0.0.1:7332');
var states = [];
var timer = setTimeout(finish, 6000);

ws.on('open', function(){
  ws.send(JSON.stringify({type:'register',role:'controller',token:tok}));
});
ws.on('message', function(raw){
  var m={}; try{m=JSON.parse(raw);}catch(e){}
  if (m.type === 'state') { states.push(m.state); }
});

function finish(){
  clearTimeout(timer);
  ok('the phone was sent state without asking', states.length >= 1);
  var s = states[0] || {};
  ok('it carries the master volume',
     typeof s['audio.master'] === 'number' && s['audio.master'] >= 0 && s['audio.master'] <= 100);
  ok('it carries the mic gain',
     typeof s['audio.mic.gain'] === 'number');
  ok('it carries the mute state', typeof s['audio.mic.mute'] === 'boolean');
  ok('desktop mirrors master', s['audio.desktop'] === s['audio.master']);
  // The window title never leaves this machine. It is read for the profile
  // watcher and carries document names, email subjects and client names.
  ok('the phone is not told what window is in front',
     s.foreground === undefined);
  // Unchanged state must not be repeated twice a second for six seconds.
  ok('an unchanging machine is not spammed', states.length <= 3);
  // Levels belong to the meters channel. If one appears here the settings
  // message changes on every poll and the guard above stops meaning
  // anything - which is exactly how it broke.
  ok('a level never rides the settings message',
     s.peakIn === undefined && s.peakOut === undefined);
  console.log('  received ' + states.length + ' update(s) in 6s: ' +
              JSON.stringify(states[0]));
  console.log('  ---'); console.log('  '+(fail.length?fail.length+' FAILED':'all pass'));
  try{ws.close();}catch(e){}
  process.exit(fail.length?1:0);
}
