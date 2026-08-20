```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                            ║
║                          ██╗  ██╗███████╗██╗   ██╗           ██╗                           ║
║                          ██║ ██╔╝██╔════╝╚██╗ ██╔╝           ██║                           ║
║                          █████╔╝ █████╗   ╚████╔╝ █████╗     ██║                           ║
║                          ██╔═██╗ ██╔══╝    ╚██╔╝  ╚════╝██   ██║                           ║
║                          ██║  ██╗███████╗   ██║         ╚█████╔╝                           ║
║                          ╚═╝  ╚═╝╚══════╝   ╚═╝          ╚════╝                            ║
║                                                                                            ║
║                    your tab, your notes, and any key plays the next one                    ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```

[![PyPI](https://img.shields.io/pypi/v/keyj)](https://pypi.org/project/keyj/)
[![Python](https://img.shields.io/pypi/pyversions/keyj)](https://pypi.org/project/keyj/)
[![Licence](https://img.shields.io/pypi/l/keyj)](../LICENSE)

Key-J on the command line. Guitar tablature goes in, notes come out, and any
keystroke plays the next one.

```
pip install keyj

keyj tab solo.txt -o song.txt      tablature to notes
keyj show song.txt                 what is in a file
keyj render song.txt out.wav       notes to audio
keyj play song.txt                 notes, played by typing
```

## Why a command line version

The [browser app](https://f-keys.com/keyj/) is where a song gets built: paste a
tab, hear it, fix it. That is a workbench, and you want it once.

Afterwards you have the song, and what you want is the smallest possible thing
that plays it. No window, no autostart, no login item. A process you start when
you want it and stop with Ctrl-C, which `ps` can see and `kill` can end.

## What it does not do

`keyj play` installs a system-wide keyboard listener, which is the same
machinery a keylogger uses. So the design point is this:

**It does not need to know which key you pressed.**

In sequence mode every key plays the next note. Which key is irrelevant, so the
identity of the key is never stored, never written, never counted per-key and
never sent anywhere. The callback asks a key one question - is it a modifier,
so that Shift does not eat a note - and then discards it. There is no buffer of
keystrokes to leak, because one is never built.

That is a structural property rather than a promise. It is nine lines, in
`src/keyj/play.py`, and you should read them before installing this.

## Dependencies

`tab`, `render` and `show` are standard library only and never touch your
keyboard. `play` is the one command that needs anything:

```
pip install 'keyj[play]'
```

| | |
|---|---|
| macOS | needs Accessibility permission, granted to your terminal |
| Linux / X11 | works as installed |
| Linux / Wayland | **no global hook exists.** `keyj play` says so and exits |
| Windows | works unless a security tool blocks the hook |

## The file format

A sequence is note names separated by whitespace, with `#` comments stripped on
the way in.

```
# Key-J sequence - 7 notes from tab
A3 E4 F#4 E4 D4 B3 A3
```

That is the same format the browser app's **Save .txt** writes and **Load .txt**
reads, and a file saved in either place pastes directly into the other's note
box. Anything that can emit a list of note names can feed Key-J.

## Tunings

Eight, by short name: `standard`, `dropd`, `eb`, `d`, `dadgad`, `openg`,
`7string`, `bass`. A capo is `--capo N`.

The reader states what it read - the tuning, how many strings, how many notes -
and a block whose line count does not match the tuning produces no notes and is
named in the report rather than guessed at. What it cannot catch is a tab that
is internally consistent and simply wrong; bad frets convert cleanly into bad
notes, and only your ear will find that.

## Tested against the browser

This package and `keyj/app.html` are two implementations of the same
conversions, and Key-J has already shipped defects that existed only because two
copies of one thing drifted apart. So `tests/test_parity.py` lifts the real
functions out of `app.html`, runs them under node against the same inputs, and
diffs the results.

```
python tests/test_parity.py
```

If node is not installed the parity checks skip and say so, because a check that
cannot run must not report success.

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
