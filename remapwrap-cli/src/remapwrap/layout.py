#!/usr/bin/env python3
"""
============================================================
remapwrap.layout - what a control surface is, as data
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

A RemapWrap layout is a JSON document describing controls on a
board. The dashboard writes one by hand, a person dragging
things around; this writes one by machine, from whatever
already describes the work - a folder of samples, a list of
applications, a configuration file.

That is the difference between an application and something
people build on. A soundboard with forty pads is twenty
minutes of dragging or one line of Python.

WHAT A LAYOUT IS

  cols, rows   the board, in cells
  keys         controls, each carrying where it is and what it
               does

  {"cols": 24, "rows": 16, "keys": [
    {"id": "k1", "type": "pad", "behaviour": "trigger",
     "command": "sound.play", "arg": "airhorn.wav",
     "label": "AIRHORN", "sub": "soundboard",
     "color": "#1a1426", "x": 1, "y": 1, "w": 4, "h": 4,
     "shape": "rect"}
  ]}

THE RULES ARE HERE TWICE ON PURPOSE

The browser enforces the same rules in JavaScript. Writing
them again in Python is not duplication for its own sake - two
implementations of one rule set disagree exactly where one of
them is wrong, and running them against each other has caught
more defects in this codebase than reading either ever did.

No dependencies. Standard library only.
============================================================
"""

from __future__ import annotations

import json
import re

#: `timer` and `input` carry no command: a timer counts and an input opens
#: the phone's own keyboard. Both are checked for that below, because a
#: generated board with a command on a timer would be a control bound to
#: something it cannot fire.
TYPES = ("key", "toggle", "pad", "dial", "slider", "timer", "input")

#: Types that do their own job rather than firing something from the
#: catalogue.
SELF_CONTAINED = ("timer", "input")
SHAPES = ("rect", "rounded", "pill", "circle")

BEHAVIOURS = {
    "key":    ("press", "double", "hold", "long"),
    "toggle": ("latch", "momentary"),
    "pad":    ("trigger", "retrigger", "choke"),
    "dial":   ("relative", "absolute", "detent"),
    "slider": ("absolute", "relative"),
    "timer":  ("countdown",),
    "input":  ("compose",),
}

#: Commands that report a value. Only a dial or a slider may carry one, and
#: a key may not: a button cannot express a position.
CONTINUOUS = (
    "audio.master", "audio.mic.gain", "audio.desktop", "audio.app",
)

#: Everything a control may be bound to. A command outside this list is a
#: typo as far as the surface is concerned, and a typo that reaches the
#: phone is a control that does nothing when pressed.
COMMANDS = {
    "audio.mic.mute", "audio.mic.ptt", "audio.mic.gain", "audio.master",
    "audio.desktop", "audio.app", "audio.duck",
    "sound.play", "sound.stop",
    "capture.clip", "capture.shot", "capture.window",
    "win.keystroke", "win.text", "win.launch", "win.desktop", "win.media",
    "macro.sequence",
    # The computer says what a key is for. This is the command that makes a
    # board of keys a way of talking rather than only a way of pressing
    # things, and it is why the free tier looks the way it does.
    "speak.text", "speak.stop",
    # The pointer and the clipboard. Both matter more for somebody using a
    # switch than for a streamer: stepping a pointer is how you use a mouse
    # without holding one, and clip.phrase is the reliable way to put a whole
    # sentence into another program - win.text types it key by key, which
    # mangles anything outside a US layout and cannot make an emoji at all.
    "mouse.click", "mouse.move", "mouse.scroll", "mouse.hold",
    "clip.copy", "clip.cut", "clip.paste", "clip.set", "clip.phrase",
}

#: Named so nobody proposes them twice, and deliberately not in COMMANDS.
#: obs.* needs an obs-websocket connection and stream.* needs a Twitch
#: token; both are integrations rather than commands. Listing them as real
#: meant a third of the catalogue existed only to announce its own absence,
#: which is a worse catalogue than a shorter true one.
PLANNED = {
    "obs.stream", "obs.record", "obs.replay", "obs.scene", "obs.transition",
    "obs.studio", "stream.marker", "stream.ad",
}

