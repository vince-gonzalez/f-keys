#!/usr/bin/env python3
"""
============================================================
check_palette - a palette that survives colour blindness
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
opticquiz-cvd is a library with no command line, so there was
no way to put it in a build. Roughly one man in twelve has some
form of red-green colour blindness, and the default matplotlib
pair - #d62728 and #2ca02c - collapses to the same colour for
them. Nobody finds that in review, because the reviewer can
see it.

This reads the colours out of a file, or takes them directly,
and fails the build when two of them become the same colour
under protanopia, deuteranopia or tritanopia.

WHAT IT READS
  --colors "#1f77b4,#ff7f0e"   an explicit list
  --file palette.json          a JSON array, or an object of
                               name -> hex
  --file theme.css             every #rrggbb in the file

Exits 0 when the palette survives, 1 on a collapse, 2 when it
was handed nothing to check - because a pass on an empty list
is not a pass.
============================================================
"""

import argparse
import json
import os
import re
import sys

HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def from_file(path):
    """A palette out of JSON, or every hex colour out of anything else."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    if path.lower().endswith(".json"):
        try:
            data = json.loads(text)
        except ValueError as e:
            print("check_palette: %s is not valid JSON: %s" % (path, e))
            return None
        if isinstance(data, dict):
            return [v for v in data.values() if isinstance(v, str)
                    and HEX.fullmatch(v.strip())]
        if isinstance(data, list):
            return [v for v in data if isinstance(v, str)
                    and HEX.fullmatch(v.strip())]
        print("check_palette: %s is JSON but not a list or an object" % path)
        return None

    # anything else - CSS, SCSS, a config - is scanned for hex colours
    seen, out = set(), []
    for c in HEX.findall(text):
        low = c.lower()
        if low not in seen:
            seen.add(low)
            out.append(c)
    return out


def main():
    p = argparse.ArgumentParser(
        prog="check_palette",
        description="Fail a build when a palette collapses under colour "
                    "blindness.")
    p.add_argument("--colors", default="",
                   help="Comma-separated hex colours.")
    p.add_argument("--file", default="",
                   help="A .json palette, or any file to scan for hex.")
    p.add_argument("--severity", type=float, default=1.0,
                   help="0..1, how complete the simulated deficiency is.")
    p.add_argument("--distinct", type=int, default=13,
                   help="Minimum perceptual distance between two colours.")
    p.add_argument("--types", default="protan,deutan,tritan",
                   help="Which deficiencies to check.")
    args = p.parse_args()

    try:
        import opticquiz_cvd as cvd
    except ImportError:
        print("check_palette: opticquiz-cvd is not installed")
        return 2

    colors = []
    if args.colors:
        colors = [c.strip() for c in args.colors.split(",") if c.strip()]
    elif args.file:
        if not os.path.exists(args.file):
            print("check_palette: no such file: %s" % args.file)
            return 2
        colors = from_file(args.file)
        if colors is None:
            return 2

    bad = [c for c in colors if not HEX.fullmatch(c)]
    if bad:
        print("check_palette: not six-digit hex colours: %s"
              % ", ".join(bad[:5]))
        return 2

    if len(colors) < 2:
        # One colour cannot conflict with anything, and zero is a config
        # mistake. Reporting either as a pass would be a green tick on a
        # palette nobody looked at.
        print("check_palette: found %d colour(s); need at least two to "
              "compare." % len(colors))
        if args.file:
            print("               Checked: %s" % args.file)
        return 2

    wanted = [t.strip() for t in args.types.split(",") if t.strip()]
    result = cvd.check_palette(colors, distinct=args.distinct,
                               severity=args.severity)

    print("check_palette: %d colours, %s"
          % (len(colors), ", ".join(wanted)))

    failures = 0
    for kind in wanted:
        block = (result.get("types") or {}).get(kind)
        if block is None:
            print("  %-8s not a deficiency this engine models" % kind)
            continue
        if block.get("pass"):
            print("  %-8s ok" % kind)
            continue
        failures += 1
        print("  %-8s FAILS" % kind)
        for c in block.get("conflicts", []):
            print("      %s and %s read as %.1f apart under %s "
                  "(%.1f to normal vision) - %s"
                  % (c["a"], c["b"], c["sim"], kind, c["normal"],
                     c.get("severity", "")))

    if failures:
        print()
        print("  %d of %d deficiencies cannot tell these colours apart."
              % (failures, len(wanted)))
        print("  opticquiz_cvd.fix_palette() will nudge them apart while "
              "staying near the originals.")
        return 1

    print("  the palette survives every deficiency checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
