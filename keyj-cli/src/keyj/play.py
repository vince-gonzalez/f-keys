"""
============================================================
keyj.play — your sequence, advanced by any key, anywhere
F-Keys | www.f-keys.com
------------------------------------------------------------
WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT

This installs a system-wide keyboard listener, which is the
same machinery a keylogger uses. So the design point is this:

  IT DOES NOT NEED TO KNOW WHICH KEY YOU PRESSED.

In sequence mode every key plays the next note of the sequence.
Which key is irrelevant, so the identity of the key is never
stored, never written, never counted per-key and never sent
anywhere. The callback examines a key for exactly one thing -
whether it is a modifier, which should not advance the melody -
and then discards it. There is no buffer of keystrokes here to
leak, because one is never built.

That is a structural property, not a promise in a README. Read
_on_press below; it is nine lines.

THE PARTS THAT NEED PERMISSION

  macOS    Accessibility permission, granted to your terminal
  Linux/X11 works as-is
  Linux/Wayland  no global hook exists; you get nothing, and
                 this says so rather than sitting there silent
  Windows  works as-is unless a security tool blocks the hook
============================================================
"""

import sys
import threading

from . import render as rendermod

RATE = 22050          # the player mixes in Python; half rate, half the work
VOICES = 12           # more than this and you cannot hear the difference


class Missing(Exception):
    """A dependency the live player needs is not installed."""


def _require():
    """
    Import the optional pieces, and say exactly what to install if they are
    absent. `pip install keyj` gives you render and tab with no dependencies
    at all; the live player is the only part that needs more.
    """
    try:
        import sounddevice
    except Exception as err:                       # pragma: no cover - env
        raise Missing(
            "keyj play needs an audio backend.\n"
            "  pip install 'keyj[play]'\n"
            "  ({})".format(err))
    try:
        import pynput
    except Exception as err:                       # pragma: no cover - env
        raise Missing(
            "keyj play needs a keyboard listener.\n"
            "  pip install 'keyj[play]'\n"
            "  ({})".format(err))
    return sounddevice, pynput


def _voice(note, seconds, tone):
    """One note, pre-rendered once at startup so the keypress path is a copy."""
    t = rendermod.TONES[tone]
    n = int(seconds * RATE)
    out = [0.0] * n
    inc = note.freq / float(RATE)
    attack = max(1, int(min(t["attack"], seconds * 0.25) * RATE))
    phase = 0.0
    for i in range(n):
        if i < attack:
            env = i / float(attack)
        else:
            env = pow(2.718281828, -3.2 * (i - attack) / float(n - attack))
        out[i] = rendermod._sample(t["wave"], phase) * env * 0.55
        phase += inc
        if phase >= 1.0:
            phase -= 1.0
    if t["drive"] > 0.01:
        curve = rendermod._drive_curve(t["drive"])
        out = [curve(v) for v in out]
    return out


class Player(object):
    """Holds the pre-rendered notes and mixes whichever are still ringing."""

    def __init__(self, notes, tone="clean", hold=0.55, loop=True, on_note=None):
        self.notes = notes
        self.tone = tone
        self.loop = loop
        self.on_note = on_note
        self.pos = 0
        self.voices = []                 # (samples, index)
        self.lock = threading.Lock()
        self.finished = threading.Event()
        self.voices_by_note = [_voice(n, hold, tone) for n in notes]

    def advance(self):
        """Start the next note. Called from the key listener thread."""
        with self.lock:
            if self.pos >= len(self.notes):
                if not self.loop:
                    self.finished.set()
                    return None
                self.pos = 0
            index = self.pos
            self.pos += 1
            self.voices.append([self.voices_by_note[index], 0])
            if len(self.voices) > VOICES:
                del self.voices[0:len(self.voices) - VOICES]
        if self.on_note:
            self.on_note(index, self.notes[index])
        return self.notes[index]

    def mix(self, frames):
        """Sum the live voices into one block of samples."""
        block = [0.0] * frames
        with self.lock:
            keep = []
            for entry in self.voices:
                samples, at = entry
                end = min(at + frames, len(samples))
                j = 0
                for i in range(at, end):
                    block[j] += samples[i]
                    j += 1
                entry[1] = end
                if end < len(samples):
                    keep.append(entry)
            self.voices = keep
        return block


def run(notes, tone="clean", loop=True, hold=0.55, on_note=None, on_ready=None):
    """
    Block until interrupted, playing the next note on every key press.

    Returns the number of notes played. Raises Missing if the optional
    dependencies are absent, and RuntimeError if the platform has no hook.
    """
    sd, pynput = _require()
    from pynput import keyboard

    player = Player(notes, tone=tone, hold=hold, loop=loop, on_note=on_note)

    MODIFIERS = {
        keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l,
        keyboard.Key.ctrl, keyboard.Key.ctrl_r, keyboard.Key.ctrl_l,
        keyboard.Key.alt, keyboard.Key.alt_r, keyboard.Key.alt_l,
        keyboard.Key.cmd, keyboard.Key.cmd_r, keyboard.Key.cmd_l,
        keyboard.Key.caps_lock, keyboard.Key.num_lock,
    }
    held = {"down": False}

    def _on_press(key):
        # The ONLY thing this asks about the key is whether it is a modifier,
        # so that Shift does not eat a note. The key is not stored, not
        # written, not counted per-key and not sent anywhere. After this
        # function returns, nothing in the process knows what was pressed.
        if key in MODIFIERS:
            return
        if held["down"]:            # ignore auto-repeat while a key is held
            return
        held["down"] = True
        player.advance()

    def _on_release(key):
        if key not in MODIFIERS:
            held["down"] = False

    def callback(outdata, frames, time_info, status):
        block = player.mix(frames)
        out = bytearray(frames * 2)
        for i in range(frames):
            v = block[i]
            if v > 1.0:
                v = 1.0
            elif v < -1.0:
                v = -1.0
            s = int(v * 32767)
            if s < 0:
                s += 65536
            out[i * 2] = s & 0xFF
            out[i * 2 + 1] = (s >> 8) & 0xFF
        outdata[:] = bytes(out)

    stream = sd.RawOutputStream(samplerate=RATE, channels=1, dtype="int16",
                                blocksize=512, callback=callback)
    listener = keyboard.Listener(on_press=_on_press, on_release=_on_release)

    try:
        listener.start()
    except Exception as err:                       # pragma: no cover - env
        raise RuntimeError(
            "no global keyboard hook on this system ({}).\n"
            "  On Wayland there is no such hook to install. X11 works.\n"
            "  On macOS, grant Accessibility permission to your terminal."
            .format(err))

    with stream:
        if on_ready:
            on_ready()
        try:
            while listener.running and not player.finished.is_set():
                player.finished.wait(0.2)
        except KeyboardInterrupt:
            pass
        finally:
            listener.stop()
    return player.pos
