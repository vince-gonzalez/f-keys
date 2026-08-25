/* ============================================================
   system — the commands that are not sound
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   The catalogue listed twenty six commands and ten of them did
   something. The rest logged "No handler yet" while the Python
   package cheerfully validated them as real, so a generated
   board could be full of buttons that did nothing.

   This closes the ones Windows can actually do on its own:

     win.text        type a string - an address, a canned reply
     win.launch      start a program or open a file
     win.desktop     move between virtual desktops
     win.media       play, pause, next, previous
     capture.clip    Game Bar: save the last thirty seconds
     capture.shot    Game Bar: screenshot
     capture.window  the Snipping Tool region grab
     macro.sequence  several of the above, in order

   What is still not here is honest about why: obs.* needs an
   obs-websocket connection and stream.* needs a Twitch token.
   Both are integrations rather than commands, and neither is
   pretended at.
   ============================================================ */

var child = require('child_process');

// Game Bar and the Snipping Tool are reached by the shortcuts Windows
// itself assigns. There is no API for them, and inventing one would mean
// shipping a second capture stack nobody asked for.
var AS_KEYSTROKE = {
  'capture.clip':   'win+alt+g',
  'capture.shot':   'win+alt+printscreen',
  'capture.window': 'win+shift+s',
  'win.desktop':    { left: 'ctrl+win+left', right: 'ctrl+win+right' },
  'win.media':      { play: 'playpause', next: 'next', prev: 'prev',
                      previous: 'prev', stop: 'stop' }
};

var HANDLED = ['win.text', 'win.launch', 'win.desktop', 'win.media',
               'capture.clip', 'capture.shot', 'capture.window',
               'macro.sequence', 'speak.text', 'speak.stop',
               'mouse.click', 'mouse.move', 'mouse.scroll', 'mouse.hold',
               'clip.copy', 'clip.cut', 'clip.paste', 'clip.set',
               'clip.phrase'];

function handles(command) { return HANDLED.indexOf(command) !== -1; }

/**
 * Run one command.
 *   fire(combo)  presses a key combination, supplied by the server
 *   log(msg)     where to say what went wrong
 * Returns a promise of { ok, result }.
 */
