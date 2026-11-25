#!/usr/bin/env python3
"""
rewrap_windows - move the last pages still in the Windows 95 window
into the site shell. F-Keys | www.f-keys.com

unify.py reads the current shell and plain <main> pages; it refuses the
older "window" shape. These nine were left in it, still linking
/win98.css. The body inside <main> is moved across verbatim, any page
script (not the JSON-LD, which shell() writes from the parsed block) is
carried after it, and the page is written only if every visible word
survives.

Run:  python tools/rewrap_windows.py --dry
      python tools/rewrap_windows.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.chdir(ROOT)
import buildsite as B   # noqa: E402
import html   # noqa: E402


def visible(s):
    """The words a reader sees (unify.py's rule, copied: unify runs on import)."""
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?is)<(nav|footer)\b.*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return " ".join(html.unescape(s).split())


def grab(pat, s, default=""):
    m = re.search(pat, s, re.S | re.I)
    return m.group(1).strip() if m else default

DRY = "--dry" in sys.argv
B.CSS_V = B.css_version()

# (page, application, catalogue branch the index highlights)
JOBS = [
    ("apps.html", "explorer", None),
    ("games.html", "explorer", None),
    ("properties.html", "explorer", None),
    ("authorecon/index.html", "explorer", "check"),
    ("axsent/index.html", "explorer", "research"),
    ("gonzalgo/data/index.html", "excel", "research"),
    ("gonzalgo/generated-proofs/index.html", "excel", "research"),
    ("status/index.html", "explorer", None),
    ("status/detail/index.html", "explorer", None),
]

bad = 0
for path, app, cat in JOBS:
    raw = io.open(path, encoding="utf-8").read()
    if "/win98.css" not in raw and path not in sys.argv:
        print("  %-40s already moved" % path)
        continue
    main = grab(r"<main\b[^>]*>(.*)</main>", raw)
    if not main:
        print("  %-40s REFUSED: no <main>" % path)
        bad += 1
        continue
    # only scripts outside <main>: the ones inside travel with the body
    outside = raw.replace(main, "")
    scripts = [m.group(0) for m in re.finditer(r"(?is)<script\b[^>]*>.*?</script>", outside)
               if "application/ld+json" not in m.group(0)]
    ld = None
    block = grab(r'(?is)<script type="application/ld\+json">(.*?)</script>', raw)
    if block:
        try:
            ld = json.loads(block)
        except ValueError:
            ld = None
    title = grab(r"<title>(.*?)</title>", raw)
    title = re.sub("&mdash;", "—", title)
    desc = grab(r'name="description"\s+content="(.*?)"', raw)
    canon = grab(r'rel="canonical"\s+href="(.*?)"', raw)
    noindex = bool(re.search(r'name="robots"\s+content="noindex', raw))
    h1 = visible(grab(r"<h1\b[^>]*>(.*?)</h1>", main)) or title
    body = main.strip() + ("\n" + "\n".join(scripts) if scripts else "")
    doc = B.shell(title, "F-Keys\\" + h1[:60], body, "", active_cat=cat,
                  description=desc, canonical=canon, ld=ld, noindex=noindex,
                  app=app)
    lost = set(visible(main).split()) - set(visible(doc).split())
    if main.strip() not in doc or lost:
        print("  %-40s REFUSED: words lost %s" % (path, " ".join(sorted(lost)[:8])))
        bad += 1
        continue
    if not DRY:
        tmp = path + ".tmp"
        io.open(tmp, "w", encoding="utf-8", newline="\n").write(doc)
        os.replace(tmp, path)
    print("  %-40s -> %s%s" % (path, app, " (+%d script)" % len(scripts) if scripts else ""))
sys.exit(1 if bad else 0)
