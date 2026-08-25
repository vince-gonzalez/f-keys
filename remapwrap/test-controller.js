/* ============================================================
   test-controller — the half nobody tested
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   Ten test files drove the server. controller.html is a
   thousand lines of the code a person actually touches, and
   nothing looked at it. That is backwards: the server fails
   into a log nobody reads, and the phone fails in somebody's
   hand.

   This runs the real page in a real DOM, with a stub for the
   socket, so it can press keys, turn dials, change pages and
   read back what a screen reader would be told - without a
   phone, a server, or a network.

   Run:  node test-controller.js
   ============================================================ */
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var fail = [];
function ok(name, cond, detail) {
  if (!cond) { fail.push(name); }
  console.log('  ' + (cond ? 'ok  ' : 'FAIL') + '  ' + name +
              (detail ? '  ' + detail : ''));
}

// ── the smallest DOM that runs this page ──────────────────────
// jsdom is not a dependency and this package has none. What the
// controller touches is a small, knowable surface, so it is built here
// rather than pulling in a browser to press one button.
function makeDom() {
  var listeners = {};
  function El(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.attributes = {};
    // style is read and written like an object, and setProperty is used
    // for the CSS custom properties that carry the grid size.
    this.style = { setProperty: function (k, v) { this[k] = v; },
                   removeProperty: function (k) { delete this[k]; } };
    this.dataset = {};
    this._text = '';
    this._html = '';
    this.classList = (function (self) {
      var set = [];
      return {
        add: function () { [].forEach.call(arguments, function (c) {
          if (set.indexOf(c) === -1) { set.push(c); } }); },
        remove: function () { [].forEach.call(arguments, function (c) {
          var i = set.indexOf(c); if (i > -1) { set.splice(i, 1); } }); },
        toggle: function (c, on) { on ? this.add(c) : this.remove(c); },
        contains: function (c) { return set.indexOf(c) > -1; },
        _all: set
      };
    })(this);
    this._events = {};
  }
  El.prototype.setAttribute = function (k, v) { this.attributes[k] = String(v); };
  El.prototype.getAttribute = function (k) {
    return Object.prototype.hasOwnProperty.call(this.attributes, k)
      ? this.attributes[k] : null; };
  El.prototype.appendChild = function (c) { this.children.push(c); c.parentNode = this; return c; };
  El.prototype.addEventListener = function (k, fn) {
    (this._events[k] = this._events[k] || []).push(fn); };
  El.prototype.removeEventListener = function () {};
  El.prototype.dispatch = function (k, ev) {
    (this._events[k] || []).forEach(function (fn) { fn(ev || { target: this }); }, this); };
  El.prototype.closest = function (sel) {
    var want = sel.replace(/[\[\].]/g, '').split('=')[0];
    var node = this;
    while (node) {
      if (node.classList && node.classList.contains(sel.replace('.', ''))) { return node; }
      if (node.attributes && node.attributes[want] !== undefined) { return node; }
      node = node.parentNode;
    }
    return null;
  };
  El.prototype.focus = function () {};
  // The page looks inside a control it just built - the dial face, the arc,
  // the reading - so an element has to be able to search its own subtree.
  El.prototype.querySelector = function (sel) {
    var cls = sel.replace(/^\./, '');
    var found = null;
    (function walk(node) {
      if (found) { return; }
      node.children.forEach(function (c) {
        if (found) { return; }
        if (c.classList && c.classList.contains(cls)) { found = c; return; }
        walk(c);
      });
    })(this);
    // innerHTML built the face rather than appendChild, so there is nothing
    // to walk. Returning null is honest: those pieces are not inspectable
    // here, and the tests below assert on attributes rather than on them.
    return found;
  };
  El.prototype.querySelectorAll = function () { return []; };
  Object.defineProperty(El.prototype, 'textContent', {
    get: function () { return this._text; },
    set: function (v) { this._text = String(v); this.children.length = 0; }
  });
  Object.defineProperty(El.prototype, 'innerHTML', {
    get: function () { return this._html; },
    set: function (v) {
      this._html = String(v);
      // Clearing a container detaches what was inside it. Without this the
      // old elements stayed findable, and a lookup by id returned the one
      // from before a re-render rather than the one on screen - which read
      // as the code failing to update when it had updated fine.
      (function detach(node) {
        node.children.forEach(function (c) { c._detached = true; detach(c); });
      })(this);
      this.children.length = 0;
    }
  });
  Object.defineProperty(El.prototype, 'offsetWidth', { get: function () { return 100; } });

  var byId = {};
  var all = [];

  var document = {
    createElement: function (t) { var e = new El(t); all.push(e); return e; },
    getElementById: function (id) { return byId[id] || null; },
    querySelector: function (sel) {
      var m = /\[data-id="([^"]+)"\]/.exec(sel);
      if (m) {
        return all.filter(function (e) {
          return e.dataset.id === m[1] && !e._detached; })[0] || null;
      }
      var p = /\.([\w-]+)\[data-page="(\d+)"\]/.exec(sel);
      if (p) {
        return all.filter(function (e) {
          return e.classList.contains(p[1]) &&
                 e.getAttribute('data-page') === p[2]; })[0] || null;
      }
      return null;
    },
    querySelectorAll: function () { return []; },
    addEventListener: function (k, fn) { (listeners[k] = listeners[k] || []).push(fn); },
    _fire: function (k, ev) { (listeners[k] || []).forEach(function (fn) { fn(ev); }); },
    _register: function (id, el) { byId[id] = el; all.push(el); return el; },
    _all: all
  };
  return { document: document, El: El };
}

