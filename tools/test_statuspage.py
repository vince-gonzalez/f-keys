#!/usr/bin/env python3
"""
============================================================
test_statuspage - the two renderers agree, or the build fails
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The status page is rendered twice: once into the HTML by
tools/statuspage.py, and once in the browser by
status/status.js when it re-reads status/latest.json. Two
implementations of one thing is precisely how Key-J shipped
three defects, and this pair is worse than most - the drift
would only appear to a reader with JavaScript on, comparing
against a page they cannot see.

So this renders every table both ways from the same snapshot
and fails on the first character that differs. The formatters
are the likely place to drift: Python's "{:,}" and a
JavaScript regex agree on 1,417 and have to be made to agree
on null, on zero, and on a float.

Run:  python tools/test_statuspage.py
============================================================
"""

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import statuspage as SP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(ROOT, "status", "latest.json")
CLIENT = os.path.join(ROOT, "status", "status.js")

# Rows that exercise the edges the formatters actually meet: a missing
# number, a zero, a false, an empty string, a value that needs commas.
EDGE_SNAPSHOT = {
    "npm": [{"package": "a", "registry": "npm", "version": None,
             "released": None, "weekly": 0, "all_time": None}],
    "pypi": [{"package": "b", "registry": "PyPI", "version": "1.0.0",
              "released": "2026-08-22T01:02:03.000Z", "weekly": 1417,
              "all_time": 1234567}],
    "github": [{"full_name": "o/r", "language": None, "license": None,
                "stars": 0, "forks": None, "open_issues": 0,
                "pushed_at": "2026-08-22T01:02:03Z"}],
    "uptime": [{"name": "up.example", "up": True, "ms": 1234},
               {"name": "down.example", "up": False, "ms": 0}],
    "cloudflare": {"sites": [{"site": "s", "uniques": None, "page_views": 0,
                              "requests": 1000, "threats": None}]},
    "zenodo": {"records": [{"title": "", "views": None, "downloads": 7}]},
    "summary": {},
}


def spec_for_client():
    return {
        "sections": [{"id": s[0], "source": s[3], "columns": s[4]}
                     for s in SP.SECTIONS],
    }


def js_render(snap):
    """Run the browser renderer under node against the same snapshot.

    The payload goes through a file rather than argv: a real snapshot is
    well past the command-line length limit on Windows, and a test that
    only passes on short input is not a test.
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="statuspage-")
    snap_path = os.path.join(tmp, "snap.json")
    spec_path = os.path.join(tmp, "spec.json")
    with io.open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snap, f)
    with io.open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec_for_client(), f)

    script = """
      var fs = require("fs");
      var api = require({client});
      var snap = JSON.parse(fs.readFileSync({snap}, "utf8"));
      var spec = JSON.parse(fs.readFileSync({spec}, "utf8"));
      var out = {{}};
      spec.sections.forEach(function (s) {{ out[s.id] = api.renderBody(s, snap); }});
      process.stdout.write(JSON.stringify(out));
    """.format(client=json.dumps(CLIENT.replace("\\", "/")),
               snap=json.dumps(snap_path.replace("\\", "/")),
               spec=json.dumps(spec_path.replace("\\", "/")))

    # text=True decodes with the locale encoding, which on Windows is
    # cp1252 and turns every em dash into three characters. The
    # renderers agreed; the harness reading them did not.
    r = subprocess.run(["node", "-e", script], capture_output=True,
                       text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("node failed:\n" + (r.stderr or "")[:2000])
    return json.loads(r.stdout)


def py_render(snap):
    out = {}
    for sec in SP.SECTIONS:
        sid, _h, _n, source, cols = sec
        rows = SP.sort_rows(sid, SP.rows_for(snap, source))
        body = []
        for r in rows:
            cells = "".join(
                '<td class="{}">{}</td>'.format(
                    cls, SP.esc(SP.FORMATS[fmt](r.get(key))))
                for _label, key, fmt, cls in cols)
            body.append("<tr>" + cells + "</tr>")
        out[sid] = "".join(body) or '<tr><td class="dim">no data</td></tr>'
    return out


def compare(name, snap, failures):
    js = js_render(snap)
    py = py_render(snap)
    for sid in py:
        if py[sid] != js.get(sid):
            failures.append(
                "{} / {}:\n      python: {}\n      js:     {}".format(
                    name, sid, py[sid][:220], (js.get(sid) or "")[:220]))


def main():
    failures = []

    compare("edge cases", EDGE_SNAPSHOT, failures)

    if os.path.exists(SNAPSHOT):
        with io.open(SNAPSHOT, encoding="utf-8") as f:
            compare("the live snapshot", json.load(f), failures)
    else:
        print("test_statuspage: no status/latest.json to compare against")

    # every format named in a column must exist on both sides
    used = set(c[2] for s in SP.SECTIONS for c in s[4])
    used |= set(f for _l, _k, f in SP.HEADLINE)
    client = io.open(CLIENT, encoding="utf-8").read()
    for fmt in sorted(used):
        if fmt not in SP.FORMATS:
            failures.append("format {!r} is used but not defined in Python"
                            .format(fmt))
        if (fmt + ":") not in client:
            failures.append("format {!r} is used but not defined in status.js"
                            .format(fmt))

    # ── the trend and the summary have to agree ──────────────
    # They did not. history was built from the dated files on disk while
    # today's file had not been written yet, so the series ended one day
    # short of the snapshot carrying it - and the page showed 41,768 page
    # views in the summary and 42,629 in the trend, for the same metric,
    # at the same moment. A status page that contradicts itself is worse
    # than one that is merely out of date: it tells a reader that none of
    # the numbers can be trusted, which is the opposite of its job.
    if os.path.exists(SNAPSHOT):
        with io.open(SNAPSHOT, encoding="utf-8") as f:
            snap = json.load(f)
        hist = snap.get("history") or []
        summary = snap.get("summary") or {}
        if hist:
            last = hist[-1]
            if last.get("date") != snap.get("date"):
                failures.append(
                    "history ends {} but the snapshot is dated {} - the "
                    "trend renders yesterday as today"
                    .format(last.get("date"), snap.get("date")))
            for key in ("page_views_7d", "visitors_7d", "package_weekly"):
                a, b = last.get(key), summary.get(key)
                if a is not None and b is not None and a != b:
                    failures.append(
                        "{}: the trend says {} and the summary says {}"
                        .format(key, a, b))

    if failures:
        print("test_statuspage: {} FAILED\n".format(len(failures)))
        for f in failures:
            print("  - " + f + "\n")
        return 1
    print("test_statuspage: the server and the browser render the same page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
