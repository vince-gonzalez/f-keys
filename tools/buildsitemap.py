#!/usr/bin/env python3
"""
============================================================
buildsitemap - the sitemap, derived instead of remembered
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
sitemap.xml was written by hand. On the day this ran for the
first time it listed 129 URLs, of which 121 were papers and
gonzalgo pages that had a generator behind them. Of the 24
product pages the site builds, it listed one. apps.html,
games.html, tools.html, hardware.html, research.html,
properties.html and about.html were not in it either.

Nothing was broken and nothing looked wrong. Every URL the
sitemap listed did exist, so the check that read it passed
every time - it only ever asked the question in the direction
that could not fail.

So the sitemap is no longer remembered. The pages buildsite
generates are read from buildsite, and the entries this tool
does not own - papers, gonzalgo, and anything added by hand -
are carried through untouched with the lastmod they already
had.

lastmod does NOT come from git. It did, and git could not
answer the question: the sitemap is generated BEFORE the commit
that changes these pages, so `git log -1` returned each page's
PREVIOUS commit date, and the moment the result was committed
the same command in CI returned today. The check failed with
159 URLs on both sides and no way to reconcile them, because
committing the tool's output changed its input.

Each page's content is hashed instead, and the hash and the
date are stored together in sitemap-dates.json. An unchanged
page keeps its date; a changed one gets today. It is also the
better answer - lastmod now means the day the content changed,
not the day somebody committed a reformat that touched it.

WORKFLOW STACK
  1. owned     - the URLs buildsite is responsible for
  2. carried   - every other URL already in the file, kept
                 verbatim so no hand-set date is lost
  3. lastmod   - the day the CONTENT changed, by hash
  4. write     - or --check, which fails when the two differ

Run:  python tools/buildsitemap.py
      python tools/buildsitemap.py --check
============================================================
"""

import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import buildsite  # noqa: E402

SITEMAP = os.path.join(ROOT, "sitemap.xml")
BASE = "https://f-keys.com/"

# The 404 is deliberately absent: it is noindex, and a sitemap is a
# request to index. Listing it asks a crawler to do the one thing the
# page's own meta tag tells it not to.
SECTIONS = ["apps.html", "games.html", "tools.html", "hardware.html",
            "research.html", "properties.html"]
STANDING = ["about.html", "contact.html", "privacy.html", "developers.html"]


DATES = os.path.join(ROOT, "sitemap-dates.json")


def load_dates():
    if not os.path.exists(DATES):
        return {}
    try:
        with io.open(DATES, encoding="utf-8") as f:
            return json.load(f)
    except ValueError:
        return {}


def content_sha(path):
    full = os.path.join(ROOT, path)
    h = hashlib.sha256()
    with open(full, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def today():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def lastmod_for(url, path, state, changed):
    """The day this page's content last changed, remembered alongside it.

    The first version asked git, and git could not answer the question
    being asked. The sitemap is generated BEFORE the commit that changes
    these pages, so `git log -1` returned each page's PREVIOUS commit
    date; the moment the result was committed, the same command in CI
    returned today, and the check failed with 159 URLs on both sides and
    no way to reconcile them. The tool could not agree with itself,
    because committing its output changed its input.

    So the date is not derived from the repository at all. Each page's
    content is hashed and the pair is stored. An unchanged page keeps
    the date it had, a changed one gets today, and CI recomputes the
    same hashes and therefore the same file. It is also a better answer:
    lastmod now means the day the content changed, not the day somebody
    committed a reformat that touched it.
    """
    entry = state.get(url) or {}
    sha = content_sha(path)
    if entry.get("sha") == sha and entry.get("lastmod"):
        return entry["lastmod"]
    stamp = entry.get("lastmod") or today()
    if entry.get("sha") != sha:
        stamp = today()
    changed[url] = {"sha": sha, "lastmod": stamp}
    return stamp


def owned():
    """Every URL buildsite is responsible for, with its priority."""
    out = [("", "index.html", "1.0")]
    for name in SECTIONS:
        out.append((name, name, "0.8"))
    for slug in buildsite.PAGES:
        out.append((slug + "/", os.path.join(slug, "index.html"), "0.8"))
    for name in STANDING:
        out.append((name, name, "0.7"))
    return out


def existing():
    """What the file says now: url -> (lastmod, priority), in order."""
    if not os.path.exists(SITEMAP):
        return []
    s = io.open(SITEMAP, encoding="utf-8").read()
    return re.findall(
        r"<loc>" + re.escape(BASE) + r"([^<]*)</loc>"
        r"\s*<lastmod>([^<]*)</lastmod>\s*<priority>([^<]*)</priority>", s)


def build():
    mine = owned()
    mine_urls = set(u for u, _, _ in mine)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    row = ('  <url><loc>{}{}</loc><lastmod>{}</lastmod>'
           '<priority>{}</priority></url>')

    state = load_dates()
    changed = {}
    skipped = []
    for url, path, priority in mine:
        if not os.path.exists(os.path.join(ROOT, path)):
            skipped.append(url)
            continue
        lines.append(row.format(
            BASE, url, lastmod_for(url, path, state, changed), priority))

    # Everything this tool does not own is carried through exactly as
    # it was. These are the deposited papers and the gonzalgo index,
    # whose dates mean something and are not this tool's to revise.
    for url, lastmod, priority in existing():
        if url not in mine_urls:
            lines.append(row.format(BASE, url, lastmod, priority))

    lines.append("</urlset>")
    return "\n".join(lines) + "\n", skipped, changed


def main():
    check = "--check" in sys.argv
    fresh, skipped, changed = build()
    for url in skipped:
        print("  skipped (no file yet): /" + url)

    current = ""
    if os.path.exists(SITEMAP):
        current = io.open(SITEMAP, encoding="utf-8").read()

    if check:
        if changed:
            print("buildsitemap: {} page(s) changed since sitemap-dates.json "
                  "was written:".format(len(changed)))
            for url in sorted(changed)[:8]:
                print("    /" + url)
            print("  run: python tools/buildsitemap.py")
            return 1
        if current != fresh:
            was = len(re.findall(r"<loc>", current))
            now = len(re.findall(r"<loc>", fresh))
            print("buildsitemap: sitemap.xml is stale "
                  "({} URLs on disk, {} generated)".format(was, now))
            print("  run: python tools/buildsitemap.py")
            return 1
        print("buildsitemap: sitemap.xml current "
              "({} URLs)".format(len(re.findall(r"<loc>", fresh))))
        return 0

    state = load_dates()
    state.update(changed)
    # Drop URLs that are no longer served, so the file does not grow a
    # tail of dates for pages that stopped existing.
    live = set(u for u, _, _ in owned())
    state = dict((k, v) for k, v in state.items() if k in live)
    with io.open(DATES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=1, sort_keys=True)

    io.open(SITEMAP, "w", encoding="utf-8", newline="\n").write(fresh)
    print("buildsitemap: wrote {} URLs ({} generated, {} carried)".format(
        len(re.findall(r"<loc>", fresh)),
        len(owned()) - len(skipped),
        len(re.findall(r"<loc>", fresh)) - len(owned()) + len(skipped)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
