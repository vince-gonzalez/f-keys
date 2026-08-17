# Key-J — Musical Keystroke Studio
### Every key you press plays a musical note. Works in any app on your PC.

---

## What it does
Key-J turns your keyboard into a musical instrument. Every keystroke plays a
customizable musical tone. It tracks your entire session, draws the notes on a
staff in real time, and lets you export the whole thing as a WAV file (which
you can convert to MP3 with any free tool).

With **Global Capture** enabled, it works even when you're typing in Notepad,
Chrome, a game, or anything else on your PC.

---

## Requirements
- **Windows 10 or 11** (Mac/Linux also work with minor tweaks — see bottom)
- **Node.js** (v18 or higher) — download from https://nodejs.org
  - Just install it with default settings, that's all
- **Git** (optional, only if you cloned this from a repo)

---

## First-Time Setup (do this once)

1. **Open a terminal** in the `key-j` folder.
   - Right-click inside the folder → "Open in Terminal"
   - Or: open Command Prompt / PowerShell and type `cd path\to\key-j`

2. **Install dependencies:**
   ```
   npm install
   ```
   This downloads Electron and the keyboard hook library. Takes 1–3 minutes.

3. **Run Key-J:**
   ```
   npm start
   ```
   The app opens. Done.

---

## How to Use Key-J

### Playing Notes
- Press any key on your keyboard. It plays a musical note.
- **Tap** a key quickly → short staccato-style note
- **Hold** a key → sustained note that lasts as long as you hold
- The app remembers every single note in order, picking up exactly where you left off

### Global Capture (play in any app)
- In the top-right of the app, toggle **"Global Capture"** ON
- Now Key-J hears your keystrokes even when you're using Notepad, Chrome, etc.
- **Important:** On Windows, you may need to run Key-J as Administrator for
  global capture to work. Right-click the terminal → "Run as administrator",
  then run `npm start` again.
- Toggle it OFF any time to go back to window-only mode

### Left Panel — Key Map
- Shows every key on your keyboard and what note it's bound to
- **Click any key row** to re-assign it to any note you want
- Use the **Scale** buttons to change the musical scale (Major, Minor, Blues, etc.)
- Use **Octave +/−** to shift all notes up or down by an octave

### Right Panel — Sound Controls

**Play Styles:**
- **Normal** — clean attack and release
- **Staccato** — sharp, punchy, cut short automatically
- **Vibrato** — pitch wobbles up and down (LFO)
- **Tremolo** — volume flutters rhythmically
- **Arpeggio** — plays a chord spread (root, 3rd, 5th, octave) on each key
- **Legato** — extra-smooth crossfade between notes

**Waveform:**
- **Sine** — smooth, pure tone (default)
- **Saw** — bright, buzzy
- **Square** — hollow, retro
- **Triangle** — soft, flute-like

**Sliders:**
- **Attack** — how fast the note fades in (ms)
- **Release** — how long the note rings after you let go (ms)
- **Volume** — overall output level
- **Reverb** — add room/hall echo
- **Detune** — shift pitch up or down in semitones

### Staff (Center Top)
- Shows a treble clef staff that draws your notes in real time as you type
- Notes are colored by play style so you can see the pattern visually
- Scrolls automatically as your session grows

### Visualizer (Center Main)
- **Wave** — real-time waveform of what you're playing
- **Roll** — piano-roll style scrolling view of notes over time
- **FFT** — frequency spectrum analyzer

### Bottom Bar
- **⏺ Rec** — starts precise timing for your session (important for export timing)
- **▶ Play** — plays back everything you've typed so far
- **Export WAV** — renders and downloads your full session as a WAV file
- **✕ Clear** — wipes the session and starts fresh

---

## Exporting

1. Click **Export WAV** at any time
2. Give it a filename
3. Choose whether to normalize the audio (recommended: Yes)
4. Click **Download** — a `.wav` file saves to your Downloads folder

**To convert to MP3:**
- Free option: Download Audacity (audacityteam.org), open the WAV, File → Export → MP3
- Command line (if you have ffmpeg): `ffmpeg -i Key-J_Session.wav Key-J_Session.mp3`
- Online: dozens of free WAV-to-MP3 converters work fine

---

## Building an Installer (.exe)

When you're ready to release or share Key-J:

1. Install the icon files (see `assets/` folder — add your own `icon.ico`)
2. Run:
   ```
   npm run build
   ```
3. Find the installer in the `dist/` folder — it's a standard Windows NSIS installer

---

## Troubleshooting

**"Global Capture doesn't work"**
→ Run your terminal as Administrator. uiohook-napi requires elevated permissions
  on some Windows configurations.

**"App won't open" / "electron not found"**
→ Run `npm install` again. Make sure Node.js is installed.

**"No sound"**
→ Click anywhere in the app first (browsers/Electron require a user gesture to
  start audio). Check your system volume.

**"I accidentally re-bound a key to the wrong note"**
→ Click the key in the left panel and re-assign it. Or just change the scale/
  octave to rebuild all bindings from scratch.

---

## Mac / Linux Notes
- Mac: works as-is. Global capture via uiohook-napi requires Accessibility
  permissions (System Preferences → Privacy → Accessibility → add Key-J)
- Linux: works on X11. Wayland support depends on your distro. Run with sudo
  if global capture fails.

---

## File Structure
```
key-j/
├── src/
│   ├── main.js       ← Electron main process (window, tray, key hook)
│   ├── preload.js    ← Secure IPC bridge
│   └── index.html    ← Full UI + audio engine
├── assets/
│   └── icon.ico      ← App icon (add your own)
├── package.json      ← App config + build settings
└── README.md         ← This file
```

---

## License
Key-J is personal-use software. For commercial release, contact DooBedder.
