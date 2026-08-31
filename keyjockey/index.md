# keyjockey

> Tablature in, notes out.

Canonical: https://f-keys.com/keyjockey/

Reads guitar tablature and gives you notes: eight tunings, capo offsets, MIDI numbers and frequencies. The same reader Key-J runs in the browser, as a package.

npm install keyjockey · MIT · 8 tunings · also on PyPI as keyj

## What it does

Reads guitar tablature and converts notes. Eight tunings, capo offsets, MIDI
and frequency.

**npm install keyjockey**
keyjockey.parseTab(tab, "Standard (EADGBe)", 0).notes;
keyjockey.parseTab(tab, "Drop D", 2).notes; // capo 2
keyjockey.midiToName(60); // "C4"
keyjockey.nameToFreq("A4"); // 440
Lifted, not rewritten
This is the same reader [Key-J](https://f-keys.com/keyj/) runs in the browser, and
the Python half is on PyPI as keyj. The npm package is generated
from app.html at build time rather than written a third time, and
the build fails if the app moves and the package does not.

Key-J has already shipped three defects that existed only because two copies
of one thing drifted. A third copy would have been a third chance.

## Errors come back, they are not thrown

A tab in a tuning that does not exist returns .error and no
notes. Text that is not tablature returns zero notes rather than guessing at
one.

## How it works

## What it does

## Specifications

| Field | Value |
| --- | --- |
| Install | npm install keyjockey |
| Licence | MIT |
| Tunings | 8, with capo offsets |
| Source | vince-gonzalez/f-keys |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
