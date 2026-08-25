```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                            ║
║       ██████╗ ███████╗███╗   ███╗ █████╗ ██████╗ ██╗    ██╗██████╗  █████╗ ██████╗         ║
║       ██╔══██╗██╔════╝████╗ ████║██╔══██╗██╔══██╗██║    ██║██╔══██╗██╔══██╗██╔══██╗        ║
║       ██████╔╝█████╗  ██╔████╔██║███████║██████╔╝██║ █╗ ██║██████╔╝███████║██████╔╝        ║
║       ██╔══██╗██╔══╝  ██║╚██╔╝██║██╔══██║██╔═══╝ ██║███╗██║██╔══██╗██╔══██║██╔═══╝         ║
║       ██║  ██║███████╗██║ ╚═╝ ██║██║  ██║██║     ╚███╔███╔╝██║  ██║██║  ██║██║             ║
║       ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝      ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝             ║
║                                                                                            ║
║                             your phone is the control surface                              ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```
[![PyPI](https://img.shields.io/pypi/v/remapwrap)](https://pypi.org/project/remapwrap/)
[![Python](https://img.shields.io/pypi/pyversions/remapwrap)](https://pypi.org/project/remapwrap/)
[![Licence](https://img.shields.io/pypi/l/remapwrap)](../LICENSE)

RemapWrap layouts, built by machine. A folder of samples becomes a soundboard,
a list of applications becomes a mixer, a list of shortcuts becomes a deck.

```
pip install remapwrap

remapwrap soundboard ./samples -o board.json     a pad per sound file
remapwrap mixer Discord Spotify chrome -o mix.json   a slider per application
remapwrap deck "Copy:ctrl+c" "Paste:ctrl+v" -o keys.json
remapwrap check board.json                       would this work
remapwrap describe board.json                    what is in it
```

Open the RemapWrap dashboard, import the file, and the surface is on your
phone.

## Why this exists

A forty-pad soundboard is twenty minutes of dragging, and the folder of samples
already knows what the pads are. So does the list of applications currently
playing audio, and so does the config file where somebody keeps their
shortcuts. Every one of those is a layout that a person should not have to
build by hand.

The dashboard is where a surface gets adjusted — moved, recoloured, tried. This
is where one gets made.

## What a layout is

One JSON document. Cells, not pixels, so the same layout fits a phone held
either way.

```json
{"cols": 12, "rows": 21, "keys": [
  {"id": "k1", "type": "pad", "behaviour": "trigger",
   "command": "sound.play", "arg": "airhorn.wav",
   "label": "AIRHORN", "sub": "soundboard", "color": "#2a1216",
   "x": 0, "y": 0, "w": 4, "h": 4, "shape": "rect"}
]}
```

Seven control types — `key`, `toggle`, `pad`, `dial`, `slider`, `timer`,
`input` — four shapes,
and a command from a fixed catalogue of twenty-nine. Read or write it with
anything; it is JSON, and this package imports nothing that is not in the
standard library.

Every command in `COMMANDS` is one the surface actually carries out —
including `speak.text`, which is what makes a board of keys a way of
talking rather than only a way of pressing things, `mouse.*` for stepping a
pointer around without holding a mouse, and `clip.phrase`, which puts a
whole sentence on the clipboard and pastes it — so what arrives is what was
written, emoji and all, which typing it key by key cannot promise. Eight more are named in
`PLANNED` and deliberately kept out of the catalogue:
`obs.*` needs an obs-websocket connection and `stream.*` needs a Twitch
token, and a list where a third of the entries exist only to announce their
own absence is a worse list than a shorter true one. Binding one is
reported as its own kind of problem, not as a typo:

```
REC is bound to 'obs.record', which is planned but not built.
It would be a key that does nothing.
```

## The rules are written twice on purpose

The dashboard enforces these rules in JavaScript. This package enforces them
again in Python, and that is not duplication for its own sake: two
implementations of one rule set disagree exactly where one of them is wrong.
Running them against each other has found more defects in this codebase than
reading either one ever did.

`check` returns sentences rather than codes, because the person reading them is
the person who has to fix it:

```
- BAD DIAL is a dial bound to 'capture.shot', which takes no value. A dial cannot fire it.
- BAD KEY is a key bound to 'audio.master', which reports a value. Use a dial or a slider.
- OFF BOARD sits at 22,14 and is 4x4, which runs off a 24x16 board.
- TYPO is bound to 'not.a.command', which is not a command.
- ELLIPSE is a circle 4x6; a circle has one dimension.
- 'BAD DIAL' and 'OVER A' overlap.
```

A generator that cannot produce a valid layout raises instead of writing a
broken one.

## As a library

A `timer` counts down from its `arg` in seconds, or up when it is blank. An
`input` opens the phone's own keyboard and what is written lands on the PC
through the clipboard, so an accent or an emoji arrives as it was written.
Neither carries a command, and `check` says so if one is given.

A `toggle` can carry a second face for when it is on, so a key says what is
true rather than only what it does:

```json
{"type": "toggle", "command": "audio.mic.mute", "label": "MIC LIVE",
 "whenOn": {"label": "MUTED", "color": "#2a1216"}}
```

```python
from remapwrap import generate, layout

board = generate.soundboard("./samples")
layout.place(board, layout.control(
    type="slider", command="audio.master", label="MASTER"))

problems = layout.check(board)
if not problems:
    layout.save(board, "board.json")
```

`place` finds a free spot and leaves a cell of air around it, because a surface
where every key touches its neighbour is a surface people press two of at once.

## What it does not do

It does not talk to your phone, press a key, or open a socket. It writes the
document a surface is made of, and the RemapWrap dashboard does the rest. There
is no network code in this package at all.

## Dependencies

None. Standard library, Python 3.8 and up.

---

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║      ███████╗      ██╗  ██╗███████╗██╗   ██╗███████╗       ║
║      ██╔════╝      ██║ ██╔╝██╔════╝╚██╗ ██╔╝██╔════╝       ║
║      █████╗  █████╗█████╔╝ █████╗   ╚████╔╝ ███████╗       ║
║      ██╔══╝  ╚════╝██╔═██╗ ██╔══╝    ╚██╔╝  ╚════██║       ║
║      ██║           ██║  ██╗███████╗   ██║   ███████║       ║
║      ╚═╝           ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝       ║
║                                                            ║
║               ·   C  R  E  A  T  I  V  E   ·               ║
║                                                            ║
║          ────────────────────────────────────────          ║
║                                                            ║
║                      Vincent Gonzalez                      ║
║                         f-keys.com                         ║
║                 ORCID 0009-0005-3640-014X                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

Part of [F-Keys](https://f-keys.com) — independent hardware, software
and internet products. See the [working log](https://f-keys.com/log/)
and [live status](https://f-keys.com/status/).

Part of [F-Keys](https://f-keys.com) — independent hardware, software
and internet products. See the [working log](https://f-keys.com/log/)
and [live status](https://f-keys.com/status/).
