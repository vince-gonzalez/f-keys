"""One builder for every gonzalgo index.

An index is a measurement we intend to keep publishing: a table a human reads,
the same table a machine can download, and enough provenance that citing it is
possible. Before this existed each index was its own script with the HTML
inlined, so a second one meant copy-paste and a third meant three copies
drifting apart.

Write a spec, call build(). Out comes index.html, <slug>.json, <slug>.csv and
the schema.org Dataset block that makes the thing findable as data.

Two things this file enforces, because both have gone wrong by hand:

  * The CSV goes through the csv module. A foundation like "ZFC set theory,
    classical first-order logic" contains a comma, and hand-joining silently
    shifts every column after it.
  * No font below MIN_PX anywhere in the generated CSS, clamp() minimums
    included. check_fonts() raises rather than writes.

Versions track the DATA, not the build. Rebuilding an unchanged index leaves
its version alone; the version only moves when the numbers do, which is what
someone citing a version has a right to assume.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]                      # the f-keys web root
GONZALGO = SITE / "gonzalgo"
VERSIONS = HERE / "versions.json"

BASE = "https://f-keys.com"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
ORCID = "https://orcid.org/0009-0005-3640-014X"

MIN_PX = 13.6   # 0.85rem. Anything under this has been complained about.


# --------------------------------------------------------------------------
# spec
# --------------------------------------------------------------------------
@dataclass
class Column:
    key: str
    label: str
    align: str = "left"      # left | right
    fmt: str = "{:,}"        # applied to ints and floats
    emph: bool = False       # bold + red when non-zero
    dim: bool = False        # muted colour, for long prose cells
    pct: bool = False        # render as "12.3%"


@dataclass
class Index:
    slug: str
    title: str                                   # the H1
    kicker: str                                  # the line under it
    meta_title: str
    meta_description: str
    lede: list[str]                              # paragraphs above the table
    columns: list[Column]
    rows: list[dict]
    description: str                             # dataset description, one sentence
    measured: dict                               # what was measured, verbatim
    provenance: str                              # the "last measured ..." line, HTML
    notes: str = ""                              # HTML directly under the table
    sections: list[tuple[str, list[str]]] = field(default_factory=list)
    reproduce: list[str] = field(default_factory=list)
    reproduce_note: str = ""
    keywords: list[str] = field(default_factory=list)
    based_on: str = "https://doi.org/10.5281/zenodo.21769846"
    citation: str = ""                           # HTML, the footer cite line
    row_limit: int | None = None                 # HTML shows this many; data has all
    row_limit_note: str = ""


# --------------------------------------------------------------------------
# versioning — the hash is over the data, so the version is too
# --------------------------------------------------------------------------
def data_fields(idx: Index) -> list[str]:
    """Every key present in the data, in the order the data presents them.

    The columns list controls the HTML table only. A field that is measured but
    not shown still belongs in the JSON and the CSV — dropping it there would
    silently shrink the artifact people actually download. Order follows the
    rows rather than the display, so re-arranging a table never moves a column
    under someone reading the CSV by position."""
    fields: list[str] = []
    for row in idx.rows:
        for k in row:
            if k not in fields:
                fields.append(k)
    for c in idx.columns:
        if c.key not in fields:
            fields.append(c.key)
    return fields


def _canonical(idx: Index) -> str:
    """Hash the data, not the presentation. Re-ordering a table or renaming a
    column heading must not look like a new measurement."""
    return json.dumps(idx.rows, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def resolve_version(idx: Index) -> tuple[str, str, bool]:
    """Return (version, sha256, changed). Unchanged data keeps its version."""
    digest = hashlib.sha256(_canonical(idx).encode("utf-8")).hexdigest()
    store = json.loads(VERSIONS.read_text(encoding="utf-8")) if VERSIONS.exists() else {}
    prev = store.get(idx.slug)
    today = date.today().isoformat()
    if prev and prev.get("sha256") == digest:
        return prev["version"], digest, False
    history = (prev or {}).get("history", [])
    if prev:
        history = [{"version": prev["version"], "sha256": prev["sha256"]}] + history
    store[idx.slug] = {"version": today, "sha256": digest, "history": history}
    VERSIONS.write_text(json.dumps(store, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    return today, digest, True


# --------------------------------------------------------------------------
# the font gate
# --------------------------------------------------------------------------
UNIT_PX = {"px": 1.0, "rem": 16.0, "em": 16.0, "pt": 4.0 / 3.0, "pc": 16.0}
KEYWORD_PX = {"xx-small": 9.0, "x-small": 10.0, "small": 13.0, "smaller": 13.0}


def _px(value: str) -> float | None:
    value = value.strip().lower()
    if value in KEYWORD_PX:
        return KEYWORD_PX[value]
    m = re.fullmatch(r"([\d.]+)(px|rem|em|pt|pc)", value)
    if m:
        return float(m.group(1)) * UNIT_PX[m.group(2)]
    return None


def check_fonts(css: str, where: str) -> None:
    """Raise if any declared font-size is under MIN_PX. clamp() counts by its
    first argument, which is the size a narrow screen actually gets."""
    bad = []
    for decl in re.findall(r"font-size\s*:\s*([^;}]+)", css):
        decl = decl.strip()
        clamp = re.match(r"clamp\(([^,]+),", decl)
        candidate = clamp.group(1) if clamp else decl
        px = _px(candidate)
        if px is not None and px < MIN_PX:
            bad.append((decl, px))
    if bad:
        lines = "\n".join(f"    font-size: {d}   ({px:.1f}px)" for d, px in bad)
        raise ValueError(
            f"{where}: font-size below the {MIN_PX}px floor:\n{lines}\n"
            "Cut words instead of shrinking type.")


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def _csv_value(v):
    """Booleans go out as true/false, matching the JSON, not Python's True/False."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return v


