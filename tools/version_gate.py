#!/usr/bin/env python3
"""Every place a package writes its version must agree. Run before any upload.

Seven wheels went to PyPI reporting a version different from the one on the tin,
because `pyproject.toml` was bumped and `__init__.py` was not. The filename and
the METADATA both derive from pyproject, so they agree with each other and the
mismatch is invisible from outside the wheel. This is the check that sees it.

    python version-gate.py            report
    python version-gate.py --sync X   write version X to every site in one tree
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Where each package tree lives.
#
# This file used to live in the temp directory, which gets cleaned. It is
# the thing that stops a wheel disagreeing with its own metadata, and it
# was one sweep away from disappearing - the same mistake as leaving a
# signing key there. It is version controlled now.
TREES = {
    "gonzalgo":       r"C:\tmp\gonzalgo-work",
    "authorecon":     r"C:\tmp\authorecon",
    "mmforge":        r"C:\tmp\setmm-choice",
    "certivl":        r"C:\tmp\certivl",
    "ishihara":       r"C:\tmp\ishihara",
    "opticquiz-cvd":  r"C:\tmp\opticquiz.com\packages\cvd-py",
    "keyj":           r"C:\tmp\f-keys\keyj-cli",
    "plumhud":        r"C:\tmp\f-keys\plumhud",
    "moonbeam-miner": r"C:\tmp\f-keys\moonbeam",
    "remapwrap":      r"C:\tmp\f-keys\remapwrap-cli",
}

PYPROJECT = re.compile(r'(?m)^(version\s*=\s*")([^"]+)(")')
DUNDER = re.compile(r'(?m)^(__version__\s*=\s*")([^"]+)(")')
JSONVER = re.compile(r'("version"\s*:\s*")([^"]+)(")')


def sites(root: Path) -> list[tuple[Path, re.Pattern, str]]:
    out = []
    p = root / "pyproject.toml"
    if p.exists():
        m = PYPROJECT.search(p.read_text(encoding="utf-8", errors="replace"))
        if m:
            out.append((p, PYPROJECT, m.group(2)))
    for f in ("server.json", "package.json"):
        j = root / f
        if j.exists():
            m = JSONVER.search(j.read_text(encoding="utf-8", errors="replace"))
            if m:
                out.append((j, JSONVER, m.group(2)))
    for init in sorted(root.glob("src/*/__init__.py")) + sorted(root.glob("*/__init__.py")):
        m = DUNDER.search(init.read_text(encoding="utf-8", errors="replace"))
        if m:
            out.append((init, DUNDER, m.group(2)))
    return out


def sync(root: Path, target: str) -> list[str]:
    touched = []
    for f, pat, cur in sites(root):
        if cur == target:
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        t = pat.sub(lambda m: m.group(1) + target + m.group(3), t, count=1)
        f.write_text(t, encoding="utf-8", newline="\n")
        touched.append(f"{f.name} {cur}->{target}")
    return touched


def main() -> int:
    if "--sync" in sys.argv:
        i = sys.argv.index("--sync")
        target, tree = sys.argv[i + 1], sys.argv[i + 2]
        for line in sync(Path(tree), target) or ["already consistent"]:
            print("   " + line)
        return 0

    bad = 0
    for name, d in TREES.items():
        root = Path(d)
        if not root.exists():
            print(f"   {name:16} TREE MISSING")
            continue
        s = sites(root)
        vals = {v for _, _, v in s}
        ok = len(vals) <= 1
        bad += 0 if ok else 1
        print("   %-16s %-9s %s   %s" % (
            name, sorted(vals)[0] if len(vals) == 1 else "SPLIT",
            "ok " if ok else "BAD",
            ", ".join(f"{f.name}={v}" for f, _, v in s)))
    print()
    print("   consistent" if not bad else f"   {bad} package(s) disagree with themselves")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
