#!/usr/bin/env python3
"""
============================================================
readme — the house README standard
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Every repository should introduce itself the same way. The
gonzalgo README already had the right shape - a boxed block
banner, a one-line statement of what the thing answers, badges,
then prose - and that shape is now a tool rather than something
copied by hand and slowly drifting.

  banner(name, tagline)  -> the boxed ASCII header
  signature()            -> the standard footer
  skeleton(...)          -> a whole README

The font is ANSI Shadow, the same one the gonzalgo banner uses.
It is verified against that banner rather than trusted: run
this file directly and it regenerates GONZALGO and reports
whether it matches the published original character for
character.

Run:  python tools/readme.py --verify
      python tools/readme.py --banner MOONBEAM "one line"
============================================================
"""

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# ── ANSI Shadow, six rows per glyph ──────────────────────────
F = {
"A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
"B": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██████╔╝", "╚═════╝ "],
"C": [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"],
"D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
"E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
"F": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "██║     ", "╚═╝     "],
"G": [" ██████╗ ", "██╔════╝ ", "██║  ███╗", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
"H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
"I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
"J": ["     ██╗", "     ██║", "     ██║", "██   ██║", "╚█████╔╝", " ╚════╝ "],
"K": ["██╗  ██╗", "██║ ██╔╝", "█████╔╝ ", "██╔═██╗ ", "██║  ██╗", "╚═╝  ╚═╝"],
"L": ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"],
"M": ["███╗   ███╗", "████╗ ████║", "██╔████╔██║", "██║╚██╔╝██║", "██║ ╚═╝ ██║", "╚═╝     ╚═╝"],
"N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
"O": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
"P": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔═══╝ ", "██║     ", "╚═╝     "],
"Q": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║▄▄ ██║", "╚██████╔╝", " ╚══▀▀═╝ "],
"R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
"S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
"T": ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
"U": ["██╗   ██╗", "██║   ██║", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
"V": ["██╗   ██╗", "██║   ██║", "██║   ██║", "╚██╗ ██╔╝", " ╚████╔╝ ", "  ╚═══╝  "],
"W": ["██╗    ██╗", "██║    ██║", "██║ █╗ ██║", "██║███╗██║", "╚███╔███╔╝", " ╚══╝╚══╝ "],
"X": ["██╗  ██╗", "╚██╗██╔╝", " ╚███╔╝ ", " ██╔██╗ ", "██╔╝ ██╗", "╚═╝  ╚═╝"],
"Y": ["██╗   ██╗", "╚██╗ ██╔╝", " ╚████╔╝ ", "  ╚██╔╝  ", "   ██║   ", "   ╚═╝   "],
"Z": ["███████╗", "╚══███╔╝", "  ███╔╝ ", " ███╔╝  ", "███████╗", "╚══════╝"],
"0": [" ██████╗ ", "██╔═████╗", "██║██╔██║", "████╔╝██║", "╚██████╔╝", " ╚═════╝ "],
"1": [" ██╗", "███║", "╚██║", " ██║", " ██║", " ╚═╝"],
"2": ["██████╗ ", "╚════██╗", " █████╔╝", "██╔═══╝ ", "███████╗", "╚══════╝"],
"3": ["██████╗ ", "╚════██╗", " █████╔╝", " ╚═══██╗", "██████╔╝", "╚═════╝ "],
"4": ["██╗  ██╗", "██║  ██║", "███████║", "╚════██║", "     ██║", "     ╚═╝"],
"5": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
"6": [" ██████╗ ", "██╔════╝ ", "███████╗ ", "██╔═══██╗", "╚██████╔╝", " ╚═════╝ "],
"7": ["███████╗", "╚══██╔═╝", "   ██║  ", "   ██║  ", "   ██║  ", "   ╚═╝  "],
"8": [" █████╗ ", "██╔══██╗", "╚█████╔╝", "██╔══██╗", "╚█████╔╝", " ╚════╝ "],
"9": [" █████╗ ", "██╔══██╗", "╚██████║", " ╚═══██║", " █████╔╝", " ╚════╝ "],
"-": ["      ", "      ", "█████╗", "╚════╝", "      ", "      "],
" ": ["    ", "    ", "    ", "    ", "    ", "    "],
}

WIDTH = 76          # inside the box, matching the gonzalgo banner


def letters(text):
    """Six rows of block letters. Unknown characters become a space."""
    rows = [""] * 6
    for ch in text.upper():
        g = F.get(ch, F[" "])
        for i in range(6):
            rows[i] += g[i]
    return rows


def banner(name, tagline="", width=WIDTH):
    """The boxed header. Returns a fenced block ready to paste into a README."""
    body = letters(name)
    span = max(len(r) for r in body)
    if span > width - 4:
        width = span + 4

    def line(s=""):
        pad = width - len(s)
        left = pad // 2
        return "║" + " " * left + s + " " * (pad - left) + "║"

    out = ["```", "╔" + "═" * width + "╗", line()]
    out += [line(r + " " * (span - len(r))) for r in body]
    out.append(line())
    if tagline:
        out.append(line(tagline))
        out.append(line())
    out.append("╚" + "═" * width + "╝")
    out.append("```")
    return "\n".join(out)


def spaced(word):
    """Letterspaced small caps. The house wordmark under the block letters."""
    return "·   " + "  ".join(word.upper()) + "   ·"


def signature(width=60):
    """
    The mark at the foot of every repository: F-KEYS in the same block font
    the banners use, the company name spaced out beneath it, then who made it.
    A reader landing on one repository can tell whose shelf it came off.
    """
    body = letters("F-KEYS")
    span = max(len(r) for r in body)
    if span > width - 6:
        width = span + 6

    def line(t=""):
        pad = width - len(t)
        left = pad // 2
        return "║" + " " * left + t + " " * (pad - left) + "║"

    out = ["---", "", "```"]
    out.append("╔" + "═" * width + "╗")
    out.append(line())
    out += [line(r + " " * (span - len(r))) for r in body]
    out.append(line())
    out.append(line(spaced("Creative")))
    out.append(line())
    out.append(line("─" * (width - 20)))
    out.append(line())
    out.append(line("Vincent Gonzalez"))
    out.append(line("f-keys.com"))
    out.append(line("ORCID 0009-0005-3640-014X"))
    out.append(line())
    out.append("╚" + "═" * width + "╝")
    out.append("```")
    out += ["",
            "Part of [F-Keys](https://f-keys.com) — independent hardware, "
            "software",
            "and internet products. See the [working log](https://f-keys.com/log/)",
            "and [live status](https://f-keys.com/status/)."]
    return "\n".join(out)


def skeleton(name, tagline, body, badges=None):
    parts = [banner(name, tagline), ""]
    if badges:
        parts += ["".join(badges), ""]
    parts += [body.strip(), "", signature(), ""]
    return "\n".join(parts)


# ── the font is checked, not trusted ─────────────────────────
PUBLISHED_GONZALGO = [
    " ██████╗  ██████╗ ███╗   ██╗███████╗ █████╗ ██╗      ██████╗  ██████╗ ",
    "██╔════╝ ██╔═══██╗████╗  ██║╚══███╔╝██╔══██╗██║     ██╔════╝ ██╔═══██╗",
    "██║  ███╗██║   ██║██╔██╗ ██║  ███╔╝ ███████║██║     ██║  ███╗██║   ██║",
    "██║   ██║██║   ██║██║╚██╗██║ ███╔╝  ██╔══██║██║     ██║   ██║██║   ██║",
    "╚██████╔╝╚██████╔╝██║ ╚████║███████╗██║  ██║███████╗╚██████╔╝╚██████╔╝",
    " ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ",
]


def verify():
    mine = letters("GONZALGO")
    ok = True
    for i, (a, b) in enumerate(zip(mine, PUBLISHED_GONZALGO)):
        if a.rstrip() != b.rstrip():
            ok = False
            print("  row {} differs".format(i + 1))
            print("    published: {!r}".format(b))
            print("    generated: {!r}".format(a))
    print("  font matches the published gonzalgo banner" if ok
          else "  FONT MISMATCH - fix the glyphs before using this")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--verify" in sys.argv:
        sys.exit(verify())
    if "--banner" in sys.argv:
        i = sys.argv.index("--banner")
        nm = sys.argv[i + 1]
        tl = sys.argv[i + 2] if len(sys.argv) > i + 2 else ""
        print(banner(nm, tl))
        sys.exit(0)
    print(__doc__)