#: What the surface can actually carry out today. A command outside this set
#: is real - it is in the catalogue, the dashboard offers it, and a layout
#: carrying it is not malformed - but pressing it does nothing yet, and a
#: generator that quietly produced a board of those would be lying.
#:
#: obs.* needs an obs-websocket connection and stream.* needs a Twitch
#: token. Both are integrations rather than commands.
IMPLEMENTED = {
    "audio.master", "audio.desktop", "audio.app", "audio.mic.gain",
    "audio.mic.mute", "audio.mic.ptt", "audio.duck",
    "sound.play", "sound.stop",
    "win.keystroke", "win.text", "win.launch", "win.desktop", "win.media",
    "capture.clip", "capture.shot", "capture.window",
    "macro.sequence",
    "speak.text", "speak.stop",
    # The pointer and the clipboard. Both matter more for somebody using a
    # switch than for a streamer: stepping a pointer is how you use a mouse
    # without holding one, and clip.phrase is the reliable way to put a whole
    # sentence into another program - win.text types it key by key, which
    # mangles anything outside a US layout and cannot make an emoji at all.
    "mouse.click", "mouse.move", "mouse.scroll", "mouse.hold",
    "clip.copy", "clip.cut", "clip.paste", "clip.set", "clip.phrase",
}

DEFAULT_SIZE = {
    "key":    (4, 4, "rounded"),
    "toggle": (4, 4, "rounded"),
    "pad":    (4, 4, "rect"),
    "dial":   (4, 4, "circle"),
    "slider": (3, 8, "pill"),
    # A timer shows mm:ss at 30px and needs the room for it.
    "timer":  (6, 4, "rounded"),
    "input":  (6, 4, "rounded"),
}


class LayoutError(Exception):
    """A layout that would not work if it reached a phone."""


# ── the pieces ───────────────────────────────────────────────

def control(type="key", command="", label="", **extra):
    """One control, with the defaults its type implies."""
    if type not in TYPES:
        raise LayoutError("{!r} is not a control type; expected one of {}"
                          .format(type, ", ".join(TYPES)))
    w, h, shape = DEFAULT_SIZE[type]
    item = {
        "id": extra.pop("id", None) or _next_id(),
        "type": type,
        "behaviour": extra.pop("behaviour", BEHAVIOURS[type][0]),
        "command": command,
        "label": label or type.upper(),
        "sub": extra.pop("sub", ""),
        "color": extra.pop("color", "#c8c4bc"),
        "x": extra.pop("x", 0), "y": extra.pop("y", 0),
        "w": extra.pop("w", w), "h": extra.pop("h", h),
        "shape": extra.pop("shape", shape),
    }
    item.update(extra)
    return item


_counter = {"n": 0}


def _next_id():
    _counter["n"] += 1
    return "k{}".format(_counter["n"])


def board(cols=24, rows=16, keys=None):
    return {"cols": cols, "rows": rows, "keys": list(keys or [])}


# ── placing things without them landing on each other ────────

