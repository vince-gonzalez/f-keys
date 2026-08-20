"""
============================================================
test_play — the live player, including the claim it makes
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

`keyj play` installs a system-wide keyboard listener. The
README, the licence, the privacy page and the product page all
make the same claim about it:

    it never learns which key you pressed.

That claim was written in four places and tested in none, which
made it a promise rather than a property. It is a property: the
function a key press calls takes no key. This file asserts that,
so the day somebody adds a `key` argument to advance() in order
to do something reasonable, the build stops and says why.

The rest is the sequence machinery - order, looping, the voice
cap, mixing - none of which needs audio hardware or a hook, so
all of it runs anywhere including CI.

Run:  python tests/test_play.py
============================================================
"""

import inspect
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from keyj import play                                  # noqa: E402
from keyj.notes import Note                            # noqa: E402

FAILED = []


def check(label, got, want):
    ok = got == want
    print("  %-58s %s" % (label, "ok" if ok else "FAIL"))
    if not ok:
        print("      got  %r" % (got,))
        print("      want %r" % (want,))
        FAILED.append(label)


def scale(n=6):
    return [Note.from_name(x) for x in ["C4", "D4", "E4", "F4", "G4", "A4"][:n]]


# ── the claim ────────────────────────────────────────────────

def test_the_privacy_property():
    """
    A key press calls Player.advance(). If advance cannot receive a key, the
    process cannot retain one, and 'never learns which key you pressed' stops
    being something anyone has to take on faith.
    """
    sig = inspect.signature(play.Player.advance)
    check("advance() takes no argument but self",
          [p for p in sig.parameters if p != "self"], [])

    # and nothing on the player is shaped like a place to keep keys
    p = play.Player(scale(), loop=True)
    suspicious = [a for a in vars(p)
                  if any(w in a.lower() for w in ("key", "char", "press", "log",
                                                  "history", "buffer", "typed"))]
    check("no attribute on Player could hold key identity", suspicious, [])

    # the handler asks exactly one question of the key, and it is not "which"
    source = inspect.getsource(play.run)
    body = source[source.index("def _on_press"):source.index("def _on_release")]
    # Strip trailing comments first. A comment mentioning a key is prose; only
    # code that touches the variable counts, and conflating the two made this
    # check fail on a line reading `if held["down"]:` because its comment
    # happened to say "while a key is held".
    uses = []
    for line in body.splitlines():
        code = line.split("#", 1)[0].strip()
        if code and "key" in code:
            uses.append(code)
    check("_on_press touches `key` only to test membership",
          uses, ["def _on_press(key):", "if key in MODIFIERS:"])


# ── the sequence machinery ───────────────────────────────────

def test_walks_in_order():
    p = play.Player(scale(), loop=False)
    check("advance walks the sequence in order",
          [p.advance().name for _ in range(6)],
          ["C4", "D4", "E4", "F4", "G4", "A4"])


def test_loop_wraps():
    p = play.Player(scale(3), loop=True)
    check("a looping sequence wraps to the start",
          [p.advance().name for _ in range(7)],
          ["C4", "D4", "E4", "C4", "D4", "E4", "C4"])


def test_no_loop_finishes():
    p = play.Player(scale(3), loop=False)
    for _ in range(3):
        p.advance()
    after = p.advance()
    check("a non-looping sequence returns None past the end", after, None)
    check("and reports itself finished", p.finished.is_set(), True)


def test_voice_cap():
    p = play.Player(scale(), loop=True)
    for _ in range(play.VOICES * 3):
        p.advance()
    check("live voices are capped at VOICES",
          len(p.voices) <= play.VOICES, True)


def test_mix_shape():
    p = play.Player(scale(2), loop=False)
    check("mixing silence returns the frames asked for",
          len(p.mix(128)), 128)
    p.advance()
    block = p.mix(128)
    check("mixing a live voice returns the frames asked for", len(block), 128)
    check("and that block is not silent", any(abs(s) > 0 for s in block), True)


def test_voices_retire():
    p = play.Player([Note.from_name("C4")], hold=0.01, loop=False)
    p.advance()
    for _ in range(200):                     # far past the length of one note
        p.mix(512)
    check("a finished voice is dropped rather than mixed forever",
          p.voices, [])


def test_missing_dependency_says_what_to_install():
    check("Missing is an exception the CLI can catch",
          issubclass(play.Missing, Exception), True)


def main():
    print("test_play")
    for fn in (test_the_privacy_property, test_walks_in_order, test_loop_wraps,
               test_no_loop_finishes, test_voice_cap, test_mix_shape,
               test_voices_retire, test_missing_dependency_says_what_to_install):
        fn()
    print()
    if FAILED:
        print("  %d check(s) failed" % len(FAILED))
        return 1
    print("  all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
