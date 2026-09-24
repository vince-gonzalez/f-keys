#!/usr/bin/env python3
"""
============================================================
buildsearch - the index, and the box that filters it
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
There was no way into this site except the front door. The four
CV pages were live and had zero inbound links, were absent from
the sitemap, and /cv/ itself was a 404 - so a recruiter who
landed on the homepage could not reach a resume by any route,
and neither could a crawler.

HOW IT WORKS
/search/ is a complete index of the site, rendered as HTML at
build time. The box filters it in the browser. That order
matters: the page is useful with JavaScript switched off,
because then it is simply the whole index, which is the thing
that was missing. A JavaScript-only search would have left the
no-JS reader exactly where they started.

It writes:
  search/index.html   the index, filterable
  search-index.json   the same rows, for anything that wants them

Run:  python tools/buildsearch.py
============================================================
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import buildsite as B  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


# Pages that are not products and not generated from the catalogue.
# The CV lanes lead, because being unreachable is what this fixes.
STANDING = [
    ("/cv/founder/", "CV - founder", "Document",
     "Company, products shipped, what was built and run end to end."),
    ("/cv/operations/", "CV - operations", "Document",
     "Logistics and operations record."),
    ("/cv/research/", "CV - research", "Document",
     "Formal methods, deposits, upstream contributions."),
    ("/cv/writing/", "CV - writing", "Document",
     "Published writing and documentation."),
    ("/papers/", "Papers", "Index",
     "Deposited work, each entry with a DOI."),
    ("/log/", "Log", "Record",
     "What got built, what broke, what turned out to be true."),
    ("/status/", "Status", "Record",
     "Measured uptime, installs and reach. Regenerated daily."),
    ("/about.html", "About", "Document", "Entity, scope, subjects."),
    ("/contact.html", "Contact", "Document",
     "Email, filing details, what to write about."),
    ("/developers.html", "Developers", "Index",
     "Packages, command-line tools and published JSON."),
    ("/Docs.html", "Docs", "Document", "RemapWrap documentation."),
    ("/intake/", "Website builds", "Service",
     "Local business websites. Fixed build fee, monthly hosting."),
    ("/privacy.html", "Privacy", "Document",
     "Every byte this site receives."),
]


def rows():
    """Every addressable thing on this site, product rows first."""
    out = []
    for slug, name, cat, kind, status, blurb, href in B.CATALOGUE:
        out.append({"name": name, "kind": kind, "status": status[0],
                    "text": blurb, "href": href, "group": cat})
    for href, name, kind, text in STANDING:
        out.append({"name": name, "kind": kind, "status": "",
                    "text": text, "href": href, "group": "site"})
    return out


PAGE = """<div class="doc" style="padding-bottom:6px">
<h1>Find</h1>
<p class="sub">Everything on this site, filtered as you type.</p>
<p><input id="q" type="search" placeholder="name, type or word"
   autocomplete="off" spellcheck="false"
   style="width:100%%;max-width:34em;padding:6px 8px;font:inherit;"></p>
<p id="count" class="sub" style="margin:0 0 10px;">%(total)d entries</p>
</div>
<table class="listing" id="results">
<thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Description</th></tr></thead>
<tbody>
%(body)s
</tbody></table>
<script>
/* The rows are already in the page. This only hides the ones that do not
   match, so the index still reads with scripting switched off. */
(function () {
  var q = document.getElementById('q');
  var rows = [].slice.call(document.querySelectorAll('#results tbody tr'));
  var count = document.getElementById('count');
  if (!q) return;
  rows.forEach(function (r) { r.dataset.hay = r.textContent.toLowerCase(); });
  function run() {
    var terms = q.value.toLowerCase().split(/\\s+/).filter(Boolean);
    var shown = 0;
    rows.forEach(function (r) {
      var hit = terms.every(function (t) { return r.dataset.hay.indexOf(t) > -1; });
      r.hidden = !hit;
      if (hit) shown++;
    });
    count.textContent = shown + (shown === 1 ? ' entry' : ' entries');
  }
  q.addEventListener('input', run);
  var pre = new URLSearchParams(location.search).get('q');
  if (pre) { q.value = pre; run(); }
  q.focus();
})();
</script>"""


def main():
    data = rows()
    body = []
    for r in data:
        ext = ' rel="noopener"' if r["href"].startswith("http") else ""
        body.append(
            '<tr><td><a href="{href}"{ext}>{name}</a></td>'
            '<td>{kind}</td><td>{status}</td><td>{text}</td></tr>'.format(
                href=B.esc(r["href"]), ext=ext, name=B.esc(r["name"]),
                kind=B.esc(r["kind"]), status=B.esc(r["status"]),
                text=B.esc(r["text"])))

    page = PAGE % {"total": len(data), "body": "\n".join(body)}
    html = B.shell("Find — F-Keys", "F-Keys\\Find", page,
                   "%d object(s)" % len(data),
                   description="Index of everything on f-keys.com.",
                   canonical="https://f-keys.com/search/")

    d = os.path.join(ROOT, "search")
    os.makedirs(d, exist_ok=True)
    io.open(os.path.join(d, "index.html"), "w",
            encoding="utf-8", newline="\n").write(html)
    io.open(os.path.join(ROOT, "search-index.json"), "w",
            encoding="utf-8", newline="\n").write(
        json.dumps(data, indent=1, ensure_ascii=False))

    print("buildsearch: /search/ with %d entries" % len(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