def _cell(row: dict, col: Column) -> str:
    v = row.get(col.key)
    if v is None or v == "":
        return "&mdash;"
    # bool before int: in Python a bool IS an int, so "{:,}".format(True)
    # gives "1" and an eligibility column silently becomes ones and zeroes.
    if isinstance(v, bool):
        return "yes" if v else "no"
    if col.pct and isinstance(v, (int, float)):
        return f"{v}%"
    if isinstance(v, (int, float)):
        text = col.fmt.format(v)
    else:
        text = str(v)
    if col.emph and v:
        return f"<strong>{text}</strong>"
    return text


def _table(idx: Index) -> str:
    head = "".join(
        f"<th{' style=\"text-align:right\"' if c.align == 'right' else ''}>{c.label}</th>"
        for c in idx.columns)
    shown = idx.rows[:idx.row_limit] if idx.row_limit else idx.rows
    body = []
    for row in shown:
        tds = []
        for c in idx.columns:
            cls = " class='num'" if c.align == "right" else (" class='found'" if c.dim else "")
            tds.append(f"<td{cls}>{_cell(row, c)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f"<thead><tr>{head}</tr></thead>\n<tbody>\n" + "\n".join(body) + "\n</tbody>"


CSS = """
:root { --bg:#0a0e0a; --panel:#111911; --border:#1f351f; --green:#39ff14; --text:#c3dcc3; --dim:#8fae8f; --cyan:#00ffcc; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--text); font-family:'Share Tech Mono',monospace; font-size:16px; line-height:1.65; }
body::before { content:''; position:fixed; inset:0; background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.07) 2px,rgba(0,0,0,0.07) 4px); pointer-events:none; z-index:9000; }
nav { position:fixed; top:0; left:0; right:0; z-index:10000; background:rgba(10,14,10,.95); border-bottom:1px solid var(--border); padding:0 2rem; height:60px; display:flex; align-items:center; justify-content:space-between; }
.logo { font-family:'VT323',monospace; font-weight:400; font-size:28px; color:var(--green); letter-spacing:4px; text-decoration:none; }
nav a { color:var(--dim); text-decoration:none; }
nav a:hover { color:var(--green); }
main { max-width:1080px; margin:0 auto; padding:7rem 1.2rem 4rem; }
h1 { font-family:'VT323',monospace; font-weight:400; font-size:clamp(38px,7vw,68px); color:var(--green); letter-spacing:4px; line-height:1; }
.kicker { font-family:'VT323',monospace; font-weight:400; font-size:clamp(20px,3vw,26px); color:var(--cyan); letter-spacing:2px; margin:.5rem 0 1.5rem; }
h2 { font-family:'VT323',monospace; font-weight:400; font-size:1.7rem; color:var(--green); margin:2.5rem 0 .8rem; letter-spacing:2px; }
p { margin-bottom:1rem; }
a { color:var(--green); }
.wrap { overflow-x:auto; border:1px solid var(--border); background:var(--panel); margin:1.5rem 0; }
table { width:100%; border-collapse:collapse; font-size:.9rem; min-width:820px; }
th { color:var(--green); text-align:left; padding:.7rem .6rem; border-bottom:1px solid var(--border); white-space:nowrap; }
td { padding:.55rem .6rem; border-bottom:1px solid #142414; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
td.found { color:var(--dim); }
tr:hover td { background:#0d120d; }
strong { color:#ff8080; }
.note { color:var(--dim); font-size:.9rem; }
.series { color:var(--dim); font-size:.9rem; border:1px solid var(--border); background:var(--panel); padding:.7rem .9rem; margin:1.2rem 0; }
pre { background:#0d120d; border:1px solid var(--border); padding:1rem; overflow-x:auto; font-size:.9rem; margin:1rem 0; }
code { color:var(--cyan); }
footer { border-top:1px solid var(--border); margin-top:3.5rem; padding:2rem 0; color:var(--dim); font-size:.9rem; }
"""


def emit_data(idx: Index) -> dict:
    """Write <slug>.json and <slug>.csv and return everything the page needs.

    Split out from build() so a hand-written page — a write-up whose prose is
    the point — can still ship the same data files and the same Dataset block
    without being forced through the table template."""
    version, digest, changed = resolve_version(idx)
    fields = data_fields(idx)
    out = GONZALGO / idx.slug
    out.mkdir(parents=True, exist_ok=True)
    url = f"{BASE}/gonzalgo/{idx.slug}/"

    payload = {
        "name": idx.title,
        "description": idx.description,
        "version": version,
        "sha256": digest,
        "url": url,
        "license": LICENSE,
        "producedBy": {
            "software": "gonzalgo",
            "url": "https://pypi.org/project/gonzalgo/",
            "paper": idx.based_on,
        },
        "measured": idx.measured,
        "fields": fields,
        "displayed": [{"key": c.key, "label": c.label} for c in idx.columns],
        "rows": idx.rows,
    }
    (out / f"{idx.slug}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with io.open(out / f"{idx.slug}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(fields)
        for r in idx.rows:
            w.writerow([_csv_value(r.get(c)) for c in fields])

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": idx.title,
        "description": idx.description,
        "url": url,
        "version": version,
        "license": LICENSE,
        "keywords": idx.keywords,
        "creator": {"@type": "Person", "name": "Vincent Gonzalez",
                    "identifier": ORCID},
        "publisher": {"@type": "Organization", "name": "F-Keys",
                      "url": BASE},
        "isBasedOn": idx.based_on,
        "isPartOf": {"@type": "DataCatalog", "name": "gonzalgo indexes",
                     "url": f"{BASE}/gonzalgo/data/"},
        "measurementTechnique": "gonzalgo",
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "application/json",
             "contentUrl": f"{url}{idx.slug}.json"},
            {"@type": "DataDownload", "encodingFormat": "text/csv",
             "contentUrl": f"{url}{idx.slug}.csv"},
        ],
    }, indent=2, ensure_ascii=False)

    return {"slug": idx.slug, "title": idx.title,
            "description": idx.description, "keywords": idx.keywords,
            "rows": len(idx.rows), "version": version, "sha256": digest,
            "changed": changed, "url": url, "jsonld": jsonld,
            "fields": fields, "payload": payload}


