# Key-J

> Every keystroke plays a note, in any application.

Canonical: https://f-keys.com/keyj/

Every key you press plays a note, in whatever program is already in front of you. Type an email and hear a melody; import guitar tablature and watch it play itself on a live staff.

**1.6.0** · Browser, Windows, Linux · no account · pip install keyj for the reader

## What it does

Your keyboard becomes an instrument. Every keystroke plays a note, the notes land
on a staff as you go, and the session exports as a WAV. With global capture on it
hears your keys in any application.

## Tablature import

Paste guitar tablature, choose a tuning, and Key-J converts the frets to notes.
Sequence mode then plays that run one note per keystroke, so the pitches are handled
and what is left to you is timing and feel.

Eight tunings including drop D, Eb, DADGAD, seven-string and bass, with a capo
offset. Hammer-ons, slides and bends are read as the notes they land on. A block with
the wrong number of strings produces no notes and says how many it found, rather than
guessing a tuning silently.

## The keyboard

An on-screen keyboard shows which computer key plays which note, printed on the
key it triggers, so a wrong binding is visible rather than something you find by
ear. Keys light as they sound, from a keystroke or from a sequence.

Turn Build on and click keys to enter a run without typing a single note name -
which is the part that made entering a sequence miserable.

## Also

Seven tone presets from clean guitar to shred. MIDI import. Six play styles, four
waveforms, remappable keys and scale switching.

## On the command line

Once a song is in, the workbench is in the way. pip install keyj gives you
the same converter and the same player without the window.

**pip install keyj**
keyj tab solo.txt -o song.txt tablature in, note names out
keyj render song.txt out.wav the sequence, at a tempo
keyj show song.txt what is in a sequence
keyj play song.txt any keystroke plays the next note
tab, render and show are standard library only and
never touch your keyboard. play is the one part that needs a global hook, so it
is a separate install: pip install "keyj[play]". It runs in the foreground and
stops when you stop it — nothing is added to startup.

It never learns which key you pressed. In sequence mode any key advances, so the player
asks whether a key went down and discards everything else. There is no keystroke buffer in
it, which is the difference between an instrument and a keylogger.

The CLI is MIT. The desktop and browser apps are not — see
[the licence](https://github.com/vince-gonzalez/f-keys/blob/main/keyj/LICENSE).

## How it works

## What it does

## Specifications

| Field | Value |
| --- | --- |
| Version | 1.6.0 |
| Licence | Proprietary |
| Platforms | Browser, Windows, Linux |
| Source | vince-gonzalez/f-keys |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
