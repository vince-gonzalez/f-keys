# Key-J Manual

> How to use Key-J: sequence mode, tablature import, global capture, and what to check when something is not working.

Canonical: https://f-keys.com/keyj/manual/

What it does, how to switch it on, and what to check when it does not.

## Which Key-J are you holding

There are two, and the difference decides what the app can do at all.

| Field | Value |
| --- | --- |
| In a browser | Notes play while the Key-J tab has focus. Nothing else. |
| The desktop app | Notes play while you type in any application, once Global Capture is switched on. |

A browser cannot see keystrokes outside its own page, and it should not be able
to — a page that could read what you type into your bank would be a keylogger.
So the browser version is not a crippled desktop version, it is at its permanent
ceiling. The header tells you which one you have.

## Turning it on

**Browser:** click anywhere on the page and type. There is no switch, because
there is nothing to switch.

**Desktop:** the titlebar carries a **Global Capture** toggle with a badge
beside it. The badge reads **Window only** until you flip it, then **Global**.
If it reads **Hook unavailable**, the native key hook did not load and only the
Key-J window will be heard — on Linux that usually means the app needs
permission to read input devices, on Windows that a security tool blocked it.

Closing the window does not quit the desktop app. It keeps running in the tray so
your keys keep playing. Quit from the tray menu.

## The three tools

The centre of the window is tabbed, and one tool shows at a time. That is
deliberate: stacked, the three of them made the page four thousand pixels tall.

| Field | Value |
| --- | --- |
| Keyboard | Sixty-one keys, C2 to C7. Click them to hear them, or turn on **Build** and click a run in. |
| Grid | A step grid with nine kits, drums among them. Draw a pattern, then **Use as sequence**. |
| Tab & Sequence | Paste guitar tablature, or type note names. This is where a song gets in. |

## Sequence mode, which is the part people miss

Normally each key holds a fixed pitch: Q is one note, W is the next. That is fine
for noise and useless for a song.

**With a sequence loaded, every key plays the next note of it.** Which key you
press stops mattering. You are no longer playing pitches, you are playing
*rhythm*, and the melody is already handled. That is how typing an email
produces a solo.

The status line shows how many notes are loaded, where you are in them and what
comes next. **Restart** returns to the first note. **Sequence OFF** puts the
fixed bindings back.

## Getting a song in

**From tablature.** Paste it in, pick the tuning, set a capo if there is one,
press **Convert**. Eight tunings including drop D, E flat, DADGAD, seven string
and bass.

The importer states what it read: the tuning it used, how many strings it found,
how many notes it produced, and the name of anything it could not read. A block with
the wrong number of lines produces no notes and says so rather than guessing, because
a wrong note you cannot see is worse than a missing one you can.

What it cannot catch is a tab that is internally consistent and simply wrong. Bad
frets convert cleanly into bad notes, and nothing but your ear will find that.

**From note names.** Type or paste them into the note box:
E5 G5 B5 E6. Sharps and flats both work.

**From a file.** **Load .txt** takes a saved sequence, or any list of note
names. **Import MIDI** takes a MIDI file and uses its note order.

**From the keyboard or the grid.** Click a run in, then **Use as sequence**.

## Saving what you built

| Field | Value |
| --- | --- |
| Save .txt | The sequence as note names. The file pastes straight back into the note box, so saving and loading are one format. |
| Export WAV | The sequence rendered one note per beat at the BPM you set, through the tone you chose. |
| Export Session | A recording of what you actually typed, with your timing. A different thing, and rarely the one you want. |

Export WAV renders the *sequence*. Export Session renders *your typing*.
If you imported a tab and want to hear the song, you want Export WAV.

## Updates

Key-J does not check for updates on its own, and that is deliberate: it makes
no network requests at all, which is a promise worth more than the convenience.
The tray menu has **Check for updates**, which opens the releases page in your
browser when you ask it to.

## Sound

Seven tone presets, four waveforms, and sliders for attack, release, volume, reverb
and pitch. Six play styles: normal, staccato, vibrato, tremolo, arpeggio, legato. The
tone you have set is the tone the WAV export uses.

## The staff

Notes land on a treble staff as you play, scrolling to keep the newest in view.
Key-J spans C2 to C7, which no single treble staff shows at a readable size, so a note
outside the drawable range is pinned to the edge in orange with an arrow pointing the
way it went and its name beside it. A note that will not fit is reported, not dropped.

## When something is wrong

| Field | Value |
| --- | --- |
| No sound at all | Browsers will not start audio until you interact with the page. Click the page, then type. |
| Nothing plays outside the window | You are in the browser version, or Global Capture is off. Check the badge in the header. |
| Every key plays the same run | Sequence mode is on, and that is what it does. Press **Sequence OFF** for fixed pitches. |
| Notes cut off sharply | Release is low. Raise the Release slider, or pick a tone with a longer tail such as Bell or Pad. |
| The tab imported nothing | The status line names what it skipped. Most often the block has a different number of string lines than the tuning expects. |
| Two Key-J entries in Add/Remove Programs | Only if you installed 1.4.0. That build carried a different application identifier, which Windows uses to recognise an upgrade, so anything newer installs beside it rather than over it. Uninstall both, then install the current version once. Nothing installed from 1.4.1 onward does this. |
| The installer says it cannot continue | Key-J is running. Close it — including from the tray — and install again. It stops rather than replacing the files it can reach and leaving the ones Windows has open, which would give you half of each version. |

## What it can see

With Global Capture on, Key-J receives a signal each time any key is pressed
anywhere. It holds which key is currently down so it can release the note, and
discards it. Nothing is written to disk, nothing is sent anywhere, and the
switch starts off every time the app launches. The
[privacy page](https://f-keys.com/keyj/privacy/) says all of this in detail, including
how to check it rather than believe it.

## The key map

The left rail lists every key and the note it plays, and **clicking a row rebinds
it**. Scale and octave sit underneath: pick a scale and the whole keyboard is
constrained to it, which makes playing something that sounds wrong difficult.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
