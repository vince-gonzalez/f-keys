#!/usr/bin/env python3
"""
============================================================
remapwrap.elgato - bring a Stream Deck profile across
F-Keys | www.f-keys.com
------------------------------------------------------------
WHAT THIS IS, AND WHAT IT IS NOT

Somebody with years of Stream Deck profiles will not rebuild
them by hand to try something else, so this reads them.

Elgato does not publish the format of a .streamDeckProfile.
The official documentation covers how to bundle one and says
nothing about what is inside it, so everything here is read
from the files themselves rather than from a specification.
That has one consequence worth stating plainly: this is
best effort, and it says so out loud.

It never invents a binding it is not sure of. An action it
does not recognise becomes a key with the right name, the
right picture and the right place on the board, and NO
command - so it is visibly inert rather than quietly wrong.
Everything it could not map comes back in a report.

WHAT IT READS

A .streamDeckProfile is a zip. Inside, one manifest.json per
page, with actions keyed by position:

  { "Name": "Streaming",
    "Actions": {
      "0,0": { "UUID": "com.elgato.streamdeck.system.hotkey",
               "States": [ { "Title": "Mute", "Image": "..." } ],
               "Settings": { "Hotkeys": [ ... ] } } } }

An extracted folder or a bare manifest.json works too, because
somebody who already unzipped it should not have to zip it up
again.

Standard library only: zipfile and json.
============================================================
"""

from __future__ import annotations

import base64
import json
import os
import re
import zipfile

from .layout import LayoutError, SHAPES

#: What an Elgato action turns into here. Only bindings that mean the same
#: thing on both sides are listed; a rough equivalent would be worse than
#: nothing, because a key that does almost the right thing is a key
#: somebody trusts.
ACTIONS = {
    "com.elgato.streamdeck.system.hotkey":      "win.keystroke",
    "com.elgato.streamdeck.system.text":        "clip.phrase",
    "com.elgato.streamdeck.system.open":        "win.launch",
    "com.elgato.streamdeck.system.website":     "win.launch",
    "com.elgato.streamdeck.system.commandline": "win.launch",
    "com.elgato.streamdeck.soundboard.playaudio": "sound.play",
    "com.elgato.streamdeck.system.playaudio":     "sound.play",
}

#: Recognised, and deliberately not mapped. Naming them means the report can
#: say "this needs OBS" instead of "unknown action", which is the difference
#: between a person knowing what to do next and not.
NEEDS_INTEGRATION = {
    "com.elgato.obsstudio": "OBS, which RemapWrap does not connect to yet",
    "com.elgato.twitch": "Twitch, which needs an account RemapWrap does not ask for",
    "com.elgato.streamdeck.profile": "switching Stream Deck profiles",
    "com.elgato.streamdeck.page": "Stream Deck folders",
}

#: A key is this many cells, so an imported board keeps the proportions of
#: the hardware it came from.
CELL = 4
GAP = 1


def _manifests(source):
    """
    Every page manifest in a profile, whatever shape the source is in.

    Returns a list of (name, parsed) pairs. A profile with folders has more
    than one; the outer manifest that only names the current page is
    skipped, because it has no actions to import.
    """
    found = []

    if os.path.isfile(source) and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as zf:
            for entry in sorted(zf.namelist()):
                if not entry.lower().endswith("manifest.json"):
                    continue
                try:
                    found.append((entry, json.loads(zf.read(entry).decode("utf-8"))))
                except (ValueError, UnicodeDecodeError):
                    # One unreadable page must not lose the others.
                    continue
    elif os.path.isfile(source):
        with open(source, encoding="utf-8") as fh:
            found.append((os.path.basename(source), json.load(fh)))
    elif os.path.isdir(source):
        for root, _dirs, files in os.walk(source):
            for name in sorted(files):
                if name.lower() != "manifest.json":
                    continue
                path = os.path.join(root, name)
                try:
                    with open(path, encoding="utf-8") as fh:
                        found.append((os.path.relpath(path, source), json.load(fh)))
                except (ValueError, UnicodeDecodeError):
                    continue
    else:
        raise LayoutError("No such profile: {}".format(source))

    pages = [(n, m) for n, m in found if isinstance(m, dict) and m.get("Actions")]
    if not pages:
        raise LayoutError(
            "Found no pages with any actions in {}. If this is a plugin "
            "rather than an exported profile, export the profile from Stream "
            "Deck first: right-click it and choose Export.".format(source))
    return pages


def _title(action):
    for state in action.get("States") or []:
        if isinstance(state, dict) and state.get("Title"):
            return str(state["Title"]).replace("\n", " ").strip()
    return str(action.get("Name") or "").strip()


def _image(action):
    """
    The picture on the key, as a data URI.

    Stream Deck stores it already base64 encoded, sometimes with the data
    URI prefix and sometimes without. Both are accepted; anything that is
    not plausibly an image is dropped rather than embedded blind.
    """
    for state in action.get("States") or []:
        if not isinstance(state, dict):
            continue
        raw = state.get("Image")
        if not raw or not isinstance(raw, str):
            continue
        if raw.startswith("data:image/"):
            return raw
        cleaned = re.sub(r"\s+", "", raw)
        if len(cleaned) < 32:
            continue
        try:
            head = base64.b64decode(cleaned[:24] + "==", validate=False)
        except Exception:
            continue
        if head.startswith(b"\x89PNG"):
            return "data:image/png;base64," + cleaned
        if head.startswith(b"\xff\xd8"):
            return "data:image/jpeg;base64," + cleaned
        if head.startswith(b"<svg") or head.startswith(b"<?xml"):
            return "data:image/svg+xml;base64," + cleaned
    return ""


