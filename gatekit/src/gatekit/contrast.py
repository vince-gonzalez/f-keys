#!/usr/bin/env python3
"""
============================================================
contrast - nothing on a page may be unreadable
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

"Dark grey on navy" has been reported by the person who has to
read it more than once, which makes it a class of defect
rather than a mistake. typefloor.py already stops type being
too small; this stops it being the wrong colour, by the same
method: measure it, fail the build, and stop relying on
anybody noticing.

WHAT IT MEASURES

The WCAG 2.1 contrast ratio between every colour a stylesheet
declares and the surface it is drawn on. A ratio is a number
between 1 (invisible) and 21 (black on white).

  4.5   the floor for body text
  3.0   large text, 24px or 19px bold

THE RULE, AND WHY IT IS THIS ONE

Comparing every ink against every surface flags pairs that
never occur together - a green meant for a black readout is
not a defect because it would be illegible on chrome. So each
ink has to reach the floor on at least ONE declared surface.
An ink that fails against all of them has nowhere it can
legitimately be used, which is exactly the "dark grey on
navy" case this exists for.

WHAT IT CANNOT SEE

A colour applied by script at runtime, and a colour whose
surface is decided by a parent this cannot resolve. Pairings
are read from the custom properties a file declares, which is
how these stylesheets are written; anything set inline in JS
is out of reach and stays that way rather than being guessed
at.

  python tools/contrast.py                 report; exit 1 if any pair fails
  python tools/contrast.py --list          every pair, passing or not
  python tools/contrast.py --root remapwrap

Pairs that must stay below the floor go in tools/contrast.json
with a reason, the same as typefloor.
============================================================
"""

import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
def _config():
    if "--config" in sys.argv:
        i = sys.argv.index("--config")
        if i + 1 < len(sys.argv):
            return os.path.abspath(sys.argv[i + 1])
    return os.environ.get("CONTRAST_CONFIG") or os.path.join(HERE, "contrast.json")


CONFIG = _config()

#: Which variables name a surface something is drawn on. Everything else
#: that looks like a colour is treated as ink.
SURFACES = ("bg", "background", "panel", "surface", "paper", "card",
            "field", "sel", "face", "desktop", "title-b")

SKIP_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__",
             "vendor", ".venv", "fonts", "assets"}


def load_config():
    if not os.path.exists(CONFIG):
        return {"floor": 4.5, "exceptions": []}
    with open(CONFIG, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg.setdefault("floor", 4.5)
    cfg.setdefault("exceptions", [])
    return cfg


def to_rgb(value):
    v = value.strip().lower()
    m = re.match(r"^#([0-9a-f]{3,8})$", v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) < 6:
            return None
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"^rgba?\(([^)]+)\)$", v)
    if m:
        parts = [p.strip() for p in m.group(1).replace("/", ",").split(",")]
        try:
            return tuple(int(float(p)) for p in parts[:3])
        except ValueError:
            return None
    return None


def luminance(rgb):
    out = []
    for c in rgb:
        c = c / 255.0
        out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def variables(text):
    """Every --name: value the file declares."""
    out = {}
    for name, value in re.findall(r"--([\w-]+)\s*:\s*([^;}]+)[;}]", text):
        rgb = to_rgb(value)
        if rgb:
            out[name] = rgb
    return out


def walk(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if name.lower().endswith((".html", ".css")):
                yield os.path.join(base, name)


def check(root, cfg):
    floor = cfg["floor"]
    allowed = {(e.get("ink"), e.get("on")) for e in cfg["exceptions"]}
    rows = []

    for path in walk(root):
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        vars_ = variables(text)
        if not vars_:
            continue

        surfaces = {n: c for n, c in vars_.items()
                    if any(s in n for s in SURFACES)}
        inks = {n: c for n, c in vars_.items()
                if n not in surfaces and not n.startswith("glow")}
        if not surfaces or not inks:
            continue

        rel = os.path.relpath(path, root).replace("\\", "/")
        for ink_name, ink in sorted(inks.items()):
            # The best surface this ink has. An ink that reaches the floor
            # somewhere has a place it belongs; one that reaches it nowhere
            # cannot be read against anything the file declares.
            best_name, best = None, 0.0
            for surf_name, surf in sorted(surfaces.items()):
                r = ratio(ink, surf)
                if r > best:
                    best_name, best = surf_name, r
            declared = any((ink_name, s) in allowed for s in surfaces)
            rows.append({"file": rel, "ink": ink_name, "on": best_name,
                         "ratio": best,
                         "ok": best >= floor or declared,
                         "declared": declared})
    return rows


def main():
    args = sys.argv[1:]
    # Packaged, the directory above this file is site-packages,
    # not the project being checked. The working directory is
    # what someone running this in their repo means.
    root = os.environ.get("CONTRAST_ROOT") or os.getcwd()
    if "--root" in args:
        root = os.path.abspath(args[args.index("--root") + 1])
    else:
        # a bare path was silently ignored, which meant this scanned its
        # own repository and reported OK on a tree nobody asked about
        positional = [a for a in args if not a.startswith("-")]
        if positional:
            root = os.path.abspath(positional[0])

    cfg = load_config()
    rows = check(root, cfg)
    if not rows:
        # This reads CSS custom properties - `--ink: #hex` against
        # `--bg: #hex` - not literal `color:` declarations. A stylesheet
        # that uses neither has nothing here to compare, which is a true
        # statement and a dangerous one: in CI it exits 0 and reads as a
        # pass on a site nobody checked. --require-pairs is how you say
        # "I expect this to find something", and the Action sets it.
        print("  contrast: nothing with declared colours to check.")
        print("            This audits CSS custom properties (--name: #hex),")
        print("            not literal color/background declarations.")
        if "--require-pairs" in args:
            print("  contrast: FAILED - --require-pairs was set and no pair "
                  "was found.")
            return 1
        return 0

    if "--list" in args:
        for r in sorted(rows, key=lambda x: x["ratio"]):
            mark = "ok  " if r["ok"] else "FAIL"
            print("  {} {:>5.2f}  --{} at best on --{}   {}".format(
                mark, r["ratio"], r["ink"], r["on"], r["file"]))
        return 0

    bad = [r for r in rows if not r["ok"]]
    if not bad:
        print("  contrast: OK - every declared pair reaches {}:1"
              .format(cfg["floor"]))
        return 0

    print("  contrast: {} pair(s) below {}:1 and not declared\n"
          .format(len(bad), cfg["floor"]))
    for r in sorted(bad, key=lambda x: x["ratio"])[:40]:
        print("    {:>5.2f}  --{} has no surface it reads on (best is --{})   {}".format(
            r["ratio"], r["ink"], r["on"], r["file"]))
    print("\n  Either change the colours, or add the pair to tools/"
          "contrast.json with a reason.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
