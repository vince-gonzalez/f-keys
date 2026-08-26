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
║                                  tablature in, notes out                                   ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```
Read guitar tablature and convert notes. Eight tunings, capo offsets, MIDI
and frequency.

This is the same reader the [Key-J](https://f-keys.com/keyj/) browser app
runs. It is **lifted from that app at build time**, not rewritten, so the
package and the page cannot answer differently. The Python half is on PyPI
as `keyj`, and a parity test diffs the two on every build.

## Install

```
npm install keyj
```

## Use

```js
var keyj = require("keyj");

keyj.parseTab(tab, "Standard (EADGBe)", 0).notes;   // [{ name: "E4", ... }]
keyj.parseTab(tab, "Drop D", 2).notes;              // capo 2, raised a tone
keyj.parseTyped("C4 E4 G4").notes;
keyj.midiToName(60);                                // "C4"
keyj.midiToFreq(69);                                // 440
keyj.nameToFreq("A4");                              // 440
keyj.looksLikeTab(text);                            // true / false
Object.keys(keyj.TUNINGS);                          // the eight
```

## What it does not do

No audio, no DOM, no recording. Those are the app. This is the pure part:
text in, notes out.

## Errors are returned, not thrown

A tab in a tuning that does not exist comes back with `.error` set and no
notes, rather than raising. Text that is not tablature returns zero notes
rather than guessing at one.

```js
keyj.parseTab(tab, "no such tuning", 0).error;   // "Unknown tuning."
```

## Tunings

Standard (EADGBe) · Drop D · Eb Standard · D Standard · DADGAD · Open G ·
7-string (B) · Bass (4)

Hammer-ons, slides and bends are read as the notes they land on. A block
with the wrong number of strings produces no notes and says how many it
found, rather than silently guessing a tuning.

## Licence

MIT.
