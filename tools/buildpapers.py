#!/usr/bin/env python3
"""
============================================================
buildpapers - the deposited work, in the shell
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
/papers/ was a different website. Green on black, its own
header, its own navigation, none of the shell the rest of the
site is built from. It holds the most serious thing here -
thirty-five deposited works, every one with a DOI - and it
looked like it belonged to somebody else.

It was also the last page whose numbers were written by hand,
and they were wrong: the header said 33 papers and 3 project
documents against 33 and 2, and "35 of the 36 carry a DOI"
when all 35 do. Every count on this page is now counted.

THE DOCUMENT
The content pane is a word processor, because that is what a
page of papers is. The chrome is the joke; the contents are
not. Titles, dates, kinds, abstracts and DOIs are all still
here, grouped exactly as they were, and the ruler and the
toolbar do not move a single one of them.

Body type is a system serif stack. No typeface is fetched from
anybody's server - the Privacy page says so, and a document
that broke that to look more like Word would be a bad trade.

WORKFLOW STACK
  1. papers.json  - the data, extracted once from the old page
  2. document()   - toolbar, ruler, page, groups, entries
  3. shell()      - the same window every other page uses
  4. --check      - regenerate and diff (CI)

Run:  python tools/buildpapers.py
      python tools/buildpapers.py --check
============================================================
"""

import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import buildsite as B  # noqa: E402

DATA = os.path.join(ROOT, "papers", "papers.json")
OUT = os.path.join(ROOT, "papers", "index.html")

ORCID = "0009-0005-3640-014X"

# The kinds that are papers. Everything else is counted separately,
# because an amendment document is not a paper and saying so is the
# whole reason the group exists.
DOCS_GROUP = "docs"


def esc(s):
    return B.esc(s)


def ruler():
    """A ruler, in inches, with the indent markers Word puts on it.

    Decorative and inert on purpose: it is drawn from the same measure
    the page text uses, so it lines up with the margin rather than
    being a picture of a ruler that lines up with nothing.
    """
    ticks = []
    for i in range(0, 61):
        cls = "maj" if i % 8 == 0 else ("mid" if i % 4 == 0 else "min")
        ticks.append('<i class="%s"></i>' % cls)
    return ('<div class="wruler" aria-hidden="true">'
            '<span class="wr-indent-top"></span>'
            '<span class="wr-indent-bot"></span>'
            '%s</div>' % "".join(ticks))


def toolbar():
    """The formatting toolbar. Inert, and labelled as such for a reader
    using a screen reader, who should not be told there are controls
    here that do nothing."""
    def btn(label, cls=""):
        return '<span class="wbtn %s">%s</span>' % (cls, label)
    return (
        '<div class="wtool" aria-hidden="true">'
        '<span class="wfield wfont">Times New Roman</span>'
        '<span class="wfield wsize">12</span>'
        '<span class="wsep"></span>'
        + btn("B", "b") + btn("I", "i") + btn("U", "u")
        + '<span class="wsep"></span>'
        + btn("&#9776;", "al") + btn("&#9776;", "ac") + btn("&#9776;", "ar")
        + '<span class="wsep"></span>'
        + btn("&#8226;") + btn("1.")
        + '</div>')


def entry_html(e):
    links = " &middot; ".join(
        '<a href="%s"%s>%s</a>' % (
            esc(l["href"]), ' rel="noopener"' if l["href"].startswith("http")
            else "", esc(l["label"]))
        for l in e.get("links") or [])
    meta = " &middot; ".join(x for x in (e.get("date"), e.get("kind")) if x)
    return (
        '<div class="wentry">'
        '<h3><a href="%s">%s</a></h3>'
        '<p class="wmeta">%s</p>'
        '<p class="wabs">%s</p>'
        '<p class="wlinks">%s</p>'
        '</div>' % (esc(e["url"]), esc(e["title"]), esc(meta),
                    esc(e.get("abstract") or ""), links))


def document(data):
    groups = data["groups"]
    papers = sum(len(g["entries"]) for g in groups if g["id"] != DOCS_GROUP)
    docs = sum(len(g["entries"]) for g in groups if g["id"] == DOCS_GROUP)
    total = papers + docs
    with_doi = sum(1 for g in groups for e in g["entries"] if e.get("doi"))

    # "all of them" reads better than "35 of 35", and it is the same
    # claim. It also cannot go stale into a lie the way "35 of the 36"
    # already had.
    doi_claim = ("every one of them carries a DOI" if with_doi == total
                 else "%d of the %d carry a DOI" % (with_doi, total))

    jump = " &middot; ".join(
        '<a href="#%s">%s</a>' % (esc(g["id"]), esc(g["title"]))
        for g in groups if g["id"] != DOCS_GROUP)

    body = []
    for g in groups:
        body.append(
            '<section class="wgroup" id="%s">'
            '<h2>%s <span class="wcount">%d</span></h2>'
            '<p class="wnote">%s</p>%s</section>' % (
                esc(g["id"]), esc(g["title"]), len(g["entries"]),
                esc(g["note"]),
                "".join(entry_html(e) for e in g["entries"])))

    return (
        '<div class="worddoc">'
        + toolbar() + ruler()
        + '<div class="wpage">'
        '<h1>Papers</h1>'
        '<p class="wkicker">%d papers &middot; %d project document%s</p>'
        '<p>Everything below is open access and %s. Full texts are served '
        'from this domain; the rest resolve to Zenodo. Ordered most recent '
        'first within each group.</p>'
        '<p class="wby">Vince Gonzalez &middot; '
        '<a href="https://orcid.org/%s" rel="noopener">ORCID %s</a> &middot; '
        'tooling at <a href="/gonzalgo/">gonzalgo</a></p>'
        '<p class="wjump">%s</p>'
        '%s</div>'
        '<div class="wstatus" aria-hidden="true">'
        '<span>Page 1</span><span>Sec 1</span><span>%d/%d</span>'
        '<span class="grow">At 2.5cm&nbsp;&nbsp;Ln 1&nbsp;&nbsp;Col 1</span>'
        '<span>REC</span><span>TRK</span><span>EXT</span><span>OVR</span>'
        '</div>'
        '</div>' % (papers, docs, "" if docs == 1 else "s", doi_claim,
                    ORCID, ORCID, jump, "".join(body), total, total))


def build():
    with io.open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    total = sum(len(g["entries"]) for g in data["groups"])
    return B.shell(
        "Papers — F-Keys",
        "F-Keys\\Research\\Papers",
        document(data),
        "%d item(s)" % total,
        active_cat="research",
        description=("Thirty-five deposited works by Vincent Gonzalez: axiom "
                     "dependence in formal libraries, certified bounds in "
                     "discrete geometry, the Modulign standard, colour "
                     "vision. Open access, every one with a DOI."),
        canonical="https://f-keys.com/papers/")


def main():
    fresh = build()
    if "--check" in sys.argv:
        current = io.open(OUT, encoding="utf-8").read() \
            if os.path.exists(OUT) else ""
        if current.replace("\r\n", "\n") != fresh.replace("\r\n", "\n"):
            print("buildpapers: papers/index.html is stale")
            print("  run: python tools/buildpapers.py")
            return 1
        print("buildpapers: papers/index.html current")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(fresh)
    with io.open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    print("buildpapers: wrote papers/index.html (%d groups, %d entries)"
          % (len(data["groups"]),
             sum(len(g["entries"]) for g in data["groups"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
