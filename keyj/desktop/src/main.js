/**
 * KEY-J — Main Process (src/main.js)
 * Handles: BrowserWindow, system tray, global keyboard hook via uiohook-napi,
 * IPC bridge between native key events and the renderer UI.
 */

const { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage, globalShortcut, shell } = require('electron');
const path = require('path');

// ── State ──────────────────────────────────────────────────────
let mainWindow = null;
let tray = null;
let uiohook = null;
let globalCaptureEnabled = false;
let isQuitting = false;

// ── Create Window ──────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    // v1.6: the renderer's design floor is 1280. Opening at 1100 with a
    // 860 minimum meant the app launched already scrolled sideways and
    // could be dragged narrower than its own layout.
    width: 1360,
    height: 860,
    minWidth: 1280,
    minHeight: 620,
    title: 'Key-J',
    // Without this the taskbar and Alt-Tab show Electron's default icon,
    // which is what shipped through 1.4.2.
    icon: path.join(__dirname, '..', 'build', 'icon.ico'),
    backgroundColor: '#0a0a0e',
    frame: false,           // custom titlebar inside renderer
    titleBarStyle: 'hidden',
    trafficLightPosition: { x: 14, y: 14 },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    },
    show: false
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // ── External links ───────────────────────────────────────────
  //
  // There was no handler here, so a target=_blank link opened a fresh
  // BrowserWindow inside the app: no chrome, no way back, and a remote page
  // running in a window this app owns. The manual lives on f-keys.com, so
  // http and https go to the system browser and everything else is refused.
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const p = new URL(url).protocol;
      if (p === 'https:' || p === 'http:') shell.openExternal(url);
    } catch (err) {
      console.error('setWindowOpenHandler:', err);
    }
    return { action: 'deny' };
  });

  // The renderer is a local file and should stay one. Navigating the main
  // window to a remote page would hand that page the preload bridge.
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://')) {
      event.preventDefault();
      try {
        const p = new URL(url).protocol;
        if (p === 'https:' || p === 'http:') shell.openExternal(url);
      } catch (err) {
        console.error('will-navigate:', err);
      }
    }
  });

  // Hide to tray instead of quitting
  mainWindow.on('close', (e) => {
    if (!isQuitting) {
      e.preventDefault();
      mainWindow.hide();
      tray && tray.displayBalloon && tray.displayBalloon({
        title: 'Key-J',
        content: 'Still running in the background. Right-click the tray icon to quit.'
      });
    }
  });
}

// ── Tray ───────────────────────────────────────────────────────
function createTray() {
  // The real Key-J mark, packaged beside this file. It shipped for four
  // versions with a generated 16x16 placeholder here and Electron's default
  // icon everywhere else, which is the first thing anyone sees.
  let icon;
  try {
    icon = nativeImage.createFromPath(path.join(__dirname, 'tray.png'));
    if (icon.isEmpty()) throw new Error('tray.png did not load');
  } catch (err) {
    console.error('tray icon:', err);
    icon = nativeImage.createEmpty();
  }
  tray = new Tray(icon);
  tray.setToolTip('Key-J — Musical Keystroke Studio');
  updateTrayMenu();

  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.focus() : mainWindow.show();
  });
}

// ── Updates ────────────────────────────────────────────────────
//
// There is deliberately no auto-updater here, and three reasons for that:
//
//   1. This repository releases several products. An updater asking GitHub
//      for "the latest release" gets whatever shipped last, which today is
//      PlumHUD 4.1.0. It would offer Key-J users a miner dashboard.
//
//   2. A silent install over a running Key-J exits 0 and leaves a mixed
//      install - Windows holds the executable and the app bundle open, so
//      those keep the old version while everything else is replaced. That is
//      measured, not theoretical, and it is what an updater does by default.
//
//   3. The privacy page says Key-J makes no outbound network requests. An
//      updater polling a release feed would make that false, and a claim
//      like that is worth more than the convenience of not clicking.
//
// So checking for an update opens the releases page in the system browser.
// No request is made unless the user asks for one, and the request is made
// by their browser rather than by this app.
const RELEASES_URL = 'https://github.com/vince-gonzalez/f-keys/releases/latest';

function updateTrayMenu() {
  const menu = Menu.buildFromTemplate([
    {
      label: 'Key-J ' + app.getVersion(),
      enabled: false
    },
    { type: 'separator' },
    {
      label: globalCaptureEnabled ? '🎹 Global Capture: ON' : '🎹 Global Capture: OFF',
      click: () => toggleGlobalCapture(!globalCaptureEnabled)
    },
    {
      label: 'Show Window',
      click: () => { mainWindow.show(); mainWindow.focus(); }
    },
    { type: 'separator' },
    {
      label: 'Manual',
      click: () => { shell.openExternal('https://f-keys.com/keyj/manual/'); }
    },
    {
      label: 'Check for updates\u2026',
      click: () => { shell.openExternal(RELEASES_URL); }
    },
    { type: 'separator' },
    {
      label: 'Quit Key-J',
      click: () => {
        isQuitting = true;
        stopHook();
        app.quit();
      }
    }
  ]);
  tray.setContextMenu(menu);
}