// ── pull the page's script out and run it ─────────────────────
var html = fs.readFileSync(path.join(__dirname, 'controller.html'), 'utf8');
var script = html.slice(html.lastIndexOf('<script>') + 8, html.lastIndexOf('</script>'));

var dom = makeDom();
var sent = [];

var sandbox = {
  document: dom.document,
  console: { log: function () {}, error: function () {} },
  navigator: { vibrate: function () { return true; } },
  localStorage: { getItem: function () { return null; }, setItem: function () {} },
  location: { search: '', pathname: '/controller' },
  history: { replaceState: function () {} },
  setTimeout: function (fn) { return 0; },      // nothing here waits
  clearTimeout: function () {},
  setInterval: function () { return 0; },
  clearInterval: function () {},
  fetch: function () { return Promise.resolve({ json: function () {
    return Promise.resolve({ ok: false }); } }); },
  WebSocket: function () { this.readyState = 1; this.send = function () {}; },
  Math: Math, JSON: JSON, Date: Date, Promise: Promise, Object: Object,
  Array: Array, String: String, Number: Number, parseInt: parseInt,
  parseFloat: parseFloat, isNaN: isNaN, isFinite: isFinite, RegExp: RegExp,
  Error: Error, encodeURIComponent: encodeURIComponent
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;

// Every id the page reaches for has to exist before it runs.
['conn-badge', 'key-grid', 'ping-disp', 'page-strip', 'pinScreen', 'pinNote',
 'pinInput', 'pinGo', 'server-ip'].forEach(function (id) {
  var el = dom.document.createElement('div');
  el.setAttribute('id', id);
  dom.document._register(id, el);
});

vm.createContext(sandbox);
try {
  vm.runInContext(script, sandbox, { timeout: 5000 });
} catch (e) {
  console.log('  FAIL  the controller script does not even run: ' + e.message);
  process.exit(1);
}
ok('the controller script runs', true);

// The socket is replaced so presses can be read rather than transmitted.
sandbox.send = function (obj) { sent.push(obj); };

// ── a layout, as the server sends one ─────────────────────────
sandbox.handleMessage({
  type: 'layout',
  pages: 3, page: 0,
  layout: { cols: 12, rows: 12, keys: [
    { id: 'a', type: 'key', command: 'win.keystroke', arg: 'ctrl+c',
      label: 'COPY', sub: 'ctrl+c', x: 0, y: 0, w: 4, h: 4, shape: 'rounded' },
    { id: 'b', type: 'dial', command: 'audio.master', label: 'MASTER',
      x: 4, y: 0, w: 4, h: 4, shape: 'circle', value: 50 },
    { id: 'c', type: 'toggle', command: 'audio.mic.mute', label: 'MUTE',
      x: 8, y: 0, w: 4, h: 4, shape: 'rounded' }
  ]}
});

ok('it takes the page count off the layout', sandbox.pageCount === 3,
   'pageCount=' + sandbox.pageCount);
ok('it takes the current page off the layout', sandbox.pageIndex === 0);

// ── accessibility, read back rather than assumed ──────────────
var built = dom.document._all;
var dial = built.filter(function (e) {
  return e.getAttribute('role') === 'slider'; })[0];
ok('a dial is a slider to a screen reader', !!dial);
ok('and it has a name', dial && /MASTER/.test(dial.getAttribute('aria-label') || ''));
ok('and a value, a floor and a ceiling',
   dial && dial.getAttribute('aria-valuenow') === '50' &&
   dial.getAttribute('aria-valuemin') === '0' &&
   dial.getAttribute('aria-valuemax') === '100');
ok('and it can be reached by keyboard', dial && dial.getAttribute('tabindex') === '0');

var toggle = built.filter(function (e) {
  return e.getAttribute('role') === 'switch'; })[0];
ok('a toggle is a switch, not a button', !!toggle);
ok('and it says whether it is on',
   toggle && toggle.getAttribute('aria-checked') === 'false');

var button = built.filter(function (e) {
  return e.getAttribute('role') === 'button'; })[0];
ok('a key is a button with a name',
   button && /COPY/.test(button.getAttribute('aria-label') || ''));

// ── the dial is operable without a mouse ──────────────────────
var before = sent.length;
dial.dispatch('keydown', { key: 'ArrowUp', preventDefault: function () {} });
var moved = sent.slice(before).filter(function (m) { return m.type === 'value'; });
ok('an arrow key moves the dial', moved.length === 1 && moved[0].value === 51,
   moved.length ? 'sent ' + moved[0].value : 'nothing sent');

dial.dispatch('keydown', { key: 'PageDown', preventDefault: function () {} });
var paged = sent.filter(function (m) { return m.type === 'value'; }).pop();
ok('page down moves it by ten', paged && paged.value === 41,
   paged ? 'sent ' + paged.value : 'nothing sent');

dial.dispatch('keydown', { key: 'Home', preventDefault: function () {} });
var homed = sent.filter(function (m) { return m.type === 'value'; }).pop();
ok('home goes to the floor', homed && homed.value === 0);

dial.dispatch('keydown', { key: 'End', preventDefault: function () {} });
var ended = sent.filter(function (m) { return m.type === 'value'; }).pop();
ok('end goes to the ceiling', ended && ended.value === 100);

ok('the announced value follows the face',
   dial.getAttribute('aria-valuenow') === '100');

// ── the PC's reading wins, except under a thumb ───────────────
sandbox.handleMessage({ type: 'state', state: { 'audio.master': 33 } });
ok('a reading from the PC moves the dial',
   dial.getAttribute('aria-valuenow') === '33');

dial.dataset.holding = '1';
sandbox.handleMessage({ type: 'state', state: { 'audio.master': 77 } });
ok('a dial being turned is left alone',
   dial.getAttribute('aria-valuenow') === '33');
dial.dataset.holding = '0';

// ── pages ─────────────────────────────────────────────────────
var strip = dom.document.getElementById('page-strip');
ok('three pages produce three tabs', strip.children.length === 3,
   strip.children.length + ' tabs');
ok('the strip is shown when there is more than one page', strip.hidden === false);
ok('the current tab says it is selected',
   strip.children[0].getAttribute('aria-selected') === 'true' &&
   strip.children[1].getAttribute('aria-selected') === 'false');

var beforePage = sent.length;
sandbox.goToPage(2);
var pageMsgs = sent.slice(beforePage).filter(function (m) { return m.type === 'page'; });
ok('asking for another page tells the PC',
   pageMsgs.length === 1 && pageMsgs[0].index === 2);
ok('the tab responds without waiting for the PC',
   strip.children[2].getAttribute('aria-selected') === 'true');

sandbox.handleMessage({ type: 'layout', pages: 1, page: 0,
                        layout: { cols: 12, rows: 12, keys: [] } });
ok('one page hides the strip entirely', strip.hidden === true);

// ── a press is confirmed, and says which kind ─────────────────
sandbox.handleMessage({ type: 'layout', pages: 1, page: 0,
  layout: { cols: 12, rows: 12, keys: [
    { id: 'z', type: 'key', command: 'win.keystroke', arg: 'ctrl+c',
      label: 'COPY', x: 0, y: 0, w: 4, h: 4 }]}});
var zEl = dom.document.querySelector('[data-id="z"]');
sandbox.confirmPress('z', true);
ok('a press that ran is confirmed', zEl && zEl.classList.contains('confirmed'));
sandbox.confirmPress('z', false);
ok('a press that ran nothing looks different',
   zEl && zEl.classList.contains('unwired') && !zEl.classList.contains('confirmed'));

// ── Scanning ──────────────────────────────────────────────────
// A board of forty keys swept one at a time costs twenty presses on
// average. Row and column costs about six. For somebody whose every press
// is effortful that is the difference between using this and giving up, so
// the saving is asserted rather than asserted about.
sandbox.handleMessage({
  type: 'layout', pages: 1, page: 0,
  layout: { cols: 12, rows: 12, keys: [
    { id: 'r1a', type: 'key', command: 'clip.copy',  label: 'A', x: 0, y: 0, w: 3, h: 3 },
    { id: 'r1b', type: 'key', command: 'clip.cut',   label: 'B', x: 3, y: 0, w: 3, h: 3 },
    { id: 'r1c', type: 'key', command: 'clip.paste', label: 'C', x: 6, y: 0, w: 3, h: 3 },
    { id: 'r2a', type: 'key', command: 'clip.copy',  label: 'D', x: 0, y: 3, w: 3, h: 3 },
    { id: 'r2b', type: 'key', command: 'clip.cut',   label: 'E', x: 3, y: 3, w: 3, h: 3 },
    { id: 'r2c', type: 'key', command: 'clip.paste', label: 'F', x: 6, y: 3, w: 3, h: 3 },
    { id: 'r3a', type: 'key', command: 'clip.copy',  label: 'G', x: 0, y: 6, w: 3, h: 3 },
    { id: 'r3b', type: 'key', command: 'clip.cut',   label: 'H', x: 3, y: 6, w: 3, h: 3 },
    { id: 'r3c', type: 'key', command: 'clip.paste', label: 'I', x: 6, y: 6, w: 3, h: 3 }
  ]}
});

var rows = sandbox.scanRows();
ok('nine keys in three bands make three rows', rows.length === 3,
   rows.map(function (r) { return r.length; }).join('+'));
ok('each row holds its three keys',
   rows.every(function (r) { return r.length === 3; }));

// A tall control must join the row it starts in, not invent one of its own.
sandbox.handleMessage({
  type: 'layout', pages: 1, page: 0,
  layout: { cols: 12, rows: 12, keys: [
    { id: 'k', type: 'key', command: 'clip.copy', label: 'K', x: 0, y: 0, w: 3, h: 3 },
    { id: 's', type: 'slider', command: 'audio.master', label: 'S', x: 3, y: 0, w: 3, h: 9 },
    { id: 'm', type: 'key', command: 'clip.cut', label: 'M', x: 6, y: 3, w: 3, h: 3 }
  ]}
});
var tall = sandbox.scanRows();
ok('a tall control joins one row and stretches it', tall.length === 1,
   tall.length + ' row(s)');

// ── the saving, counted ───────────────────────────────────────
function pressesToReach(pattern, wantedLabel, cap) {
  sandbox.access.mode = 'step';
  sandbox.access.pattern = pattern;
  sandbox.access.guard = 0;
  sandbox.scanStart();
  for (var n = 1; n <= cap; n++) {
    var groups = sandbox.scanGroups();
    var lit = groups[sandbox.scanAt] || [];
    var isTarget = lit.length === 1 &&
      (lit[0].getAttribute('aria-label') || '').indexOf(wantedLabel) === 0;
    if (isTarget) { return n; }
    // In row and column, taking a row that contains the target is progress.
    if (pattern === 'rowcol' && sandbox.scanPhase === 'rows' &&
        lit.some(function (e) {
          return (e.getAttribute('aria-label') || '').indexOf(wantedLabel) === 0; })) {
      sandbox.scanChoose();
      continue;
    }
    sandbox.scanStep();
  }
  return cap + 1;
}

sandbox.handleMessage({
  type: 'layout', pages: 1, page: 0,
  layout: { cols: 12, rows: 12, keys: (function () {
    var out = [], n = 0;
    for (var r = 0; r < 5; r++) {
      for (var c = 0; c < 8; c++) {
        out.push({ id: 'g' + (n), type: 'key', command: 'clip.copy',
                   label: 'KEY' + n, x: c, y: r, w: 1, h: 1 });
        n++;
      }
    }
    return out;
  })() }
});
ok('a forty key board makes five rows', sandbox.scanRows().length === 5);

var linear = pressesToReach('linear', 'KEY39', 200);
var rowcol = pressesToReach('rowcol', 'KEY39', 200);
ok('row and column reaches the far key in fewer presses', rowcol < linear,
   rowcol + ' presses instead of ' + linear);

// ── you cannot get stuck in a row you did not want ────────────
sandbox.access.pattern = 'rowcol';
sandbox.scanStart();
sandbox.scanChoose();                       // take row one
ok('taking a row enters it', sandbox.scanPhase === 'keys');
for (var i = 0; i < 40; i++) { sandbox.scanStep(); }
ok('sweeping a row twice without choosing backs out of it',
   sandbox.scanPhase === 'rows');

sandbox.access.mode = 'off';
sandbox.access.pattern = 'linear';
sandbox.scanStop();

// A layout that flows rather than placing its keys still has rows. This
// was found by looking at the real phone rather than by a test: the built
// in starter board has no coordinates at all, every key read as y=0, and
// twelve keys became one row of twelve - which made row and column
// scanning cost a press more than sweeping one at a time.
sandbox.handleMessage({
  type: 'layout', pages: 1, page: 0,
  layout: { cols: 4, rows: 3, keys: [
    { id: 'f1', label: 'A', action: 'ctrl+a' }, { id: 'f2', label: 'B', action: 'ctrl+b' },
    { id: 'f3', label: 'C', action: 'ctrl+c' }, { id: 'f4', label: 'D', action: 'ctrl+d' },
    { id: 'f5', label: 'E', action: 'ctrl+e' }, { id: 'f6', label: 'F', action: 'ctrl+f' },
    { id: 'f7', label: 'G', action: 'ctrl+g' }, { id: 'f8', label: 'H', action: 'ctrl+h' }
  ]}
});
var flowed = sandbox.scanRows();
ok('a layout with no coordinates still has rows', flowed.length === 2,
   flowed.map(function (r) { return r.length; }).join('+') + ' from a 4 wide board');

// ── The second face ───────────────────────────────────────────
// A mute key that reads MUTE MIC whether or not the microphone is muted
// tells you what the key does rather than what is true.
sandbox.handleMessage({
  type: 'layout', pages: 1, page: 0,
  layout: { cols: 8, rows: 4, keys: [
    { id: 'mic', type: 'toggle', command: 'audio.mic.mute',
      label: 'MIC LIVE', color: '#12211a',
      whenOn: { label: 'MUTED', color: '#2a1216' },
      x: 0, y: 0, w: 4, h: 4 }
  ]}
});
var micEl = dom.document.querySelector('[data-id="mic"]');
ok('a toggle shows its ordinary face when off',
   /MIC LIVE/.test(micEl.getAttribute('aria-label') || ''));

// Deliberately NOT re-rendering. A state arriving from the PC has to
// change the face where it stands - calling renderKeys() here was the
// test doing the work the code was supposed to do, and it hid the fact
// that applyState only ever toggled a class and left the words alone.
sandbox.handleMessage({ type: 'state', state: { 'audio.mic.mute': true } });
micEl = dom.document.querySelector('[data-id="mic"]');
ok('and its second face when on, without a re-render',
   /MUTED/.test(micEl.getAttribute('aria-label') || ''),
   micEl.getAttribute('aria-label'));

sandbox.handleMessage({ type: 'state', state: { 'audio.mic.mute': false } });
micEl = dom.document.querySelector('[data-id="mic"]');
ok('and back again when it is unmuted',
   /MIC LIVE/.test(micEl.getAttribute('aria-label') || ''),
   micEl.getAttribute('aria-label'));

var partial = sandbox.faceFor({ label: 'A', sub: 'b', color: '#111111',
                                state: true, whenOn: { color: '#222222' } });
ok('anything left out of whenOn keeps the ordinary face',
   partial.label === 'A' && partial.sub === 'b' && partial.color === '#222222');

// ── Timers ────────────────────────────────────────────────────
sandbox.handleMessage({
  type: 'layout', pages: 1, page: 0,
  layout: { cols: 8, rows: 4, keys: [
    { id: 'ad', type: 'timer', label: 'AD BREAK', arg: '180',
      x: 0, y: 0, w: 6, h: 4 }
  ]}
});
var adEl = dom.document.querySelector('[data-id="ad"]');
ok('a timer is a button with a name', adEl &&
   adEl.getAttribute('role') === 'button' &&
   /AD BREAK/.test(adEl.getAttribute('aria-label') || ''));

var nowMs = Date.now();
sandbox.handleMessage({ type: 'timers', timers: {
  ad: { running: true, startedAt: nowMs - 20000, accumulated: 0,
        duration: 180, done: false } } });
adEl = dom.document.querySelector('[data-id="ad"]');
ok('a countdown shows what is left, not what has passed',
   /02:40/.test(adEl.getAttribute('aria-label') || ''),
   adEl.getAttribute('aria-label'));
ok('and says it is running',
   /running/.test(adEl.getAttribute('aria-label') || ''));

sandbox.handleMessage({ type: 'timers', timers: {
  ad: { running: false, startedAt: 0, accumulated: 180000,
        duration: 180, done: true } } });
adEl = dom.document.querySelector('[data-id="ad"]');
ok('a finished countdown reads zero and says so',
   /00:00/.test(adEl.getAttribute('aria-label') || '') &&
   /finished/.test(adEl.getAttribute('aria-label') || ''),
   adEl.getAttribute('aria-label'));

sandbox.handleMessage({ type: 'timers', timers: {
  ad: { running: false, startedAt: 0, accumulated: 3725000, duration: 0,
        done: false } } });
adEl = dom.document.querySelector('[data-id="ad"]');
ok('past an hour it grows an hours column',
   /1:02:05/.test(adEl.getAttribute('aria-label') || ''),
   adEl.getAttribute('aria-label'));

// ── Compose ───────────────────────────────────────────────────
// The phone already has a keyboard this person can use. Typing there and
// sending it is the shortest route to a text box on a computer they
// cannot easily type into - and the same text through the PC's voice is
// what turns a keyboard into a way of speaking.
dom.document._register('compose-text', (function () {
  var el = dom.document.createElement('textarea');
  el.setAttribute('id', 'compose-text');
  return el;
})());
dom.document._register('compose-note', dom.document.createElement('div'));
dom.document._register('compose-sheet', dom.document.createElement('div'));
dom.document._register('compose-title', dom.document.createElement('div'));

var beforeCompose = sent.length;
dom.document.getElementById('compose-text').value = 'Could you pass the water please.';
sandbox.sendCompose('type');
var typed = sent.slice(beforeCompose).filter(function (m) { return m.type === 'compose'; });
ok('what was typed on the phone is sent to the PC',
   typed.length === 1 && typed[0].mode === 'type' &&
   typed[0].text === 'Could you pass the water please.');

sandbox.sendCompose('say');
var said = sent.filter(function (m) { return m.type === 'compose' && m.mode === 'say'; });
ok('and the same words can be spoken instead', said.length === 1);

dom.document.getElementById('compose-text').value = '';
var beforeEmpty = sent.length;
sandbox.sendCompose('type');
ok('an empty box sends nothing', sent.length === beforeEmpty);

console.log('  ---');
console.log('  ' + (fail.length ? fail.length + ' FAILED' : 'all pass'));
process.exit(fail.length ? 1 : 0);
