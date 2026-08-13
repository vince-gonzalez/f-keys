"""Build every gonzalgo index, the hub that lists them, and the sitemap rows.

    python gonzalgo/_build/build_all.py

Run this rather than the individual scripts. The hub is generated from what the
indexes actually emitted, so an index cannot be published and left off the
catalogue, and the sitemap is rewritten from the same list, so the data files
cannot be live but unlisted.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SITE / "gonzalgo"))

import indexlib  # noqa: E402
from indexlib import BASE, CSS, LICENSE, ORCID, SERIES_DOI, check_fonts  # noqa: E402

import mk_kernel_index  # noqa: E402
import mk_dominator_table  # noqa: E402
import mk_controlled_tactics  # noqa: E402
import mk_spend_points  # noqa: E402
import mk_substitution  # noqa: E402
import mk_entry_points  # noqa: E402
import mk_tactic_bands  # noqa: E402
import mk_cleanable  # noqa: E402
import mk_setmm_axioms  # noqa: E402
import mk_site_diagnosis  # noqa: E402
import mk_choice_strength  # noqa: E402
import mk_version_delta  # noqa: E402
import buildnote  # noqa: E402

HUB = SITE / "gonzalgo" / "data"


def build_indexes() -> list[dict]:
    print("indexes:")
    metas = [indexlib.build(mk_kernel_index.idx),
             indexlib.build(mk_dominator_table.idx),
             indexlib.build(mk_controlled_tactics.idx),
             indexlib.build(mk_spend_points.idx),
             indexlib.build(mk_substitution.idx),
             indexlib.build(mk_entry_points.idx),
             indexlib.build(mk_tactic_bands.idx),
             indexlib.build(mk_cleanable.idx),
             indexlib.build(mk_setmm_axioms.idx),
             indexlib.build(mk_site_diagnosis.idx),
             indexlib.build(mk_choice_strength.idx),
             indexlib.build(mk_version_delta.idx)]

    # generated-proofs keeps its own hand-written page; only its data comes
    # through indexlib, so build it the way that page expects and take the
    # metadata it recorded.
    out = SITE / "gonzalgo" / "generated-proofs" / "index.html"
    out.write_text(buildnote.build(), encoding="utf-8", newline="\n")
    meta = dict(buildnote.META)
    meta["note"] = "write-up with the summary table as data"
    print(f"  {meta['slug']}: {meta['rows']} rows, version {meta['version']}"
          f"{' (data changed)' if meta['changed'] else ' (unchanged)'}")
    metas.append(meta)
    return metas


# --------------------------------------------------------------------------
def build_hub(metas: list[dict]) -> None:
    url = f"{BASE}/gonzalgo/data/"
    catalog = json.dumps({
        "@context": "https://schema.org",
        "@type": "DataCatalog",
        "name": "gonzalgo indexes",
        "url": url,
        "description": (
            "Standing measurements of what formal mathematical libraries rest "
            "on, produced by gonzalgo and remeasured as the libraries move."),
        "identifier": SERIES_DOI,
        "license": LICENSE,
        "creator": {"@type": "Person", "name": "Vincent Gonzalez",
                    "identifier": ORCID},
        "publisher": {"@type": "Organization", "name": "F-Keys", "url": BASE},
        "dataset": [
            {"@type": "Dataset", "name": m["title"], "url": m["url"],
             "description": m["description"], "version": m["version"],
             "license": LICENSE,
             "distribution": [
                 {"@type": "DataDownload",
                  "encodingFormat": "application/json",
                  "contentUrl": f"{m['url']}{m['slug']}.json"},
                 {"@type": "DataDownload", "encodingFormat": "text/csv",
                  "contentUrl": f"{m['url']}{m['slug']}.csv"},
             ]}
            for m in metas
        ],
    }, indent=2, ensure_ascii=False)

    cards = []
    for m in metas:
        cards.append(f"""
<div class="card">
  <h2><a href="{m['url']}">{m['title']}</a></h2>
  <p>{m['description']}</p>
  <p class="meta">
    {m['rows']:,} rows &middot; version {m['version']} &middot;
    <a href="{m['url']}{m['slug']}.json">JSON</a> &middot;
    <a href="{m['url']}{m['slug']}.csv">CSV</a> &middot; CC-BY-4.0
  </p>
</div>""")

    extra = """
