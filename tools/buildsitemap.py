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
generates are read from buildsite, the dates come from git
rather than from a guess, and the entries this tool does not
own - papers, gonzalgo, and anything else added by hand - are
carried through untouched with the lastmod they already had.

WORKFLOW STACK
  1. owned     - the URLs buildsite is responsible for
  2. carried   - every other URL already in the file, kept
                 verbatim so no hand-set date is lost
  3. lastmod   - git's date for the file, not today's
  4. write     - or --check, which fails when the two differ

Run:  python tools/buildsitemap.py
      python tools/buildsitemap.py --check
============================================================
"""

import io
import os
import re
import subprocess
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


def is_shallow():
    """A shallow clone answers every date question with the same day.

    This is not a theory. The first CI run of this check failed with
    159 URLs on both sides, because actions/checkout clones to depth 1
    and git log then reports the checkout commit for every file. A
    tool whose output depends on how the repository was cloned has to
    say so, rather than writing a different file and looking fine.
    """
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        return out == "true"
    except (subprocess.CalledProcessError, OSError):
        return False


def git_date(path):
    """The day this file actually last changed.

    An invented lastmod is worse than none: it tells a crawler to come
    back for a page that did not move. Untracked files fall back to the
    working tree's date, which is the day they are about to be
    committed.
    """
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", path],
            cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        if out:
            return out
    except (subprocess.CalledProcessError, OSError):
        pass
    try:
        stamp = os.path.getmtime(os.path.join(ROOT, path))
        import datetime
        return datetime.date.fromtimestamp(stamp).isoformat()
    except OSError:
        return None


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

    skipped = []
    for url, path, priority in mine:
        if not os.path.exists(os.path.join(ROOT, path)):
            skipped.append(url)
            continue
        lines.append(row.format(BASE, url, git_date(path), priority))

    # Everything this tool does not own is carried through exactly as
    # it was. These are the deposited papers and the gonzalgo index,
    # whose dates mean something and are not this tool's to revise.
    for url, lastmod, priority in existing():
        if url not in mine_urls:
            lines.append(row.format(BASE, url, lastmod, priority))

    lines.append("</urlset>")
    return "\n".join(lines) + "\n", skipped


def main():
    check = "--check" in sys.argv
    if is_shallow():
        print("buildsitemap: this is a shallow clone, so git reports one "
              "date for every file.")
        print("  every lastmod would be wrong. fetch the history first:")
        print("  git fetch --unshallow      "
              "(in CI: actions/checkout with fetch-depth: 0)")
        return 2
    fresh, skipped = build()
    for url in skipped:
        print("  skipped (no file yet): /" + url)

    current = ""
    if os.path.exists(SITEMAP):
        current = io.open(SITEMAP, encoding="utf-8").read()

    if check:
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

    io.open(SITEMAP, "w", encoding="utf-8", newline="\n").write(fresh)
    print("buildsitemap: wrote {} URLs ({} generated, {} carried)".format(
        len(re.findall(r"<loc>", fresh)),
        len(owned()) - len(skipped),
        len(re.findall(r"<loc>", fresh)) - len(owned()) + len(skipped)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
