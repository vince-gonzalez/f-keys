/**
 * KEY-J — the OS keyboard hook is installed only while capture is on.
 *
 *   node test/hook-lifecycle.test.js
 *
 * Key-J installs a WH_KEYBOARD_LL hook, which sits between Windows and its
 * own shortcuts. It used to be installed at start-up and left there for the
 * session even though Global Capture defaults to off, so the app was in the
 * path of every keystroke on the machine while doing nothing with them.
 *
 * This counts the real uIOhook.start()/stop() calls behind a mocked electron
 * and a mocked uiohook-napi, so it fails if the hook is ever installed
 * before someone asks for it.
 */
'use strict';

const Module = require('module');
const path = require('path');
const assert = require('assert');

// ── the two things main.js requires ────────────────────────────
const hook = { started: 0, stopped: 0, listeners: {} };
const uiohookMock = {
  UiohookKey: { A: 30, B: 48, Space: 57, Comma: 51, 1: 2 },
  uIOhook: {
    on: (evt, fn) => { (hook.listeners[evt] = hook.listeners[evt] || []).push(fn); },
    start: () => { hook.started++; },
    stop: () => { hook.stopped++; }
  }
};

const sent = [];
const ipc = { handlers: {}, listeners: {} };
const win = {
  destroyed: false,
  isDestroyed: () => win.destroyed,
  webContents: { send: (ch, data) => sent.push({ ch, data }), on: () => {},
                 setWindowOpenHandler: () => {} },
  on: () => {}, once: () => {}, loadFile: () => {}, show: () => {},
  focus: () => {}, hide: () => {}, minimize: () => {}, maximize: () => {},
  unmaximize: () => {}, isMaximized: () => false, isVisible: () => true
};
let readyResolve;
const electronMock = {
  app: {
    whenReady: () => new Promise((r) => { readyResolve = r; }),
    on: () => {}, quit: () => {}, getVersion: () => '1.6.1',
    requestSingleInstanceLock: () => true
  },
  BrowserWindow: Object.assign(function () { return win; },
    { getAllWindows: () => [win] }),
  Tray: function () {
    return { setToolTip: () => {}, setContextMenu: () => {}, on: () => {},
             displayBalloon: () => {} };
  },
  Menu: { buildFromTemplate: (t) => t },
  ipcMain: {
    handle: (ch, fn) => { ipc.handlers[ch] = fn; },
    on: (ch, fn) => { ipc.listeners[ch] = fn; }
  },
  nativeImage: {
    createFromPath: () => ({ isEmpty: () => false }),
    createEmpty: () => ({ isEmpty: () => true })
  },
  globalShortcut: { register: () => {}, unregisterAll: () => {} },
  shell: { openExternal: () => {} }
};

const realLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === 'electron') return electronMock;
  if (request === 'uiohook-napi') return uiohookMock;
  return realLoad.apply(this, arguments);
};

require(path.join(__dirname, '..', 'src', 'main.js'));

function check(name, fn) {
  try { fn(); console.log('  ok    ' + name); return true; }
  catch (err) { console.log('  FAIL  ' + name + '\n        ' + err.message); return false; }
}

(async () => {
  let pass = true;
  readyResolve();
  await new Promise((r) => setImmediate(r));

  pass &= check('start-up installs no hook', () => {
    assert.strictEqual(hook.started, 0,
      'uIOhook.start() was called ' + hook.started + ' time(s) before capture was asked for');
  });

  pass &= check('start-up still reports availability to the renderer', () => {
    assert.ok(ipc.handlers['get-global-capture-status'], 'status handler missing');
    const s = ipc.handlers['get-global-capture-status']();
    assert.strictEqual(s.enabled, false, 'capture should default to off');
    assert.strictEqual(s.available, true, 'the module loaded, so it is available');
  });

  pass &= check('turning capture on installs the hook exactly once', () => {
    const r = ipc.handlers['toggle-global-capture'](null, true);
    assert.strictEqual(hook.started, 1, 'expected 1 start, got ' + hook.started);
    assert.strictEqual(r.enabled, true);
  });

  pass &= check('turning it on again does not install a second hook', () => {
    ipc.handlers['toggle-global-capture'](null, true);
    assert.strictEqual(hook.started, 1, 'expected still 1 start, got ' + hook.started);
  });

  pass &= check('keys reach the renderer while capture is on', () => {
    const before = sent.filter((m) => m.ch === 'global-keydown').length;
    hook.listeners.keydown.forEach((fn) => fn({ keycode: 30 }));
    const after = sent.filter((m) => m.ch === 'global-keydown');
    assert.strictEqual(after.length, before + 1, 'keydown did not reach the renderer');
    assert.strictEqual(after[after.length - 1].data.key, 'a', 'keycode 30 should map to "a"');
  });

  pass &= check('turning capture off removes the hook', () => {
    const r = ipc.handlers['toggle-global-capture'](null, false);
    assert.strictEqual(hook.stopped, 1, 'expected 1 stop, got ' + hook.stopped);
    assert.strictEqual(r.enabled, false);
  });

  pass &= check('no keys reach the renderer once capture is off', () => {
    const before = sent.filter((m) => m.ch === 'global-keydown').length;
    hook.listeners.keydown.forEach((fn) => fn({ keycode: 30 }));
    assert.strictEqual(sent.filter((m) => m.ch === 'global-keydown').length, before,
      'a key was forwarded after capture was turned off');
  });

  pass &= check('quitting removes the hook it installed', () => {
    ipc.handlers['toggle-global-capture'](null, true);
    const stoppedBefore = hook.stopped;
    ipc.listeners['window-quit']();
    assert.strictEqual(hook.stopped, stoppedBefore + 1, 'quit did not remove the hook');
  });

  console.log(pass ? '\n  all passed' : '\n  FAILURES');
  process.exit(pass ? 0 : 1);
})();
