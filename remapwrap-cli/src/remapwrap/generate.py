#!/usr/bin/env python3
"""
============================================================
remapwrap.generate - a surface built from what you already
                     have
F-Keys | www.f-keys.com
------------------------------------------------------------
Building a forty-pad soundboard by dragging is twenty minutes
of dragging. The folder of samples already knows what the pads
are; this reads it.

  soundboard(folder)   a pad per sound file
  mixer(apps)          a dial per application, plus a master
  deck(pairs)          a key per label and keystroke

Every generator returns a layout that passes layout.check, or
raises with the reason it cannot.

No dependencies. Standard library only.
============================================================
"""

from __future__ import annotations

import os

from .layout import (LayoutError, board, control, first_free, place)

SOUND_TYPES = (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac")

#: Colours that stay distinguishable next to each other on a phone, and
#: that a label can sit on in either black or white.
PALETTE = ["#2a1216", "#161a2a", "#12211a", "#1c1626", "#241a10", "#101a1e"]


def _label(text, limit=16):
    """
    A label that fits a key without being cut mid-word.

    Truncating at a fixed character count turned "commercial break" - the
    default a streamer actually wants - into "COMMERCIAL BRE". A label is
    read at a glance, so it keeps whole words and drops the rest.
    """
    text = " ".join(str(text).replace("_", " ").replace("-", " ").split())
    text = text.upper()
    if len(text) <= limit:
        return text
    cut = text[:limit + 1].rsplit(" ", 1)[0]
    # One long word has no boundary to break on, and the slice above
    # would hand back limit + 1 characters. Cut it.
    return cut if 0 < len(cut) <= limit else text[:limit]


def _fit(count, w, h, cols_max=48, rows_max=32):
    """
    The best board that holds this many controls with air between them.

    Taking the first size that fits produced an eight by twenty-eight
    ribbon for five sliders. A phone is about one to two, so the candidate
    closest to that wins, and among equals the smaller one does.
    """
    target = 1.9          # height over width, roughly a phone in the hand
    best = None
    for cols in range(6, cols_max + 1, 2):
        per_row = cols // (w + 1)
        if not per_row:
            continue
        rows_needed = -(-count // per_row) * (h + 1) + 1
        if rows_needed > rows_max:
            continue
        rows = max(8, rows_needed)
        score = (abs((rows / float(cols)) - target), cols * rows)
        if best is None or score < best[0]:
            best = (score, cols, rows)
    if best is None:
        raise LayoutError(
            "{} controls of {}x{} will not fit on any board this supports; "
            "split them across two layouts.".format(count, w, h))
    return best[1], best[2]


def soundboard(folder, label_from_name=True):
    """A pad for every sound file in a folder."""
    if not os.path.isdir(folder):
        raise LayoutError("No such folder: {}".format(folder))

    files = sorted(f for f in os.listdir(folder)
                   if f.lower().endswith(SOUND_TYPES))
    if not files:
        raise LayoutError(
            "No sound files in {}. Looked for {}."
            .format(folder, ", ".join(SOUND_TYPES)))

    cols, rows = _fit(len(files), 4, 4)
    lay = board(cols, rows)
    for i, name in enumerate(files):
        stem = os.path.splitext(name)[0]
        label = _label(stem) if label_from_name else "PAD {}".format(i + 1)
        place(lay, control(
            type="pad", command="sound.play", arg=name,
            label=label, sub="soundboard",
            color=PALETTE[i % len(PALETTE)]))
    return lay


def mixer(apps, master=True, mic=True):
    """
    A slider per application, and the two that are always wanted.

    `apps` is a list of process names - what Windows calls them, so
    "Discord" rather than "Discord Voice". The surface cannot know what is
    running on the machine it will be used on, so the caller says.
    """
    apps = [a for a in (apps or []) if a.strip()]
    total = len(apps) + (1 if master else 0) + (1 if mic else 0)
    if not total:
        raise LayoutError("Name at least one application, or ask for the "
                          "master and microphone.")

    cols, rows = _fit(total, 3, 8)
    lay = board(cols, rows)

    if master:
        place(lay, control(type="slider", command="audio.master",
                           label="MASTER", sub="all sound",
                           color="#12211a"))
    if mic:
        place(lay, control(type="dial", command="audio.mic.gain",
                           label="MIC", sub="gain", color="#2a1216",
                           w=4, h=4, shape="circle"))
    for i, app in enumerate(apps):
        place(lay, control(type="slider", command="audio.app", arg=app,
                           label=_label(app, 14), sub="app volume",
                           color=PALETTE[i % len(PALETTE)]))
    return lay


def deck(pairs):
    """
    A key per (label, keystroke) pair.

    The oldest use there is: somebody who wants twelve shortcuts they
    cannot remember, on glass, next to the keyboard.
    """
    pairs = list(pairs or [])
    if not pairs:
        raise LayoutError("Give at least one label and keystroke.")

    cols, rows = _fit(len(pairs), 4, 4)
    lay = board(cols, rows)
    for i, pair in enumerate(pairs):
        label, keys = (list(pair) + [""])[:2]
        place(lay, control(
            type="key", command="win.keystroke", arg=keys,
            label=_label(label), sub=str(keys),
            color=PALETTE[i % len(PALETTE)]))
    return lay
