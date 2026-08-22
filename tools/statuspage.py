#!/usr/bin/env python3
"""
============================================================
statuspage - one spec, rendered on the server and in the page
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The status page was rendered once a day and then frozen, so a
refresh showed whatever the build had baked in. It also showed
five sections of a file that carries far more: package
versions, repositories, licences, response times, sixty days
of history, thirty-five deposited records.

Making it live means the numbers get rendered twice - once
here into the HTML, once in the browser from status/latest.json
- and two renderers of the same thing is exactly how Key-J
shipped three defects. So neither renderer owns the layout.
The SECTIONS below own it, both read from them, and
tools/test_statuspage.py runs the JavaScript under node
against the same snapshot and fails if the two disagree.

WORKFLOW STACK
  1. FORMATS   - the shared vocabulary (num, date, ms, ...)
  2. SECTIONS  - every table, its source and its columns
  3. render_*  - the server side, from SECTIONS
  4. client_js - the browser side, from the same SECTIONS

Run:  imported by tools/snapshot.py
      python tools/test_statuspage.py   (parity)
============================================================
"""

import datetime
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── 1. the shared vocabulary ─────────────────────────────────
# Every formatter here has a twin in client_js(). The parity test
# is what keeps the pair honest; adding one here without adding it
# there fails the build rather than silently rendering "undefined".
def f_num(v):
    return "—" if v is None else "{:,}".format(v)


def f_text(v):
    return "—" if v in (None, "") else str(v)


def f_ms(v):
    return "—" if v is None else "{:,}ms".format(v)


def f_date(v):
    """An ISO timestamp down to the day. Anyone who needs the hour can
    read the JSON; on the page it is noise."""
    return "—" if not v else str(v)[:10]


def f_ver(v):
    return "—" if not v else "v" + str(v)


def f_up(v):
    return "UP" if v else "DOWN"


FORMATS = {"num": f_num, "text": f_text, "ms": f_ms,
           "date": f_date, "ver": f_ver, "up": f_up}


# ── 2. what the page is ──────────────────────────────────────
# (id, heading, note, source key, columns)
# A column is (label, path-into-the-row, format, css class).
SECTIONS = [
    ("packages", "Packages",
     "Every published package, the version currently on the registry, and "
     "what it is being installed at. A package that is published and absent "
     "from this table reads exactly like one that does not exist.",
     "packages",
     [("Package", "package", "text", ""),
      ("Registry", "registry", "text", "dim"),
      ("Version", "version", "ver", ""),
      ("Released", "released", "date", "dim"),
      ("Week", "weekly", "num", "num"),
      ("All time", "all_time", "num", "num")]),

    ("repos", "Repositories",
     "Public source. A repository with no licence cannot legally be reused "
     "by anyone who finds it, so that column is reported rather than left "
     "for a reader to discover.",
     "github",
     [("Repository", "full_name", "text", ""),
      ("Language", "language", "text", "dim"),
      ("Licence", "license", "text", "dim"),
      ("Stars", "stars", "num", "num"),
      ("Forks", "forks", "num", "num"),
      ("Issues", "open_issues", "num", "num"),
      ("Last push", "pushed_at", "date", "dim")]),

    ("uptime", "Properties",
     "Every public property, checked from outside on each run, with the "
     "time it took to answer.",
     "uptime",
     [("Property", "name", "text", ""),
      ("State", "up", "up", ""),
      ("Response", "ms", "ms", "num")]),

    ("traffic", "Traffic by property",
     "Seven days, from Cloudflare. Unique visitors and page views per site, "
     "with the country the largest share of requests came from.",
     "cloudflare.sites",
     [("Property", "site", "text", ""),
      ("Visitors", "uniques", "num", "num"),
      ("Page views", "page_views", "num", "num"),
      ("Requests", "requests", "num", "num"),
      ("Threats", "threats", "num", "num")]),

    ("papers", "Deposited works",
     "Every record with a DOI, and what it has actually been read and "
     "downloaded. Sorted by downloads, because a download is someone taking "
     "the thing away rather than glancing at it.",
     "zenodo.records",
     [("Record", "title", "text", ""),
      ("Views", "views", "num", "num"),
      ("Downloads", "downloads", "num", "num")]),
]

# The headline figures, in the order they read. (label, key, format)
HEADLINE = [
    ("Visitors · 7d", "visitors_7d", "num"),
    ("Page views · 7d", "page_views_7d", "num"),
    ("Properties up", "properties_up", "num"),
    ("Median response", "median_response_ms", "ms"),
    ("Packages published", "packages_total", "num"),
    ("Installs · week", "package_weekly", "num"),
    ("Installs · all time", "package_all_time", "num"),
    ("Repositories", "github_repos", "num"),
    ("Stars", "github_stars", "num"),
    ("Open issues", "open_issues", "num"),
    ("Repos without a licence", "repos_unlicensed", "num"),
    ("Deposited records", "zenodo_records", "num"),
    ("Paper views", "zenodo_views", "num"),
    ("Paper downloads", "zenodo_downloads", "num"),
]

