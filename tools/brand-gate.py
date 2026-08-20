#!/usr/bin/env python3
"""
============================================================
brand-gate v1.0.0
Fails the build if retired brand names appear in anything a
human reads. Machine identifiers are allowed by exception.
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Zengine was dissolved 2026-07-15 and f-keys.com is the company.
The old name kept surviving in page titles, footers and header
comments, which is how it gets copied forward into new work.
A convention you have to remember is not a control. This is.

WORKFLOW STACK
  1. Walk the repo, skipping vendored and generated trees
  2. For each text line, delete every ALLOWED identifier
  3. If a forbidden brand word survives that deletion, it is
     human-visible branding -> report it and exit 1

THE RULE
  Human-visible  (titles, meta, footers, bylines, prose,
                  comments, alt text)          -> must say F-Keys
  Machine identifier (org names, repo paths, live URLs,
                  published artifact names)    -> left alone,
                  because renaming them breaks working links
                  or contradicts a deposited record

Run:  python tools/brand-gate.py
      python tools/brand-gate.py --list-allowed
============================================================
"""

import os
import re
import sys

# The offending lines usually contain (TM) and (C). On a Windows console
# those raise UnicodeEncodeError, which would fail the run for the wrong
# reason and hide the real report.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

FORBIDDEN = re.compile(r"zengine", re.IGNORECASE)

# Each entry: (pattern, why it is allowed to contain the brand word).
# Order does not matter; every pattern is stripped before the check.
ALLOWED = [
    (re.compile(r"github\.com/zengineco\b", re.I),
     "GitHub org URL - renaming breaks every repo and Pages link"),
    (re.compile(r"zengineco\.github\.io", re.I),
     "live GitHub Pages origins (QV, WikiPolish) linked from f-keys.com"),
    (re.compile(r"\bzengineco/[\w.\-]+", re.I),
     "GitHub org namespace: repo paths and Action refs (uses: zengineco/...)"),
    (re.compile(r"\bzengineco\b", re.I),
     "the GitHub org account name itself"),
    (re.compile("zengine" + chr(92) + ".org", re.I),
     "a DNS zone he still owns, reported by name in measured Cloudflare "
     "data. It takes real traffic and redirects to f-keys.com, so renaming "
     "it inside a measurement would make the snapshot wrong. The word "
     "Zengine alone, and zengine.site, still fail."),
    (re.compile(r"ZengineCamBot"),
     "classifier under test in a published paper, DOI 10.5281/zenodo.19643322 - "
     "renaming it here would make the site contradict the deposited record"),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
SKIP_FILES = {"skills-lock.json"}          # tooling lockfile, not published

# The gate's own definition files are exempt: they must name the thing they
# ban in order to ban it. Nothing else gets this exemption.
SKIP_PATHS = {
    "tools/brand-gate.py",
    ".github/workflows/brand-gate.yml",
}

TEXT_EXT = {
    ".html", ".htm", ".md", ".txt", ".py", ".js", ".mjs", ".css",
    ".json", ".yml", ".yaml", ".sh", ".service", ".xml", ".svg",
}


def scrub(line):
    """Remove every allowed identifier so only real branding can survive."""
    for pattern, _ in ALLOWED:
        line = pattern.sub("", line)
    return line


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name in SKIP_FILES:
                continue
            if os.path.splitext(name)[1].lower() not in TEXT_EXT:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if rel in SKIP_PATHS:
                continue
            yield full


def main():
    # Defaults to the repo this script lives in. Pass a path to check any
    # other property with the same rules, e.g.
    #   python tools/brand-gate.py ../wikiscout
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        root = os.path.abspath(args[0])
    else:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if "--list-allowed" in sys.argv:
        print("Allowed by exception:\n")
        for pattern, why in ALLOWED:
            print(f"  {pattern.pattern}\n      {why}\n")
        return 0

    violations = []
    for path in walk(root):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for n, raw in enumerate(fh, 1):
                    if FORBIDDEN.search(scrub(raw)):
                        rel = os.path.relpath(path, root).replace("\\", "/")
                        violations.append((rel, n, raw.strip()[:120]))
        except OSError:
            continue

    if not violations:
        print("brand-gate: clean - no retired brand names in human-visible text")
        return 0

    print(f"brand-gate: FAILED - {len(violations)} occurrence(s) of a retired brand name\n")
    for rel, n, text in violations:
        print(f"  {rel}:{n}")
        print(f"      {text}")
    print("\nThe rule: anything a human reads says F-Keys.")
    print("If this is a machine identifier (org name, repo path, live URL, or a")
    print("published artifact name), add it to ALLOWED in tools/brand-gate.py")
    print("with a one-line reason. Do not weaken FORBIDDEN.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