// ── Global Key Hook (uiohook-napi) ─────────────────────────────
function startHook() {
  try {
    const { UiohookKey, uIOhook } = require('uiohook-napi');
    uiohook = uIOhook;
    CODE_TO_CHAR = buildKeycodeMap(UiohookKey);
    console.log('[Key-J] keycode map built from UiohookKey:',
                Object.keys(CODE_TO_CHAR).length, 'keys');

    uiohook.on('keydown', (e) => {
      if (!globalCaptureEnabled) return;
      // Send raw keycode to renderer
      mainWindow && mainWindow.webContents.send('global-keydown', {
        keycode: e.keycode,
        key: keycodeToChar(e.keycode)
      });
    });

    uiohook.on('keyup', (e) => {
      if (!globalCaptureEnabled) return;
      mainWindow && mainWindow.webContents.send('global-keyup', {
        keycode: e.keycode,
        key: keycodeToChar(e.keycode)
      });
    });

    uiohook.start();
    console.log('[Key-J] Global key hook started.');
  } catch (err) {
    console.warn('[Key-J] uiohook-napi not available — falling back to window-focused mode only.', err.message);
    // Graceful fallback: renderer still works when window is focused
    mainWindow && mainWindow.webContents.send('hook-status', { available: false });
  }
}

function stopHook() {
  try { uiohook && uiohook.stop(); } catch(e) {}
}

function toggleGlobalCapture(enable) {
  globalCaptureEnabled = enable;
  updateTrayMenu();
  mainWindow && mainWindow.webContents.send('global-capture-status', { enabled: globalCaptureEnabled });
}


// ── Keycode -> character ───────────────────────────────────────
//
// This was a hand-written table of guessed numbers, and every entry in it
// was wrong. It used macOS iokit codes (A = 0) while uiohook-napi emits its
// own constants on every platform (A = 30). The object literal also had
// duplicate keys - 16 was assigned three times - so six of the thirty-six
// entries were silently discarded by the parser before anything ran.
//
// The net effect: global capture, which is the entire reason this app exists
// as a desktop build, played the wrong note for the handful of codes that
// happened to collide and nothing at all for the rest.
//
// So the table is not written by hand any more. UiohookKey is the library's
// own name -> code map; inverting it is correct by construction and cannot
// drift when the library changes.
let CODE_TO_CHAR = null;

const PUNCTUATION = {
  Space: ' ', Comma: ',', Period: '.', Semicolon: ';', Quote: "'",
  Slash: '/', Backslash: String.fromCharCode(92), Minus: '-', Equal: '=',
  BracketLeft: '[', BracketRight: ']', Backquote: '`'
};

function buildKeycodeMap(UiohookKey) {
  const out = {};
  Object.keys(UiohookKey).forEach((name) => {
    const code = UiohookKey[name];
    let ch = null;
    if (/^[A-Z]$/.test(name)) ch = name.toLowerCase();      // A -> a
    else if (/^[0-9]$/.test(name)) ch = name;               // 7 -> 7
    else if (PUNCTUATION[name]) ch = PUNCTUATION[name];
    if (ch !== null) out[code] = ch;
  });
  return out;
}

function keycodeToChar(keycode) {
  return (CODE_TO_CHAR && CODE_TO_CHAR[keycode]) || null;
}

// ── IPC Handlers ───────────────────────────────────────────────
ipcMain.handle('toggle-global-capture', (_, enabled) => {
  toggleGlobalCapture(enabled);
  return { enabled: globalCaptureEnabled };
});

ipcMain.handle('get-global-capture-status', () => {
  return { enabled: globalCaptureEnabled };
});

ipcMain.on('window-minimize', () => mainWindow.minimize());
ipcMain.on('window-maximize', () => {
  mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
});
ipcMain.on('window-close', () => mainWindow.hide());
ipcMain.on('window-quit', () => { isQuitting = true; stopHook(); app.quit(); });

// ── App Lifecycle ──────────────────────────────────────────────
app.whenReady().then(() => {
  createWindow();
  createTray();
  startHook();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
    else mainWindow.show();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // Don't quit — keep tray alive
  }
});

app.on('before-quit', () => {
  isQuitting = true;
  stopHook();
});

// Prevent second instance
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) { mainWindow.show(); mainWindow.focus(); }
  });
}