def overlaps(a, b):
    return (a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"] and
            a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"])


def first_free(lay, w, h, gap=1):
    """
    Somewhere this fits, scanning across and then down.

    A gap of one cell is left between controls by default, because a
    surface where every key touches its neighbour is a surface people press
    two of at once.
    """
    for y in range(lay["rows"] - h + 1):
        for x in range(lay["cols"] - w + 1):
            box = {"x": x, "y": y, "w": w + gap, "h": h + gap}
            if not any(overlaps(box, k) for k in lay["keys"]):
                return x, y
    return None


def place(lay, item):
    """Add a control, finding it a home. Raises if the board is full."""
    spot = first_free(lay, item["w"], item["h"])
    if spot is None:
        raise LayoutError(
            "no room for {!r}: a {}x{} control does not fit on what is left "
            "of a {}x{} board".format(item["label"], item["w"], item["h"],
                                      lay["cols"], lay["rows"]))
    item["x"], item["y"] = spot
    lay["keys"].append(item)
    return item


# ── is this layout actually usable ───────────────────────────

def check(lay):
    """
    Every reason a layout would not work, as a list of sentences.

    Returns an empty list for a good layout. Nothing is raised, because a
    caller usually wants all the problems rather than the first one.
    """
    problems = []

    if not isinstance(lay, dict) or "keys" not in lay:
        return ["That is not a layout: expected an object with a keys list."]

    cols = lay.get("cols", 24)
    rows = lay.get("rows", 16)
    if cols < 1 or rows < 1:
        problems.append("The board is {}x{}, which has no area.".format(cols, rows))

    seen_ids = set()
    for i, k in enumerate(lay["keys"]):
        where = k.get("label") or k.get("id") or "control {}".format(i + 1)

        kid = k.get("id")
        if not kid:
            problems.append("{} has no id.".format(where))
        elif kid in seen_ids:
            problems.append("Two controls share the id {!r}; the phone would "
                            "only ever address one of them.".format(kid))
        else:
            seen_ids.add(kid)

        ktype = k.get("type", "key")
        if ktype not in TYPES:
            problems.append("{} is a {!r}, which is not a control type."
                            .format(where, ktype))
            continue

        if k.get("shape") and k["shape"] not in SHAPES:
            problems.append("{} has shape {!r}; expected one of {}."
                            .format(where, k["shape"], ", ".join(SHAPES)))

        if k.get("behaviour") and k["behaviour"] not in BEHAVIOURS[ktype]:
            problems.append("{} is a {} with behaviour {!r}, which a {} "
                            "cannot do.".format(where, ktype, k["behaviour"],
                                                ktype))

        cmd = k.get("command", "")
        if ktype in SELF_CONTAINED and cmd:
            problems.append("{} is a {} and does not fire a command, but it "
                            "is bound to {!r}.".format(where, ktype, cmd))
        elif cmd and cmd in PLANNED:
            problems.append("{} is bound to {!r}, which is planned but not "
                            "built. It would be a key that does nothing."
                            .format(where, cmd))
        elif cmd and cmd not in COMMANDS:
            problems.append("{} is bound to {!r}, which is not a command."
                            .format(where, cmd))


        # The rule the browser enforces by hiding the options: a dial
        # reports a value and can only drive something that takes one.
        wants_value = ktype in ("dial", "slider")
        if cmd and wants_value and cmd not in CONTINUOUS:
            problems.append("{} is a {} bound to {!r}, which takes no value. "
                            "A dial cannot fire it.".format(where, ktype, cmd))
        if cmd and not wants_value and cmd in CONTINUOUS:
            problems.append("{} is a {} bound to {!r}, which reports a value. "
                            "Use a dial or a slider.".format(where, ktype, cmd))

        if k.get("shape") == "circle" and k.get("w") != k.get("h"):
            problems.append("{} is a circle {}x{}; a circle has one dimension."
                            .format(where, k.get("w"), k.get("h")))

        for field in ("x", "y", "w", "h"):
            if not isinstance(k.get(field), int):
                problems.append("{} has no {}.".format(where, field))
                break
        else:
            if k["w"] < 1 or k["h"] < 1:
                problems.append("{} is {}x{}, which has no area."
                                .format(where, k["w"], k["h"]))
            if k["x"] < 0 or k["y"] < 0 or \
               k["x"] + k["w"] > cols or k["y"] + k["h"] > rows:
                problems.append(
                    "{} sits at {},{} and is {}x{}, which runs off a {}x{} "
                    "board.".format(where, k["x"], k["y"], k["w"], k["h"],
                                    cols, rows))

        on = k.get("whenOn")
        if on is not None:
            if not isinstance(on, dict):
                problems.append("{} has a whenOn that is not an object."
                                .format(where))
            elif ktype not in ("toggle",):
                # Only something that latches has an "on" to have a face for.
                problems.append("{} is a {}, which is never on, so whenOn "
                                "would never show.".format(where, ktype))
            elif on.get("color") and not re.match(r"^#[0-9a-fA-F]{6}$",
                                                  on["color"]):
                problems.append("{} has a whenOn colour {!r}; expected #rrggbb."
                                .format(where, on["color"]))

        if k.get("color") and not re.match(r"^#[0-9a-fA-F]{6}$", k["color"]):
            problems.append("{} has colour {!r}; expected #rrggbb."
                            .format(where, k["color"]))

    placed = [k for k in lay["keys"]
              if all(isinstance(k.get(f), int) for f in ("x", "y", "w", "h"))]
    for i, a in enumerate(placed):
        for b in placed[i + 1:]:
            if overlaps(a, b):
                problems.append("{!r} and {!r} overlap."
                                .format(a.get("label"), b.get("label")))
    return problems


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(lay, path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(lay, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def describe(lay):
    """A layout in words, for somebody deciding whether to open it."""
    keys = lay.get("keys", [])
    kinds = {}
    for k in keys:
        kinds[k.get("type", "key")] = kinds.get(k.get("type", "key"), 0) + 1
    used = sum(k.get("w", 0) * k.get("h", 0) for k in keys)
    area = lay.get("cols", 24) * lay.get("rows", 16)
    lines = [
        "{} control(s) on a {}x{} board".format(
            len(keys), lay.get("cols", 24), lay.get("rows", 16)),
        "  " + ", ".join("{} {}{}".format(n, t, "" if n == 1 else "s")
                         for t, n in sorted(kinds.items())),
        "  {:.0f}% of the surface used".format(100.0 * used / area if area else 0),
    ]
    return "\n".join(lines)