def build(idx: Index) -> dict:
    d = emit_data(idx)
    version, url, jsonld = d["version"], d["url"], d["jsonld"]
    out = GONZALGO / idx.slug

    check_fonts(CSS, f"{idx.slug} stylesheet")

    lede = "\n".join(f"<p>{p}</p>" for p in idx.lede)
    sections = []
    for heading, paras in idx.sections:
        body = "\n".join(f"<p>{p}</p>" for p in paras)
        sections.append(f"<h2>{heading}</h2>\n{body}")
    sections_html = "\n\n".join(sections)

    repro = ""
    if idx.reproduce:
        cmds = "\n".join(idx.reproduce)
        repro = (f"<h2>Reproduce it</h2>\n<pre>{cmds}</pre>\n"
                 + (f'<p class="note">{idx.reproduce_note}</p>\n' if idx.reproduce_note else ""))

    limit_note = ""
    if idx.row_limit and len(idx.rows) > idx.row_limit:
        limit_note = (f'<p class="note">Showing the first {idx.row_limit:,} of '
                      f'{len(idx.rows):,} rows. {idx.row_limit_note} '
                      f'The full set is in the JSON and the CSV.</p>')

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="index, follow, max-snippet:-1">
<link rel="canonical" href="{url}">
<title>{idx.meta_title}</title>
<meta name="description" content="{idx.meta_description}">
<meta name="llms-txt" content="{BASE}/llms.txt">
<meta name="ai" content="allow">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{idx.title}">
<meta property="og:description" content="{idx.kicker}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<script type="application/ld+json">
{jsonld}
</script>
<style>{CSS}</style>
</head>
<body>
<nav>
  <a href="/" class="logo">F-KEYS</a>
  <div style="display:flex;gap:1.5rem;font-size:.9rem;">
    <a href="/gonzalgo/">gonzalgo</a>
    <a href="/gonzalgo/data/">indexes</a>
    <a href="https://github.com/zengineco/gonzalgo">GitHub</a>
  </div>
