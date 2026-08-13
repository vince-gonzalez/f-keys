"""Publish the Kernel Trust Profile specification, schema and profiles.

    python gonzalgo/_build/mk_kernel_trust.py

This is not an index. An index is a measurement; this is a format other projects
are meant to emit, so it needs a stable home, a fetchable schema, and worked
examples rather than a table with a download link.

Source of truth stays in universal-cover/ktp — SPEC.md, the JSON Schema, and the
fourteen profiles built from the Kernel Index. This copies them onto the domain
and renders the specification as a page.

The profiles are published with their `null` fields untouched. Rule R2 says
absence is not zero and `null` means not measured; four fields are null across
all fourteen because those measurements were never taken. Filling them in with
numbers from a different measurement is exactly what R1 forbids.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from indexlib import BASE, CSS, LICENSE, ORCID, SERIES_DOI, check_fonts

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]
KTP = Path(r"C:\Users\Admin\OneDrive\Desktop\universal-cover\ktp")
OUT = SITE / "gonzalgo" / "kernel-trust"


def md(text: str) -> str:
    """Enough Markdown for this document. Deliberately small: a renderer that
    silently mangles a spec is worse than one that only handles what is here."""
    out, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(html.escape(lines[i]))
                i += 1
            out.append("<pre>" + "\n".join(block) + "</pre>")
        elif ln.startswith("### "):
            out.append(f"<h3>{inline(ln[4:])}</h3>")
        elif ln.startswith("## "):
            out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("# "):
            i += 1
            continue                       # the page supplies its own H1
        elif ln.strip() == "---":
            out.append("<hr>")
        elif ln.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif ln.strip():
            para = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(
                    ("#", "-", "```", "---")):
                para.append(lines[i])
                i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
            continue
        i += 1
    return "\n".join(out)


def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"(?<![\">=])(https?://[^\s,<)]+)", r'<a href="\1">\1</a>', s)
    return s


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "profiles").mkdir(exist_ok=True)

    spec = (KTP / "SPEC.md").read_text(encoding="utf-8")
    shutil.copy2(KTP / "SPEC.md", OUT / "SPEC.md")
    schema_src = next((KTP / "schema").glob("*.json"))
    shutil.copy2(schema_src, OUT / schema_src.name)

    profiles = []
    for p in sorted((KTP / "profiles").glob("*.json")):
        shutil.copy2(p, OUT / "profiles" / p.name)
        d = json.loads(p.read_text(encoding="utf-8"))
        nulls = sum(1 for v in (
            d["subject"]["system_version"], d["subject"]["revision"],
            d["subject"]["url"], d["counts"]["declarations"],
            d["compiler_trusted"]["theorems_reaching"]) if v is None)
        profiles.append({
            "file": p.name,
            "name": d["subject"]["name"],
            "system": d["subject"]["system"],
            "foundation": d["subject"]["foundation"],
            "theorems": d["counts"]["theorems"],
            "unfinished": d["unfinished"]["theorems_reaching"],
            "compiler_trusted": d["compiler_trusted"]["theorems_reaching"],
            "assumptions": len(d["assumptions"]),
            "unmeasured_fields": nulls,
        })

    rows = "\n".join(
        f"<tr><td><a href=\"profiles/{p['file']}\">{p['name']}</a></td>"
        f"<td>{p['system']}</td><td class='found'>{p['foundation']}</td>"
        f"<td class='num'>{p['theorems']:,}</td>"
        f"<td class='num'>{p['unfinished']}</td>"
        f"<td class='num'>"
        f"{'&mdash;' if p['compiler_trusted'] is None else p['compiler_trusted']}</td>"
        f"<td class='num'>{p['assumptions']}</td>"
        f"<td class='num'>{p['unmeasured_fields']}</td></tr>"
        for p in profiles)

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "name": "Kernel Trust Profile",
        "headline": "Kernel Trust Profile 0.1 — a machine-readable declaration "
                    "of what a body of machine-checked mathematics rests on",
        "description": (
            "A specification for declaring what a formal library's theorems "
            "actually rest on: unfinished proofs, compiler-trusted results, and "
            "each axiom reached, with statement and proof dependencies kept "
            "apart. CITATION.cff standardises citation and SPDX standardises "
            "licence; this does the same for trust assumptions."),
        "url": f"{BASE}/gonzalgo/kernel-trust/",
        "version": "0.1",
        "license": LICENSE,
        "author": {"@type": "Person", "name": "Vincent Gonzalez",
                   "identifier": ORCID},
        "isBasedOn": "https://doi.org/10.5281/zenodo.21769846",
        "citation": SERIES_DOI,
        "keywords": ["formal verification", "Lean 4", "Metamath",
                     "trusted computing base", "specification", "provenance",
                     "reproducibility", "CITATION.cff", "SPDX"],
    }, indent=2)

    extra = """
