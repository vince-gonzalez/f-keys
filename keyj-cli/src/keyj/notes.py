"""
============================================================
keyj.notes — pitch, and the names people write it with
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The browser app and this package have to agree on what "E5"
means, or a sequence saved in one will not play in the other.
Every conversion here is the same arithmetic as the JavaScript
in keyj/app.html, and tests/test_parity.py checks the two
against each other at every pitch Key-J can produce.

Nothing here has dependencies. A sequence is a list of notes,
a note is a name and a frequency, and that is the whole model.
============================================================
"""

import re

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_BASE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
_NAME = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")

#: A4 = 440 Hz, twelve equal steps to the octave.
A4_HZ = 440.0
A4_MIDI = 69


def midi_to_name(midi):
    """60 -> 'C4'. Sharps, never flats, matching the browser app."""
    return NAMES[midi % 12] + str(midi // 12 - 1)


def midi_to_freq(midi):
    """60 -> 261.6255653... Hz."""
    return A4_HZ * (2.0 ** ((midi - A4_MIDI) / 12.0))


def name_to_midi(name):
    """
    'C4' -> 60, 'Bb3' -> 58, 'F#5' -> 78.

    Returns None rather than raising or guessing. A name this cannot read
    is reported to the caller, which reports it to the user; the one thing
    it must never do is quietly become some other note.
    """
    m = _NAME.match(str(name).strip())
    if not m:
        return None
    step = _BASE[m.group(1).lower()]
    if m.group(2) == "#":
        step += 1
    elif m.group(2) == "b":
        step -= 1
    return step + (int(m.group(3)) + 1) * 12


def name_to_freq(name):
    midi = name_to_midi(name)
    return None if midi is None else midi_to_freq(midi)


class Note(object):
    """A pitch with the name it was written as."""

    __slots__ = ("name", "freq")

    def __init__(self, name, freq):
        self.name = name
        self.freq = freq

    @classmethod
    def from_midi(cls, midi):
        return cls(midi_to_name(midi), midi_to_freq(midi))

    @classmethod
    def from_name(cls, name):
        f = name_to_freq(name)
        return None if f is None else cls(str(name).strip().upper(), f)

    def __repr__(self):
        return "Note({!r}, {:.3f})".format(self.name, self.freq)

    def __eq__(self, other):
        return (isinstance(other, Note)
                and other.name == self.name
                and abs(other.freq - self.freq) < 1e-9)
