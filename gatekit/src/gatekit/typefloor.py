#!/usr/bin/env python3
"""Fail when text is set below the minimum readable size.

    python tools/typefloor.py            # report; exit 1 if anything undeclared is too small
    python tools/typefloor.py --list     # every hit, declared or not, grouped by selector
    python tools/typefloor.py --fix      # raise undeclared violations to the floor

Small type is the single defect that has come back on this project more often than any other,
and it keeps coming back because it is invisible in a diff and nobody re-measures a page they
did not touch. So the rule is not "don't set small type" - it is "you cannot set small type by
accident." A size below the floor has to be written down in typefloor.json with a reason, and
anything not written down fails.

Three places it hides, all of them checked here, because grepping for `font-size: 10px` finds
only the first:

  1. plain declarations          font-size: 10px
  2. clamp() minimums            font-size: clamp(9px, 2vw, 18px)   <- renders at 9px on a phone
  3. canvas text                 cx.font = "10px monospace"          <- no CSS rule to grep

Not checked: computed sizes from em/rem/% chains. Those need a browser; tools/a11y-sweep.js
covers the rendered side.
"""
import json, os, re, sys
from pathlib import Path

def _root():
    """
    The tree to check. Defaults to the repository this file sits in, but takes
    --root so one copy can gate every property rather than one copy per
    property drifting apart - which is the fault this repository already
    learned the hard way with two copies of one renderer.
    """
    argv = sys.argv
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 < len(argv):
            return Path(argv[i + 1]).resolve()
    # A bare path used to be ignored, so `typefloor ./src` scanned this
    # repository instead and printed OK - a pass on a tree it never
    # looked at. It is the root now, which is what anyone typing it
    # meant.
    positional = [a for a in argv[1:] if not a.startswith("-")]
    if positional:
        return Path(positional[0]).resolve()
    env = os.environ.get("TYPEFLOOR_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd()


ROOT = _root()
# The packaged default. --config points at your own, and the F-Keys
# repo passes tools/typefloor.json so its exception list stays local.
def _config():
    argv = sys.argv
    if "--config" in argv:
        i = argv.index("--config")
        if i + 1 < len(argv):
            return Path(argv[i + 1]).resolve()
    env = os.environ.get("TYPEFLOOR_CONFIG")
    if env:
        return Path(env).resolve()
    return Path(__file__).parent / "typefloor.json"


CONFIG = _config()
SKIP_DIRS = {"node_modules", ".git", "dist", "__pycache__"}

# .js and .css are scanned, not only .html, because the widget and the feedback control build
# their own stylesheets in JavaScript. Those rules are invisible to an HTML scan and they ship
# to OTHER people's sites, which makes them the worst possible place to hide small type.
EXTS = ("*.html", "*.js", "*.css")

# Patterns return (declared_px, whole_match). Each corresponds to a hiding place above.
PATTERNS = [
    ("css",    re.compile(r"font-size\s*:\s*(\d+(?:\.\d+)?)px")),
    ("clamp",  re.compile(r"font-size\s*:\s*clamp\(\s*(\d+(?:\.\d+)?)px")),
    ("canvas", re.compile(r"""\.font\s*=\s*['"][^'"]*?(\d+(?:\.\d+)?)px""")),
    # `font: 600 11px/1.3 system-ui` sets a size without the string "font-size" appearing at
    # all, so it survives every grep anyone reaches for first.
    ("short",  re.compile(r"(?<!-)\bfont\s*:\s*(?:(?:normal|italic|oblique|small-caps|bold|bolder|lighter|\d{3})\s+)*(\d+(?:\.\d+)?)px")),
]


def load_config():
    if not CONFIG.exists():
        return {"floor_px": 13, "exceptions": []}
    return json.loads(CONFIG.read_text(encoding="utf-8"))


# A hit inside JavaScript has no CSS selector, but selector_for() will happily
# invent one, because the nearest preceding "{" is a JS block. A 12px textarea
# built in a string was reported as the selector `if (!w)`, which reads as a
# stylesheet rule, sends the reader looking for one that does not exist, and
# cost a wrong diagnosis. When the guess does not look like a selector, say so.
_JS_LIKE = re.compile(
    r"(?:^|[\s;{}])(?:if|for|while|function|return|var|let|const|else|switch|try|catch)\b"
    r"|[!<>=&|]=|=[=>]|\(\s*!")


def _looks_like_selector(sel):
    return bool(sel) and sel != "?" and not _JS_LIKE.search(sel)


def _inline_label(text, pos):
    """Name a hit that lives in a string rather than a stylesheet."""
    start = text.rfind("style=", max(0, pos - 300), pos)
    if start != -1:
        frag = text[start + 6:pos + 30].strip("\"' ")
        return "inline style: " + re.sub(r"\s+", " ", frag)[:56]
    line_start = text.rfind("\n", 0, pos) + 1
    frag = text[line_start:pos + 30].strip()
    return "in script: " + re.sub(r"\s+", " ", frag)[:56]


def selector_for(text, pos):
    """Best-effort CSS selector for a hit, so an exception can name something stable."""
    head = text[:pos]
    brace = head.rfind("{")
    if brace == -1:
        return _inline_label(text, pos)
    # Start after whichever delimiter ends the PREVIOUS rule. Each candidate contributes the
    # index just past itself, so a two-character delimiter like */ does not leave its slash
    # glued to the front of the selector.
    ends = [0]
    for delim in ("}", "*/", ">", ";"):
        i = head.rfind(delim, 0, brace)
        if i != -1:
            ends.append(i + len(delim))
    sel = head[max(ends):brace].strip().replace("\n", " ")
    sel = re.sub(r"\s+", " ", sel)[-90:]
    return sel if _looks_like_selector(sel) else _inline_label(text, pos)


def scan(floor, exceptions):
    exact = {e["selector"] for e in exceptions}
    hits = []
    paths = sorted({p for ext in EXTS for p in ROOT.rglob(ext)})
    for path in paths:
        if SKIP_DIRS & set(path.parts):
            continue
        if path.name in ("typefloor.py", "a11y-sweep.js"):   # the tools' own thresholds
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for kind, pat in PATTERNS:
            for m in pat.finditer(text):
                px = float(m.group(1))
                if px >= floor:
                    continue
                sel = selector_for(text, m.start()) if kind != "canvas" else "canvas:" + m.group(0)[:40]
                hits.append({
                    "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "line": text.count("\n", 0, m.start()) + 1,
                    "px": px, "kind": kind, "selector": sel,
                    "match": m.group(0),
                    "declared": sel in exact,
                })
    return hits


def _help():
    print("""typefloor - Fail a build when type is declared below a readable floor.

usage:
  typefloor [PATH] [--floor N] [--config FILE] [--list] [--fix]

  PATH        directory to check (default: the working directory)
  --floor N   minimum size in px (default: 13, or floor_px in the config)
  --config    JSON file of recorded exceptions
  --list      every offender rather than the summary
  --fix       raise undeclared sizes to the floor
  --root DIR  same as PATH, kept for existing callers

Exits 0 when clean, 1 on a finding. Part of readable-gates.
https://f-keys.com/gatekit/""")
    return 0


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        return _help()
    cfg = load_config()
    # --floor overrides the config, so the Action can advertise it as an
    # input without that input being decoration.
    floor = cfg.get("floor_px", 13)
    if "--floor" in sys.argv:
        i = sys.argv.index("--floor")
        if i + 1 < len(sys.argv):
            try:
                floor = int(sys.argv[i + 1])
            except ValueError:
                print("typefloor: --floor needs a number, got %r"
                      % sys.argv[i + 1])
                return 1
    hits = scan(floor, cfg.get("exceptions", []))
    undeclared = [h for h in hits if not h["declared"]]

    if "--list" in sys.argv:
        by_sel = {}
        for h in hits:
            by_sel.setdefault((h["selector"], h["px"], h["declared"]), []).append(h["file"])
        for (sel, px, dec), files in sorted(by_sel.items(), key=lambda kv: (kv[0][2], kv[0][1])):
            flag = "declared" if dec else "TOO SMALL"
            print("%-9s %5.1fpx  %-52s  %d file(s)" % (flag, px, sel[:52], len(set(files))))
        print("\nfloor %dpx | %d hit(s), %d undeclared" % (floor, len(hits), len(undeclared)))
        return 0

    if "--fix" in sys.argv and undeclared:
        edits = {}
        for h in undeclared:
            if h["kind"] == "canvas":       # never rewrite canvas strings blind
                continue
            edits.setdefault(h["file"], []).append(h)
        for f, hs in edits.items():
            p = ROOT / f
            t = p.read_text(encoding="utf-8")
            for h in hs:
                fixed = h["match"].replace("%gpx" % h["px"] if h["px"] % 1 else "%dpx" % h["px"],
                                           "%dpx" % floor, 1)
                if fixed != h["match"]:
                    t = t.replace(h["match"], fixed)
            p.write_text(t, encoding="utf-8")
        print("raised %d declaration(s) in %d file(s) to %dpx" % (
            sum(len(v) for v in edits.values()), len(edits), floor))
        print("canvas hits are never auto-fixed - fix those by hand")
        hits = scan(floor, cfg.get("exceptions", []))
        undeclared = [h for h in hits if not h["declared"]]

    if not undeclared:
        print("typefloor: OK - %d declaration(s) below %dpx, all declared in typefloor.json"
              % (len(hits), floor))
        return 0

    print("typefloor: %d declaration(s) below the %dpx floor and not declared\n" % (len(undeclared), floor))
    for h in sorted(undeclared, key=lambda h: (h["px"], h["file"]))[:60]:
        print("  %s:%d  %.0fpx  %s  [%s]" % (h["file"], h["line"], h["px"], h["selector"][:46], h["kind"]))
    if len(undeclared) > 60:
        print("  ... and %d more (use --list)" % (len(undeclared) - 60))
    print("\nEither raise them (--fix) or add the selector to tools/typefloor.json with a reason.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
