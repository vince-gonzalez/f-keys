"""
============================================================
keyj.sequence — the text format, both directions
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
A sequence saved from the browser app must load here, and a
sequence written here must paste back into the browser's note
box. That means one format, and it is deliberately the dullest
one available: note names separated by whitespace, with #
comment lines that are stripped on the way in.

  # Key-J sequence - 8 notes from tab
  E5 G5 B5 E6 D5 A4 C5 G4

The header is a courtesy, not structure. A file containing
nothing but note names is equally valid, which means anything
that can produce a list of note names can feed Key-J.
============================================================
"""

from .notes import Note

#: Names per line when writing. Wide enough to read, narrow enough to paste.
PER_LINE = 16


class Read(object):
    """What a parse produced, including what it could not."""

    def __init__(self, notes, skipped):
        self.notes = notes
        self.skipped = skipped

    def __repr__(self):
        return "Read({} notes, {} skipped)".format(len(self.notes), len(self.skipped))


def strip_comments(text):
    """Drop # lines so a saved file pastes as-is into the browser's note box."""
    keep = [ln for ln in str(text).splitlines() if not ln.strip().startswith("#")]
    return " ".join(keep)


def parse(text):
    """
    Read note names out of text. Separators are whitespace, commas or bars,
    so tab output and hand-typed lists both work.

    Anything unreadable lands in .skipped and is reported. It is never
    dropped silently and never guessed at - a wrong note you cannot see is
    worse than a missing one you can.
    """
    notes, skipped = [], []
    for token in _tokens(strip_comments(text)):
        note = Note.from_name(token)
        if note is None:
            skipped.append(token)
        else:
            notes.append(note)
    return Read(notes, skipped)


def _tokens(text):
    out, cur = [], []
    for ch in text:
        if ch.isspace() or ch in ",|":
            if cur:
                out.append("".join(cur))
                cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


def format(notes, source=""):
    """Write the format parse() reads. Round-trips exactly."""
    head = "# Key-J sequence - {} notes{}".format(
        len(notes), " from " + source if source else "")
    lines = [head,
             '# Paste this whole file into "Or type note names", or use Load .txt']
    for i in range(0, len(notes), PER_LINE):
        lines.append(" ".join(n.name for n in notes[i:i + PER_LINE]))
    return "\n".join(lines) + "\n"


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read())


def save(path, notes, source=""):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(format(notes, source))