table { width:100%; border-collapse:collapse; font-size:.9rem; min-width:760px; }
hr { border:0; border-top:1px solid var(--border); margin:2rem 0; }
h3 { font-family:'VT323',monospace; font-weight:400; font-size:1.35rem; color:var(--cyan); letter-spacing:1px; margin:1.6rem 0 .6rem; }
"""
    check_fonts(CSS + extra, "kernel-trust stylesheet")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="index, follow, max-snippet:-1">
<link rel="canonical" href="{BASE}/gonzalgo/kernel-trust/">
<title>Kernel Trust Profile &mdash; a standard way to say what a proof rests on</title>
<meta name="description" content="A machine-readable declaration of what a body of machine-checked mathematics rests on. CITATION.cff standardises citation, SPDX standardises licence; there is no standard way to say what a library rests on. This is that, with a JSON Schema and fourteen worked profiles.">
<meta name="llms-txt" content="{BASE}/llms.txt">
<meta name="ai" content="allow">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/gonzalgo/kernel-trust/">
<meta property="og:title" content="Kernel Trust Profile 0.1">
<meta property="og:description" content="There is no standard way to say what a formal library rests on. This is one.">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<script type="application/ld+json">
{jsonld}
</script>
<style>{CSS}{extra}</style>
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

<h1>KERNEL TRUST PROFILE</h1>
<p class="kicker">a standard way to say what a proof rests on &middot; version 0.1, draft</p>

<p class="series">
<a href="SPEC.md">SPEC.md</a> &middot;
<a href="{schema_src.name}">JSON Schema</a> &middot;
{len(profiles)} worked profiles below &middot; CC-BY-4.0
</p>

{md(spec)}

<h2>Profiles</h2>
<p>
Fourteen libraries, emitted by <code>gonzalgo profile</code> from the Kernel
Index. These exist to test the specification against data gathered before the
specification was written &mdash; a format that only fits the numbers you happen
to have is not a standard.
</p>
<div class="wrap">
<table>
<thead><tr>
  <th>library</th><th>system</th><th>foundation</th>
  <th style="text-align:right">theorems</th>
  <th style="text-align:right">unfinished</th>
  <th style="text-align:right">compiler-trusted</th>
  <th style="text-align:right">assumptions</th>
  <th style="text-align:right">unmeasured</th>
</tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
<p class="note">
The <em>unmeasured</em> column is the specification working. Rule R2 says absence
is not zero and <code>null</code> means not measured, so four fields sit null
across every profile &mdash; system version, revision, url, and the declaration
count &mdash; because those measurements were never taken. Filling them from a
different measurement is what R1 forbids.
</p>

<footer>
  <p>
    Method and definitions: Gonzalez, V. (2026).
    <em>Where Formal Libraries Spend Their Axioms</em>. Zenodo.
    <a href="https://doi.org/10.5281/zenodo.21769846">10.5281/zenodo.21769846</a>
  </p>
  <p style="margin-top:.8rem;">
    Vince Gonzalez &middot;
    <a href="{ORCID}">ORCID 0009-0005-3640-014X</a> &middot;
    specification CC-BY-4.0, implementations unencumbered
  </p>
  <p style="margin-top:1.5rem;">&copy; 2026 F-Keys</p>
</footer>
</main>
</body>
</html>
"""
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"  wrote {OUT / 'index.html'}")
    print(f"  spec {len(spec):,} chars, schema {schema_src.name}, "
          f"{len(profiles)} profiles")
    print(f"  fields left null across all profiles: "
          f"{sorted({p['unmeasured_fields'] for p in profiles})}")


if __name__ == "__main__":
    main()
