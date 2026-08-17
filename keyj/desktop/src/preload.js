/**
 * KEY-J — Preload Script (src/preload.js)
 * Exposes a safe, typed API from main process to renderer via contextBridge.
 * No raw Node/Electron APIs are exposed — renderer stays sandboxed.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('keyJBridge', {

  // ── Window chrome controls ──────────────────────────────────
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close:    () => ipcRenderer.send('window-close'),
  quit:     () => ipcRenderer.send('window-quit'),

  // ── Global capture toggle ───────────────────────────────────
  toggleGlobalCapture: (enabled) =>
    ipcRenderer.invoke('toggle-global-capture', enabled),

  getGlobalCaptureStatus: () =>
    ipcRenderer.invoke('get-global-capture-status'),

  // ── Listen for global key events from main process ──────────
  onGlobalKeydown: (callback) => {
    ipcRenderer.on('global-keydown', (_, data) => callback(data));
  },
  onGlobalKeyup: (callback) => {
    ipcRenderer.on('global-keyup', (_, data) => callback(data));
  },

  // ── Status events ───────────────────────────────────────────
  onGlobalCaptureStatus: (callback) => {
    ipcRenderer.on('global-capture-status', (_, data) => callback(data));
  },
  onHookStatus: (callback) => {
    ipcRenderer.on('hook-status', (_, data) => callback(data));
  },

  // ── Cleanup ─────────────────────────────────────────────────
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }

});
