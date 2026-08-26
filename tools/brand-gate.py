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
    # deadname_gate is this gate generalised, and its config names the
    # retired word in order to forbid it. A file that must contain the word
    # to do its job is skipped for the same reason this file is.
    "tools/deadname_gate.py",
    "tools/deadname_gate.json",
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


if __name__ == "__main__" and "--commits" not in sys.argv:
    sys.exit(main())


# ── commit messages ──────────────────────────────────────────
# Added 2026-08-26. The rule "no Claude attribution in this repository"
# was stated, recorded, and then broken fifteen times in one sitting,
# because the trailer is a default that has to be actively suppressed on
# every single commit. A rule that depends on remembering is not a rule.
#
# This reads the messages rather than the files, so it catches the one
# place the rest of this script cannot see.
ATTRIBUTION = (
    r"co-authored-by:\s*claude",
    r"co-authored-by:.*@anthropic\.com",
    r"generated with .{0,20}claude code",
    r"\U0001F916 generated with",
)


def check_commits(rev_range=None):
    """Fail if any commit message in the range carries AI attribution."""
    import subprocess
    rng = rev_range or "origin/main..HEAD"
    try:
        out = subprocess.run(["git", "log", "--format=%H%x00%B%x00%x00", rng],
                             capture_output=True, text=True,
                             cwd=os.path.dirname(os.path.dirname(
                                 os.path.abspath(__file__))),
                             encoding="utf-8", errors="replace")
    except Exception as e:
        # A gate that cannot read what it guards has not found it clean.
        # The first version of this returned 0 here and reported success
        # while raising NameError internally, which is the whole failure
        # mode this file exists to prevent.
        print("brand-gate: FAILED - could not read commit messages:", e)
        return 1
    if out.returncode != 0:
        print("brand-gate: FAILED - git log {!r} did not run: {}"
              .format(rng, (out.stderr or "").strip()[:160]))
        return 1

    bad = []
    for entry in (out.stdout or "").split("\x00\x00"):
        if "\x00" not in entry:
            continue
        sha, message = entry.split("\x00", 1)
        for pattern in ATTRIBUTION:
            hit = re.search(pattern, message, re.I)
            if hit:
                bad.append((sha.strip()[:8], hit.group(0).strip()))
                break

    if not bad:
        print("brand-gate: commit messages clean - no AI attribution")
        return 0

    print("brand-gate: FAILED - {} commit(s) carry AI attribution\n"
          .format(len(bad)))
    for sha, hit in bad:
        print("  {}  {!r}".format(sha, hit))
    print("\n  This repository does not credit a model for the work. Strip the"
          "\n  trailer and amend, or rewrite the range:"
          "\n    git filter-branch -f --msg-filter"
          " 'sed \"/^Co-Authored-By: Claude/d\"' <range>")
    return 1


if __name__ == "__main__" and "--commits" in sys.argv:
    _i = sys.argv.index("--commits")
    sys.exit(check_commits(sys.argv[_i + 1] if _i + 1 < len(sys.argv) else None))
