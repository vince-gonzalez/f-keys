#!/usr/bin/env python3
"""
============================================================
relink_css - put the current stylesheet fingerprint on every
page, including the ones no builder owns
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

win98.css is cache-busted with a short hash of its contents,
and test_site checks that every page links the same one. Most
pages are regenerated whenever the stylesheet changes, so they
pick the new hash up on their own.

Fifty-one do not. The paper pages, the gonzalgo data pages and
Docs.html are committed output that no builder rewrites, so
every edit to the stylesheet left them pointing at the previous
fingerprint and failed the gate. That was fixed by hand three
times in one day, which is two times more than a thing should
be done by hand.

The query string is only a cache key - a stale one still serves
the current stylesheet, so this is hygiene rather than a
visible defect. It is worth automating precisely because it is
boring: a gate that fails for a boring reason is a gate people
start ignoring.

Run:  python tools/relink_css.py
============================================================
"""
import hashlib
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {".git", "node_modules", ".wrangler", "dist", "build", "__pycache__"}


def current():
    """Hash the bytes that SHIP, not the bytes on this disk.

    Git stores LF and checks out CRLF on Windows, so hashing the working
    copy gives a fingerprint no visitor ever receives. Same reasoning as
    css_version() in buildsite.py, and the same normalisation.
    """
    raw = open(os.path.join(ROOT, "win98.css"), "rb").read()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()[:8]


def main():
    want = current()
    changed, scanned = [], 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(base, name)
            scanned += 1
            text = io.open(path, encoding="utf-8", errors="replace").read()
            new = re.sub(r"win98\.css\?v=[0-9a-f]+",
                         "win98.css?v=" + want, text)
            if new != text:
                tmp = path + ".tmp"
                with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(new)
                os.replace(tmp, path)
                changed.append(os.path.relpath(path, ROOT))

    print("relink_css: %s, %d page(s) scanned, %d relinked"
          % (want, scanned, len(changed)))
    for c in changed[:8]:
        print("   %s" % c.replace("\\", "/"))
    if len(changed) > 8:
        print("   ... and %d more" % (len(changed) - 8))
    return 0


if __name__ == "__main__":
    sys.exit(main())