</nav>
<main>

<h1>{idx.title.upper()}</h1>
<p class="kicker">{idx.kicker}</p>

{lede}
<p class="note">{idx.provenance}</p>

<div class="wrap">
<table>
{_table(idx)}
</table>
</div>
{limit_note}
{f'<p class="note">{idx.notes}</p>' if idx.notes else ''}

<h2>Get the data</h2>
<p>
<a href="{idx.slug}.json">{idx.slug}.json</a> &middot;
<a href="{idx.slug}.csv">{idx.slug}.csv</a> &middot; CC-BY-4.0 &middot;
version {version}
</p>
<p class="series">
One of the <a href="/gonzalgo/data/">gonzalgo indexes</a> &mdash; standing
measurements of what formal libraries rest on, remeasured as the libraries move.
</p>

{repro}
{sections_html}

<footer>
  <p>{idx.citation}</p>
  <p style="margin-top:.8rem;">
    Maintained at <a href="{url}">{url.replace('https://', '')}</a>
    &mdash; the home of <code>kernel &gt; sorry</code>.
  </p>
  <p style="margin-top:1.5rem;">&copy; 2026 F-Keys</p>
</footer>
</main>
</body>
</html>
"""
    (out / "index.html").write_text(html_doc, encoding="utf-8")

    print(f"  {idx.slug}: {len(idx.rows):,} rows, version {version}"
          f"{' (data changed)' if d['changed'] else ' (unchanged)'}")
    return d
