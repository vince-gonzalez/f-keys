#!/usr/bin/env python3
"""
============================================================
unify - put every page in the same window
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

The site had grown three visual identities. The catalogue was a
Windows desktop. /gonzalgo/ was a green terminal, then a serif
document page. /papers/ was a serif document page. Docs,
portfolio and the CVs were a fourth thing again. A reader
moving between them had no reason to think they were on one
site, and he had asked for this four times.

So every page is now a window on the same desktop, and the
only thing that varies is which APPLICATION the window belongs
to. A grid of measurements belongs in a spreadsheet; a paper
belongs in a word processor; a file listing belongs in the file
manager. That is a difference a reader already understands,
and it does not need a second colour scheme to express it.

WHAT IT WILL NOT DO

The body of each page is moved across VERBATIM. The paper
abstracts have DOIs and the deposited text cannot be edited
after the fact, so this script compares the visible text
before and after and REFUSES to write anything if a single
character of it changed. Chrome is replaced; content is not
touched.

Run:  python tools/unify.py --dry
      python tools/unify.py
============================================================
"""

import glob
import html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import buildsite as B   # noqa: E402

DRY = "--dry" in sys.argv

# (glob, which application, which catalogue branch the tree highlights)
JOBS = [
    ("papers/*/index.html", "wordpad", "research"),
    ("gonzalgo/*/index.html", "excel", "research"),
    ("gonzalgo/index.html", "excel", "research"),
    ("Docs.html", "wordpad", None),
    ("portfolio.html", "wordpad", None),
]


def visible(s):
    """The words a reader sees, for comparing before against after."""
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?is)<(nav|footer)\b.*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return " ".join(html.unescape(s).split())


def grab(pat, s, default=""):
    m = re.search(pat, s, re.S | re.I)
    return m.group(1).strip() if m else default


def convert(path, app, cat):
    raw = io.open(path, encoding="utf-8").read()

    if 'class="window' in raw:
        # Already converted, so re-emit it. This has to be repeatable: a
        # one-shot converter leaves these pages frozen, and the first
        # time the stylesheet changed they kept a hash describing a file
        # nobody is served. shell() writes the content section in one
        # exact shape, so it can be read back out of the same shape.
        main = grab(r'<section class="content sunken[^"]*">\s*'
                    r'<div class="doc">(.*?)\n</div>\s*</section>', raw)
        if not main:
            return None, "in the shell but its content could not be read back"
    else:
        main = grab(r"<main\b[^>]*>(.*?)</main>", raw)
        if not main:
            return None, "no <main>"

    title = html.unescape(grab(r"<title>(.*?)</title>", raw))
    desc = html.unescape(grab(r'name="description"\s+content="(.*?)"', raw))
    canon = grab(r'rel="canonical"\s+href="(.*?)"', raw)

    ld = None
    blocks = re.findall(
        r'(?is)<script type="application/ld\+json">(.*?)</script>', raw)
    if blocks:
        try:
            ld = json.loads(blocks[0])
        except ValueError:
            ld = None

    h1 = visible(grab(r"<h1\b[^>]*>(.*?)</h1>", main)) or title
    body = '<div class="doc">\n%s\n</div>' % main.strip()

    doc = B.shell(
        title,
        h1[:60],
        body,
        "%s" % ("measurements" if app == "excel" else "document"),
        active_cat=cat,
        description=desc,
        canonical=canon,
        ld=ld,
        app=app)

    # The check that means something: the new page must CONTAIN the old
    # <main> byte for byte. Comparing whole pages only reports the
    # chrome as added text, and re-extracting the content with a regex
    # just tests the regex, because nested </div> ends a lazy match
    # early and reads as lost content when nothing was lost.
    if main.strip() not in doc:
        return None, "content did not survive verbatim"
    # and nothing of the original's words may have gone missing
    missing = set(visible(main).split()) - set(visible(doc).split())
    if missing:
        return None, "words lost: " + " ".join(sorted(missing)[:8])
    return doc, "ok"


changed, skipped, failed = [], [], []
for pattern, app, cat in JOBS:
    for path in sorted(glob.glob(pattern)):
        doc, why = convert(path, app, cat)
        if doc is None:
            (skipped if why in ("already in the shell",) else failed).append(
                (path, why))
            continue
        if not DRY:
            io.open(path, "w", encoding="utf-8", newline="\n").write(doc)
        changed.append((path, app))

for path, app in changed:
    print("  %-62s -> %s" % (path, app))
if skipped:
    print("\n  skipped %d already in the shell" % len(skipped))
if failed:
    print("\n  REFUSED %d:" % len(failed))
    for path, why in failed:
        print("    %-52s %s" % (path, why))

print("\n  %s %d page(s); every one's visible text compared before and "
      "after" % ("would convert" if DRY else "converted", len(changed)))
sys.exit(1 if failed else 0)