def _hotkey(settings):
    """
    A Stream Deck hotkey turned into the combination this presses.

    The stored shape is a list of records carrying the modifier flags and a
    virtual key code. Where the key cannot be worked out the whole binding
    is refused rather than guessed at, because half a shortcut is a key
    that does the wrong thing.
    """
    keys = settings.get("Hotkeys") or []
    if not keys and settings.get("VirtualKey") is not None:
        keys = [settings]
    for entry in keys:
        if not isinstance(entry, dict):
            continue
        parts = []
        if entry.get("Ctrl"):
            parts.append("ctrl")
        if entry.get("Shift"):
            parts.append("shift")
        if entry.get("Alt"):
            parts.append("alt")
        if entry.get("Cmd") or entry.get("Win"):
            parts.append("win")
        name = VIRTUAL_KEYS.get(entry.get("VirtualKey"))
        if not name:
            continue
        parts.append(name)
        return "+".join(parts)
    return ""


#: Windows virtual key codes, for the ones a shortcut is actually built
#: from. Anything absent means the binding is reported rather than guessed.
VIRTUAL_KEYS = {
    8: "backspace", 9: "tab", 13: "enter", 19: "pause", 20: "capslock",
    27: "esc", 32: "space", 33: "pgup", 34: "pgdown", 35: "end", 36: "home",
    37: "left", 38: "up", 39: "right", 40: "down", 45: "insert", 46: "delete",
    91: "win", 93: "menu",
    186: ";", 187: "=", 188: ",", 189: "-", 190: ".", 191: "/", 192: "`",
    219: "[", 220: "\\", 221: "]", 222: "'",
}
for _n in range(48, 58):
    VIRTUAL_KEYS[_n] = chr(_n)                      # 0-9
for _n in range(65, 91):
    VIRTUAL_KEYS[_n] = chr(_n).lower()              # a-z
for _n in range(112, 136):
    VIRTUAL_KEYS[_n] = "f{}".format(_n - 111)       # F1-F24
for _n in range(96, 106):
    VIRTUAL_KEYS[_n] = "numpad{}".format(_n - 96)


def _bind(action):
    """
    (command, arg, note). note is set when something could not be carried.
    """
    uuid = str(action.get("UUID") or "")
    settings = action.get("Settings") or {}
    if not isinstance(settings, dict):
        settings = {}

    for prefix, why in NEEDS_INTEGRATION.items():
        if uuid.startswith(prefix):
            return "", "", "needs " + why

    command = ACTIONS.get(uuid)
    if not command:
        return "", "", "no equivalent for {}".format(uuid or "an unnamed action")

    if command == "win.keystroke":
        combo = _hotkey(settings)
        if not combo:
            return "", "", "a hotkey whose keys could not be read"
        return command, combo, ""

    if command == "clip.phrase":
        text = settings.get("text") or settings.get("Text") or ""
        if not text:
            return "", "", "a text action with no text in it"
        return command, str(text), ""

    if command == "win.launch":
        target = (settings.get("path") or settings.get("Path") or
                  settings.get("url") or settings.get("URL") or
                  settings.get("openInBrowser") or "")
        if not target:
            return "", "", "an open action with nothing to open"
        return command, str(target), ""

    if command == "sound.play":
        path = settings.get("path") or settings.get("Path") or ""
        if not path:
            return "", "", "a sound action with no file"
        return command, os.path.basename(str(path)), ""

    return command, "", ""


def read(source, name=None):
    """
    Turn a Stream Deck profile into a RemapWrap profile.

    Returns (profile, report). The report lists everything that could not be
    carried across, in plain sentences, because a silent partial import is
    the worst outcome available: a board that looks finished and is not.
    """
    pages_in = _manifests(source)
    report = []
    pages_out = []
    counter = [0]

    for page_name, manifest in pages_in:
        actions = manifest.get("Actions") or {}
        placed = []
        max_col = max_row = 0

        for where, action in sorted(actions.items()):
            if not isinstance(action, dict):
                continue
            m = re.match(r"^\s*(\d+)\s*,\s*(\d+)\s*$", str(where))
            if not m:
                report.append("Skipped an action at {!r}: not a position."
                              .format(where))
                continue
            col, row = int(m.group(1)), int(m.group(2))
            max_col, max_row = max(max_col, col), max(max_row, row)

            command, arg, note = _bind(action)
            label = _title(action)
            counter[0] += 1
            key = {
                "id": "e{}".format(counter[0]),
                "type": "key",
                "behaviour": "press",
                "command": command,
                "label": (label or "KEY")[:16],
                "sub": "",
                "color": "#111820",
                "x": col * (CELL + GAP),
                "y": row * (CELL + GAP),
                "w": CELL, "h": CELL,
                "shape": "rounded",
            }
            if arg:
                key["arg"] = arg
            image = _image(action)
            if image:
                key["image"] = image
            placed.append(key)

            if note:
                report.append('"{}" at {},{} came across with its name and '
                              'picture but no binding: {}.'
                              .format(label or "an untitled key", col, row, note))

        if not placed:
            continue
        pages_out.append({
            "name": str(manifest.get("Name") or page_name or
                        "Page {}".format(len(pages_out) + 1))[:40],
            "cols": (max_col + 1) * (CELL + GAP),
            "rows": (max_row + 1) * (CELL + GAP),
            "keys": placed,
        })

    if not pages_out:
        raise LayoutError("Nothing in {} could be placed on a board.".format(source))

    profile = {
        "schema": 1,
        "name": name or str(pages_in[0][1].get("Name") or "Imported")[:40],
        "pages": pages_out,
    }
    bound = sum(1 for p in pages_out for k in p["keys"] if k["command"])
    total = sum(len(p["keys"]) for p in pages_out)
    report.insert(0, "{} of {} keys came across with a working binding."
                  .format(bound, total))
    return profile, report
