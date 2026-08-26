#!/usr/bin/env python3
"""
============================================================
deadname-gate v1.0.0
Fails a build when a retired name reaches anything a human
reads, while leaving the machine identifiers that cannot
change.
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

Every company that renames itself has the same problem, and
grep does not solve it. The old name survives in two very
different places:

  human-visible   titles, footers, bylines, prose, alt text.
                  These must change, and they are the ones
                  that get copied forward into new work.
  machine         organisation accounts, repository paths,
                  live URLs, published artifact names, a DOI
                  on a deposited record. Renaming these breaks
                  working links or contradicts a permanent
                  record, so they must NOT change.

Grepping the old name finds both and reports hundreds of hits,
most of which are correct. So people stop running it.

THE TRICK, WHICH IS THE WHOLE TOOL

Delete every allowed identifier from the line first. If a
forbidden word survives that deletion, what is left is
branding a person reads. The allow list is patterns with
reasons attached, so an exception has to be justified once
rather than argued every time.

  python tools/deadname_gate.py
  python tools/deadname_gate.py --root ../other-repo
  python tools/deadname_gate.py --init     write a starter config
  python tools/deadname_gate.py --list-allowed

Generalised from the gate written for one dissolved company.
Configuration lives in deadname_gate.json beside this file, so
the same code serves any rename.
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
    return os.environ.get("DEADNAME_CONFIG") or os.path.join(HERE, "deadname_gate.json")


CONFIG = _config()

TEXT_EXTS = (".html", ".htm", ".css", ".js", ".json", ".md", ".txt", ".py",
             ".yml", ".yaml", ".toml", ".xml", ".svg", ".sh", ".cff")

DEFAULT = {
    "forbidden": [],
    "allowed": [],
    "skip": ["node_modules", ".git", "dist", "build", "__pycache__",
             "vendor", ".venv"],
}

STARTER = {
    "forbidden": ["oldname"],
    "allowed": [
        {"pattern": "github\\.com/oldname\\b",
         "reason": "the organisation account; renaming breaks every link"},
        {"pattern": "oldname\\.github\\.io",
         "reason": "live Pages origins still serving"},
    ],
    "skip": DEFAULT["skip"],
}


def load(path=CONFIG):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    for key, value in DEFAULT.items():
        cfg.setdefault(key, value)
    cfg["_forbidden"] = [re.compile(p, re.I) for p in cfg["forbidden"]]
    cfg["_allowed"] = [(re.compile(a["pattern"], re.I), a.get("reason", ""))
                       for a in cfg["allowed"]]
    return cfg


def scrub(line, cfg):
    """Remove every allowed identifier, so only branding is left to find."""
    for pattern, _ in cfg["_allowed"]:
        line = pattern.sub("", line)
    return line


def walk(root, cfg):
    skip = set(cfg["skip"])
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
        for name in files:
            if not name.lower().endswith(TEXT_EXTS):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            if rel in skip or os.path.basename(path) in (
                    os.path.basename(__file__), os.path.basename(CONFIG)):
                continue
            yield path, rel


def scan(root, cfg):
    hits = []
    for path, rel in walk(root, cfg):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for n, line in enumerate(fh, 1):
                    left = scrub(line, cfg)
                    for pattern in cfg["_forbidden"]:
                        m = pattern.search(left)
                        if m:
                            hits.append((rel, n, line.strip()[:100], m.group(0)))
                            break
        except OSError:
            continue
    return hits


def _help():
    print("""deadname-gate - Fail a build when a retired name reaches anything a human reads.

usage:
  deadname-gate [PATH] [--config FILE] [--list]

  PATH        directory to check (default: the working directory)
  --config    JSON file: forbidden words, and allowed machine identifiers
  --list      every occurrence rather than the summary
  --root DIR  same as PATH, kept for existing callers

Nothing is forbidden by default. Say what yours is in the config.

Exits 0 when clean, 1 on a finding. Part of readable-gates.
https://f-keys.com/gatekit/""")
    return 0


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        return _help()
    # Packaged, the directory above this file is site-packages,
    # not the project being checked. The working directory is
    # what someone running this in their repo means.
    root = os.environ.get("DEADNAME_ROOT") or os.getcwd()
    if "--root" in sys.argv:
        i = sys.argv.index("--root")
        if i + 1 < len(sys.argv):
            root = os.path.abspath(sys.argv[i + 1])
    else:
        # A bare path was ignored, so `deadname-gate ./site` scanned this
        # repository and reported clean on a tree it never opened. That is
        # the worst possible answer from a gate: a pass nobody earned.
        positional = [a for a in sys.argv[1:] if not a.startswith("-")]
        if positional:
            root = os.path.abspath(positional[0])

    if "--init" in sys.argv:
        if os.path.exists(CONFIG):
            print("  {} already exists; not overwriting it".format(CONFIG))
            return 1
        with open(CONFIG, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(STARTER, fh, indent=2)
        print("  wrote {}".format(CONFIG))
        print("  Put the retired name in 'forbidden', and every machine")
        print("  identifier that must survive in 'allowed', each with the")
        print("  reason it cannot change.")
        return 0

    cfg = load()
    if cfg is None:
        print("  No config. Run --init to write a starter one.")
        return 2
    if not cfg["forbidden"]:
        print("  Nothing is forbidden, so there is nothing to check.")
        print("  Add the retired name to 'forbidden' in {}".format(CONFIG))
        return 2

    if "--list-allowed" in sys.argv:
        print("  allowed by exception:")
        for pattern, reason in cfg["_allowed"]:
            print("    {:<40} {}".format(pattern.pattern, reason))
        return 0

    hits = scan(root, cfg)
    if not hits:
        print("  deadname-gate: clean - no retired name in human-visible text")
        return 0

    print("  deadname-gate: {} line(s) carry a retired name where a person "
          "reads it\n".format(len(hits)))
    for rel, n, line, word in hits:
        print("    {}:{}  [{}]".format(rel, n, word))
        print("      {}".format(line))
    print("\n  Either rewrite these, or if one is a machine identifier that")
    print("  cannot change, add it to 'allowed' in {} with the reason."
          .format(os.path.basename(CONFIG)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