# What the trend strip plots. (label, key)
TRENDS = [
    ("Page views · 7d", "page_views_7d"),
    ("Visitors · 7d", "visitors_7d"),
    ("Installs · week", "package_weekly"),
    ("Paper downloads", "zenodo_downloads"),
]


def dig(obj, path):
    """`cloudflare.sites` out of the snapshot, or None if any hop is
    missing - a source that failed must not take the page down."""
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def rows_for(snap, source):
    """`packages` is the one source that is assembled rather than read:
    npm and PyPI are two lists of the same shape and one table."""
    if source == "packages":
        return (snap.get("npm") or []) + (snap.get("pypi") or [])
    got = dig(snap, source)
    return got if isinstance(got, list) else []


def sort_rows(section_id, rows):
    if section_id == "papers":
        return sorted(rows, key=lambda r: -(r.get("downloads") or 0))
    if section_id == "repos":
        return sorted(rows, key=lambda r: (-(r.get("stars") or 0),
                                           r.get("full_name") or ""))
    if section_id == "packages":
        return sorted(rows, key=lambda r: -(r.get("weekly") or 0))
    if section_id == "traffic":
        return sorted(rows, key=lambda r: -(r.get("page_views") or 0))
    return rows


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ── 3. the server side ───────────────────────────────────────
def render_table(section, snap):
    sid, heading, note, source, cols = section
    rows = sort_rows(sid, rows_for(snap, source))
    head = "".join('<th class="{}">{}</th>'.format(c[3], esc(c[0])) for c in cols)
    body = []
    for r in rows:
        cells = []
        for label, key, fmt, cls in cols:
            val = FORMATS[fmt](r.get(key))
            cells.append('<td class="{}">{}</td>'.format(cls, esc(val)))
        body.append("<tr>" + "".join(cells) + "</tr>")
    return ('<h2 id="{sid}">{h}</h2><p class="dim">{note}</p>'
            '<div class="scroll"><table class="details" data-table="{sid}">'
            "<thead><tr>{head}</tr></thead>"
            '<tbody data-body="{sid}">{body}</tbody></table></div>').format(
        sid=sid, h=esc(heading), note=esc(note), head=head,
        body="".join(body) or '<tr><td class="dim">no data</td></tr>')


def render_headline(snap):
    s = snap.get("summary") or {}
    out = []
    for label, key, fmt in HEADLINE:
        out.append('<tr><th>{}</th><td class="num" data-k="{}" data-f="{}">{}</td></tr>'
                   .format(esc(label), key, fmt, esc(FORMATS[fmt](s.get(key)))))
    return '<table class="facts">' + "".join(out) + "</table>"


def spark(values, width=180, height=28):
    """A line, not a chart library. Sixty points of one number is a shape
    a reader takes in without reading any of it."""
    pts = [v for v in values if v is not None]
    if len(pts) < 2:
        return ""
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1
    step = width / float(len(pts) - 1)
    coords = " ".join(
        "{:.1f},{:.1f}".format(i * step, height - ((v - lo) / span) * (height - 4) - 2)
        for i, v in enumerate(pts))
    return ('<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            'preserveAspectRatio="none" aria-hidden="true">'
            '<polyline points="{p}"/></svg>').format(w=width, h=height, p=coords)


def render_trends(snap):
    hist = snap.get("history") or []
    if len(hist) < 2:
        return ('<p class="dim">Trends appear once there are two days of '
                'history. The series is built from status/data/.</p>')
    out = []
    for label, key in TRENDS:
        vals = [h.get(key) for h in hist]
        pts = [v for v in vals if v is not None]
        first, last = (pts[0], pts[-1]) if pts else (None, None)
        delta = ""
        if first is not None and last is not None and first != last:
            diff = last - first
            delta = ('<span class="{}">{}{:,}</span>'
                     .format("up" if diff > 0 else "down",
                             "+" if diff > 0 else "", diff))
        out.append('<tr><th>{}</th><td class="num">{} {}</td>'
                   '<td class="num" data-spark="{}">{}</td></tr>'
                   .format(esc(label), esc(f_num(last)), delta, key, spark(vals)))
    return ('<table class="facts">' + "".join(out) + "</table>"
            '<p class="dim">Over the last {} day(s) on record.</p>'
            .format(len(hist)))