function apply(msg, fire, log) {
  var command = msg.command;
  var arg = msg.arg === undefined ? '' : String(msg.arg);

  // Speech is why a board of keys can be a way of talking rather than only
  // a way of pressing things. A person who cannot speak, or cannot type
  // fast enough to be part of a conversation, presses a key and the
  // computer says the sentence.
  if (command === 'speak.text') {
    if (!arg) { return done(false, 'nothing to say'); }
    return fire.speak(arg)
      .then(function () { return done(true, 'said ' + arg.length + ' characters'); })
      .catch(function (e) { return done(false, e.message); });
  }
  if (command === 'speak.stop') {
    return fire.speakStop().then(function () { return done(true, 'stopped'); })
      .catch(function (e) { return done(false, e.message); });
  }

  // ── The pointer ────────────────────────────────────────────
  // nut-js has had a mouse since the first build and nothing ever asked it
  // for anything. Four keys that move the pointer in steps are how somebody
  // who cannot hold a mouse still uses one, and they are useful to anybody
  // whose hands are busy.
  if (command === 'mouse.click') {
    var which = arg.toLowerCase() || 'left';
    return fire.mouseClick(which)
      .then(function () { return done(true, which + ' click'); })
      .catch(function (e) { return done(false, e.message); });
  }

  if (command === 'mouse.move') {
    // "0,-40" - relative, because absolute coordinates mean nothing on a
    // machine whose screen is not the one the layout was written on.
    var parts = arg.split(',').map(function (n) { return parseInt(n.trim(), 10); });
    var dx = isFinite(parts[0]) ? parts[0] : 0;
    var dy = isFinite(parts[1]) ? parts[1] : 0;
    if (!dx && !dy) { return done(false, 'nowhere to move'); }
    return fire.mouseMove(dx, dy)
      .then(function () { return done(true, 'moved ' + dx + ',' + dy); })
      .catch(function (e) { return done(false, e.message); });
  }

  if (command === 'mouse.scroll') {
    var bits = arg.toLowerCase().split(/\s+/);
    var dir = bits[0] || 'down';
    var amount = parseInt(bits[1], 10);
    if (!isFinite(amount) || amount < 1) { amount = 3; }
    return fire.mouseScroll(dir, amount)
      .then(function () { return done(true, dir + ' ' + amount); })
      .catch(function (e) { return done(false, e.message); });
  }

  if (command === 'mouse.hold') {
    // A toggle rather than a press. Holding a physical button down while
    // moving is exactly the movement somebody using this cannot make, so
    // dragging becomes: press to grip, move, press to let go.
    var down = (msg.state === true || msg.down === true);
    return fire.mouseHold(down)
      .then(function () { return done(true, down ? 'gripped' : 'released'); })
      .catch(function (e) { return done(false, e.message); });
  }

  // ── The clipboard ──────────────────────────────────────────
  // copy, cut and paste are keystrokes and could be bound as such, but
  // somebody building a board should not have to know that ctrl+c is copy.
  // Naming the thing they want is the whole point of a catalogue.
  if (command === 'clip.copy') {
    return Promise.resolve(fire.combo('ctrl+c')).then(function () {
      return done(true, 'copied'); });
  }
  if (command === 'clip.cut') {
    return Promise.resolve(fire.combo('ctrl+x')).then(function () {
      return done(true, 'cut'); });
  }
  if (command === 'clip.paste') {
    return Promise.resolve(fire.combo('ctrl+v')).then(function () {
      return done(true, 'pasted'); });
  }
  if (command === 'clip.set') {
    return fire.clipSet(arg)
      .then(function () {
        return done(true, arg ? 'copied ' + arg.length + ' characters'
                              : 'clipboard cleared'); })
      .catch(function (e) { return done(false, e.message); });
  }
  if (command === 'clip.phrase') {
    // The reliable way to put a sentence into another program. win.text
    // types it key by key, which mangles anything outside a US layout and
    // cannot produce an emoji at all. This puts it on the clipboard and
    // pastes, so what arrives is what was written.
    if (!arg) { return done(false, 'nothing to insert'); }
    return fire.clipSet(arg)
      .then(function () { return fire.combo('ctrl+v'); })
      .then(function () { return done(true, 'inserted ' + arg.length + ' characters'); })
      .catch(function (e) { return done(false, e.message); });
  }

  if (command === 'win.text') {
    if (!arg) { return done(false, 'nothing to type'); }
    // Typed rather than pressed: this is a string, not a shortcut, and
    // resolving it key by key would mangle anything outside US layout.
    return Promise.resolve(fire.type(arg))
      .then(function () { return done(true, 'typed ' + arg.length + ' characters'); })
      .catch(function (e) { return done(false, e.message); });
  }

  if (command === 'win.launch') {
    if (!arg) { return done(false, 'nothing to launch'); }
    try {
      // Handed to the shell rather than exec'd, so "spotify", a path, and
      // a URL all behave the way they do in the Run box. The argument
      // comes from a layout on this machine, not from the network.
      child.spawn('cmd', ['/c', 'start', '', arg],
                  { detached: true, stdio: 'ignore', windowsHide: true }).unref();
      return done(true, 'launched ' + arg);
    } catch (e) { return done(false, e.message); }
  }

  if (command === 'win.desktop') {
    var dir = AS_KEYSTROKE['win.desktop'][arg.toLowerCase()] ||
              AS_KEYSTROKE['win.desktop'].right;
    return Promise.resolve(fire.combo(dir)).then(function () {
      return done(true, dir); });
  }

  if (command === 'win.media') {
    var media = AS_KEYSTROKE['win.media'][arg.toLowerCase()] ||
                AS_KEYSTROKE['win.media'].play;
    return Promise.resolve(fire.combo(media)).then(function () {
      return done(true, media); });
  }

  if (AS_KEYSTROKE[command] && typeof AS_KEYSTROKE[command] === 'string') {
    var combo = AS_KEYSTROKE[command];
    return Promise.resolve(fire.combo(combo)).then(function () {
      return done(true, combo); });
  }

  if (command === 'macro.sequence') {
    // "ctrl+c, 250, ctrl+v" - combinations and pauses in milliseconds.
    var steps = arg.split(',').map(function (t) { return t.trim(); })
                   .filter(Boolean);
    if (!steps.length) { return done(false, 'an empty sequence'); }
    var chain = Promise.resolve();
    steps.forEach(function (step) {
      chain = chain.then(function () {
        if (/^[0-9]+$/.test(step)) {
          return new Promise(function (r) { setTimeout(r, Math.min(5000, Number(step))); });
        }
        return fire.combo(step);
      });
    });
    return chain.then(function () { return done(true, steps.length + ' steps'); })
                .catch(function (e) { return done(false, e.message); });
  }

  return done(false, 'not a system command');
}

function done(ok, result) { return Promise.resolve({ ok: ok, result: result }); }

module.exports = { handles: handles, apply: apply, HANDLED: HANDLED };