.card { border:1px solid var(--border); background:var(--panel); padding:1.2rem 1.3rem; margin:1.2rem 0; }
.card h2 { margin:0 0 .5rem; }
.card h2 a { text-decoration:none; }
.card p { margin-bottom:.6rem; }
.meta { color:var(--dim); font-size:.9rem; margin-bottom:0; }
"""
    check_fonts(CSS + extra, "hub stylesheet")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="index, follow, max-snippet:-1">
<link rel="canonical" href="{url}">
<title>gonzalgo indexes &mdash; standing measurements of what formal libraries rest on</title>
<meta name="description" content="Downloadable measurements of what formal mathematical libraries rest on: unfinished proofs, compiler-trusted reductions, axiom dependence, and which constants that dependence is responsible to. JSON and CSV, CC-BY-4.0.">
<meta name="llms-txt" content="{BASE}/llms.txt">
<meta name="ai" content="allow">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="gonzalgo indexes">
<meta property="og:description" content="Standing measurements of what formal libraries rest on. JSON and CSV, CC-BY-4.0.">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<script type="application/ld+json">
{catalog}
</script>
<style>{CSS}{extra}</style>
</head>
<body>
<nav>
  <a href="/" class="logo">F-KEYS</a>
  <div style="display:flex;gap:1.5rem;font-size:.9rem;">
    <a href="/gonzalgo/">gonzalgo</a>
    <a href="/gonzalgo/faq/">FAQ</a>
    <a href="https://github.com/zengineco/gonzalgo">GitHub</a>
  </div>
</nav>
<main>

<h1>GONZALGO INDEXES</h1>
<p class="kicker">measurements, kept current, in a form you can download</p>

<p>
What a formal library rests on is a fact about it that changes when the library
changes. These are the measurements taken so far, each with the table on the
page and the same table as JSON and CSV.
</p>
<p>
Every figure comes from the proof system's own bookkeeping &mdash; Lean's
<code>collectAxioms</code> and Metamath's proof structure &mdash; read by
<a href="/gonzalgo/">gonzalgo</a>, which proves nothing itself. Each index says
which version of which library it was taken from, and carries a version that
moves only when the numbers do.
</p>

{''.join(cards)}

<h2>Using them</h2>
<p>
CC-BY-4.0: use them, quote them, redistribute them, cite the DOI on the index
you used. If a number here disagrees with one you measured, that is worth an
<a href="https://github.com/zengineco/gonzalgo/issues">issue</a> &mdash; the
point of publishing the data is that someone can check it.
</p>

<footer>
  <p>
    Cite the series: Gonzalez, V. (2026). <em>The gonzalgo Indexes</em>. Zenodo.
    <a href="{SERIES_DOI}">10.5281/zenodo.21900625</a>
  </p>
  <p style="margin-top:.8rem;">
    Method and definitions: Gonzalez, V. (2026).
    <em>Where Formal Libraries Spend Their Axioms</em>. Zenodo.
    <a href="https://doi.org/10.5281/zenodo.21769846">10.5281/zenodo.21769846</a>
  </p>
  <p style="margin-top:.8rem;">
    Vince Gonzalez &middot;
    <a href="{ORCID}">ORCID 0009-0005-3640-014X</a> &middot;
    the home of <code>kernel &gt; sorry</code>
  </p>
  <p style="margin-top:1.5rem;">&copy; 2026 F-Keys</p>
</footer>
</main>
</body>
</html>
"""
    HUB.mkdir(parents=True, exist_ok=True)
    (HUB / "index.html").write_text(html, encoding="utf-8")
    print(f"hub: {len(metas)} indexes listed")


# --------------------------------------------------------------------------
def update_sitemap(metas: list[dict]) -> None:
    """Put every index page AND every data file in the sitemap.

    A .json or .csv that is live but unlisted is a download nobody finds."""
    path = SITE / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")

    wanted = [(f"{BASE}/gonzalgo/data/", "0.9", max(m["version"] for m in metas))]
    for m in metas:
        wanted.append((m["url"], "0.9", m["version"]))
        wanted.append((f"{m['url']}{m['slug']}.json", "0.7", m["version"]))
        wanted.append((f"{m['url']}{m['slug']}.csv", "0.7", m["version"]))

    for loc, prio, lastmod in wanted:
        entry = (f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod>"
                 f"<priority>{prio}</priority></url>")
        existing = re.search(
            r"[ \t]*<url><loc>" + re.escape(loc) + r"</loc>.*?</url>\n", xml)
        if existing:
            xml = xml.replace(existing.group(0), entry + "\n")
        else:
            xml = xml.replace("</urlset>", entry + "\n</urlset>")

    path.write_text(xml, encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", xml)
    assert len(locs) == len(set(locs)), "sitemap has duplicate <loc> entries"
    print(f"sitemap: {len(wanted)} index URLs present, {len(locs)} total")


if __name__ == "__main__":
    metas = build_indexes()
    build_hub(metas)
    update_sitemap(metas)
    print("\nsummary")
    for m in metas:
        print(f"  {m['url']}  {m['rows']:>6,} rows  v{m['version']}")
