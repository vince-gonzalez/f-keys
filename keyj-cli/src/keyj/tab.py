"""
============================================================
keyj.tab — guitar tablature to notes
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Tablature says which fret on which string. A fret is an offset
in semitones from that string's open pitch, so the conversion
is addition - once you know the tuning, and knowing the tuning
is the part a machine cannot infer.

So this never guesses one. It is told, it says which one it
used, and a block whose line count does not match that tuning
produces no notes and is named in the report. The reason is
that a wrong note you cannot see is worse than a missing one
you can: mistakes in a converted tab are inaudible until you
play them.

This is a port of the reader in keyj/app.html and must stay
identical to it. tests/test_parity.py holds them together.
============================================================
"""

from .notes import Note

#: Open-string MIDI numbers, highest string first, matching the browser app.
TUNINGS = {
    "Standard (EADGBe)": [64, 59, 55, 50, 45, 40],
    "Drop D":            [64, 59, 55, 50, 45, 38],
    "Eb Standard":       [63, 58, 54, 49, 44, 39],
    "D Standard":        [62, 57, 53, 48, 43, 38],
    "DADGAD":            [62, 57, 55, 50, 45, 38],
    "Open G":            [62, 59, 55, 50, 43, 38],
    "7-string (B)":      [64, 59, 55, 50, 45, 40, 35],
    "Bass (4)":          [43, 38, 33, 28],
}

#: Short names for the command line. "standard" beats "Standard (EADGBe)".
ALIASES = {
    "standard": "Standard (EADGBe)",
    "dropd": "Drop D",
    "drop-d": "Drop D",
    "eb": "Eb Standard",
    "d": "D Standard",
    "dadgad": "DADGAD",
    "openg": "Open G",
    "open-g": "Open G",
    "7string": "7-string (B)",
    "7-string": "7-string (B)",
    "bass": "Bass (4)",
}

MAX_CHARS = 200000          # a tab this long is not a tab
MAX_FRET = 24


def resolve_tuning(name):
    """Accept either the full name or a short alias. Returns None if unknown."""
    if name in TUNINGS:
        return name
    return ALIASES.get(str(name).strip().lower().replace(" ", ""))


class Report(object):
    """
    The result, and an account of itself.

    Every field here exists so the caller can tell the user what happened.
    A converter you cannot audit is worse than no converter.
    """

    def __init__(self, tuning, capo):
        self.notes = []
        self.strings = 0
        self.blocks = 0
        self.skipped = []
        self.tuning = tuning
        self.capo = capo
        self.error = None

    def __repr__(self):
        return "Report({} notes, {} blocks, {} skipped)".format(
            len(self.notes), self.blocks, len(self.skipped))


def _strip_label(line):
    """
    Remove a leading string label such as "e|" or "Bb|", replacing it with
    spaces so the remaining fret columns keep their positions. Column index
    is how notes played together are kept together, so it must survive.
    """
    i = 0
    n = len(line)
    while i < n and line[i].isspace():
        i += 1
    j = i
    while j < n and j - i < 2 and (line[j].isalpha() or line[j] in "#b"):
        j += 1
    k = j
    while k < n and line[k].isspace():
        k += 1
    if k < n and line[k] == "|":
        return " " * (k + 1) + line[k + 1:]
    return line


def looks_like_tab(line):
    body = _strip_label(line)
    return body.count("-") >= 4 and ("-" in body or "|" in body)


def read_frets(line):
    """
    Fret numbers with the column they sit in.

    Technique characters - h p / \\ b r ~ x - separate frets rather than
    joining them. They change how a note is played, not which note it is,
    and sequence mode supplies the rhythm anyway.
    """
    body = _strip_label(line)
    out = []
    i = 0
    while i < len(body):
        if body[i].isdigit():
            start = i
            digits = ""
            while i < len(body) and body[i].isdigit() and len(digits) < 2:
                digits += body[i]
                i += 1
            fret = int(digits)
            if fret <= MAX_FRET:
                out.append((start, fret))
        else:
            i += 1
    return out


def parse(text, tuning="Standard (EADGBe)", capo=0):
    """Convert tablature to notes under a stated tuning."""
    resolved = resolve_tuning(tuning)
    report = Report(resolved or tuning, capo)

    if not text or not text.strip():
        report.error = "Nothing to read."
        return report
    if len(text) > MAX_CHARS:
        report.error = "That is too long to be tablature."
        return report
    if resolved is None:
        report.error = "Unknown tuning: {}. Known: {}".format(
            tuning, ", ".join(sorted(ALIASES)))
        return report

    open_strings = TUNINGS[resolved]
    lines = text.replace("\r", "").split("\n")
    events = []
    i = 0
    while i < len(lines):
        if not looks_like_tab(lines[i]):
            i += 1
            continue
        block = []
        while i < len(lines) and looks_like_tab(lines[i]):
            block.append(lines[i])
            i += 1

        # A block should be one full set of strings. Anything else is
        # reported rather than guessed at.
        if len(block) != len(open_strings):
            report.skipped.append(
                "{} line(s) - expected {} strings for {}".format(
                    len(block), len(open_strings), resolved))
            continue

        report.blocks += 1
        report.strings = len(open_strings)
        # Later blocks must sort after earlier ones even though their column
        # numbers start over.
        offset = 0 if report.blocks == 1 else (100000 * report.blocks if events else 0)
        for si, line in enumerate(block):
            for col, fret in read_frets(line):
                events.append((col + offset, si, open_strings[si] + fret + capo))

    if not report.blocks:
        report.error = ("No tablature found. Expect {} lines of dashes and "
                        "fret numbers.".format(len(open_strings)))
        return report

    # Column order first, then low string to high so a chord rolls upward.
    events.sort(key=lambda e: (e[0], -e[1]))
    report.notes = [Note.from_midi(midi) for _, _, midi in events]
    return report
