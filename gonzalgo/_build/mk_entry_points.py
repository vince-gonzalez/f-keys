"""The Entry-Point Table — how often a database touches its own axioms.

    python gonzalgo/_build/mk_entry_points.py

Rows come from data/kernel-index-rows.json — the columns the Kernel Index
measures but does not render.

The obvious table to build from this data is an amplification ranking, and it
would be wrong. §3.1 of the axiom-spend paper proves amplification is a property
of how a library was factored rather than of its mathematics: inlining sends it
to 1, a single gateway lemma sends it to |D(a)|, and neither changes any
theorem's statement or axiom closure. Entry points per theorem is the quantity
the paper names as comparable across databases, so that is what this ranks.
Amplification is carried as reported, labelled for what it is.
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
source = json.loads((HERE / "data" / "kernel-index-rows.json").read_text(encoding="utf-8"))

rows = []
for r in source:
    if r.get("entries_per_theorem") is None:
        continue
    rows.append({
        "database": r["library"],
        "foundation": r["foundation"],
        "theorems": r["theorems"],
        "axioms_used": r["axioms_used"],
        "entry_points": r["entry_points"],
        "entries_per_theorem": r["entries_per_theorem"],
        "amplification_as_reported": r["amplification"],
    })
rows.sort(key=lambda r: r["entries_per_theorem"])

BIG = [r for r in rows if r["theorems"] > 5000]

idx = Index(
    slug="entry-points",
    title="The Entry-Point Table",
    kicker="how often a library reaches for its own axioms",
    meta_title="The Entry-Point Table — axiom entry points across five Metamath foundations",
    meta_description=(
        "Five Metamath databases across ZFC, intuitionistic logic, New Foundations, "
        "quantum logic and higher-order logic: axioms used, entry points, and entry "
        "points per theorem — the one quantity here that survives refactoring and "
        "can be compared across libraries."),
    description=(
        "Axioms used, direct entry points into them, and entry points per theorem, "
        "for five Metamath databases spanning five foundations. Entry points per "
        "theorem normalises for library size and is the measure that can be compared "
        "across databases; amplification is carried as reported but is a property of "
        "factorization rather than of mathematics."),
    lede=[
        "An axiom is cited directly by a few theorems and inherited by many. The "
        "count of direct citations is the entry points, and dividing by the library's "
        "size gives a figure that means the same thing in a database of 47,000 "
        "theorems and one of 151.",
        "The three large databases land close together — "
        + ", ".join(f"{r['entries_per_theorem']:.4f} ({r['database']})" for r in BIG)
        + " — across ZFC, intuitionistic logic and New Foundations. Three "
        "communities with different foundations and no shared plan reach for their "
        "axioms at nearly the same rate. The two small databases sit far above, "
        "which is what a library looks like before its results are mostly built on "
        "earlier results.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Metamath '
        '<code>set.mm</code>, <code>iset.mm</code>, <code>nf.mm</code>, '
        '<code>ql.mm</code>, <code>hol.mm</code> &middot; each database\'s own '
        'axiom declarations and proof structure'),
    columns=[
        Column("database", "database"),
        Column("foundation", "foundation", dim=True),
        Column("theorems", "theorems", align="right"),
        Column("axioms_used", "axioms used", align="right"),
        Column("entry_points", "entry points", align="right"),
        Column("entries_per_theorem", "entries / theorem", align="right",
               fmt="{:.4f}"),
        Column("amplification_as_reported", "amplification", align="right",
               fmt="{:.1f}"),
    ],
    rows=rows,
    measured={"Metamath": "set.mm, iset.mm, nf.mm, ql.mm, hol.mm"},
    notes=(
        "<em>entry points</em> counts theorems citing an axiom directly, as opposed "
        "to inheriting it through another theorem. <em>entries / theorem</em> is "
        "that over the theorem count and is the column to compare across rows. "
        "<em>amplification</em> is dependents over entry points, reproduced from the "
        "published table; the next section is why it is not a column to rank on."),
    sections=[
        ("What amplification cannot mean", [
            "Amplification is dependents divided by entry points, and it looks like "
            "a measure of how much a foundation yields. It is not. Consider two "
            "refactorings that preserve every theorem's statement and every "
            "theorem's transitive axiom closure. Inline every citation of a lemma "
            "and each dependent now cites the axiom directly, so entry points equal "
            "dependents and amplification falls to 1. Introduce a single gateway "
            "lemma stating the axiom and reroute every citation through it, and "
            "entry points fall to one, sending amplification to the full dependent "
            "count.",
            "So amplification ranges over the whole interval between those two "
            "extremes without a single theorem changing. The figures 292&times;, "
            "221&times;, 94&times; here, and 2,256&times; for "
            "<code>Classical.choice</code> in Mathlib, describe how four communities "
            "chose to organise proofs. That they land in a similar range is a real "
            "observation about engineering practice and not one about ZFC.",
            "This is why the column is present and the table is not sorted on it.",
        ]),
        ("The extreme case", [
            "In <code>set.mm</code>, <code>ax-4</code> is cited directly in one "
            "proof and inherited by 44,501 theorems — a single proof step carrying "
            "an axiom into 93% of the library. Most axioms there are cited directly "
            "in three proofs or fewer. Concentration like that is what makes "
            "provenance worth computing at all: the theorems that depend on an "
            "axiom and the theorems that use it are almost disjoint sets.",
        ]),
        ("Why no Lean rows", [
            "Lean's axioms are fixed by the system rather than declared per library, "
            "so the nine Lean libraries in the "
            "<a href=\"/gonzalgo/kernel-index/\">Kernel Index</a> share one axiom set "
            "and the comparison would be against a constant. The single Mathlib "
            "figure quoted above is stated in the paper, not derived here.",
        ]),
    ],
    reproduce=["pip install gonzalgo",
               "gonzalgo mm set.mm iset.mm nf.mm ql.mm hol.mm"],
    reproduce_note=(
        "The same command produces the Metamath rows of the "
        "<a href=\"/gonzalgo/kernel-index/\">Kernel Index</a>; these are its "
        "remaining columns."),
    keywords=["Metamath", "set.mm", "iset.mm", "New Foundations", "quantum logic",
              "higher-order logic", "intuitionistic logic", "axioms",
              "formal verification", "foundations of mathematics"],
    invariants=[
        ("every row has all five measured columns",
         lambda rs: all(r[k] is not None for r in rs for k in (
             "theorems", "axioms_used", "entry_points",
             "entries_per_theorem", "amplification_as_reported"))),
        ("rows are ordered by entries per theorem, not by amplification",
         lambda rs: all(rs[i]["entries_per_theorem"] <= rs[i + 1]["entries_per_theorem"]
                        for i in range(len(rs) - 1))),
        ("entries per theorem recomputes from its own two columns",
         lambda rs: all(abs(round(r["entry_points"] / r["theorems"], 4)
                            - r["entries_per_theorem"]) <= 0.0001 for r in rs)),
        ("entry points never exceed the theorem count in the large databases",
         lambda rs: all(r["entry_points"] <= r["theorems"] for r in rs
                        if r["theorems"] > 5000)),
        ("all five Metamath databases are present and no Lean library is",
         lambda rs: sorted(r["database"] for r in rs)
         == ["hol.mm", "iset.mm", "nf.mm", "ql.mm", "set.mm"]),
        # The lede's claim, checked against the rows underneath it.
        ("the three large databases agree on entries/theorem within 14%",
         lambda rs: (lambda v: max(v) / min(v) <= 1.14)(
             [r["entries_per_theorem"] for r in rs if r["theorems"] > 5000])),
        ("the amplification figures still match the published table",
         lambda rs: {r["database"]: r["amplification_as_reported"] for r in rs}
         == {"set.mm": 292.1, "iset.mm": 220.5, "nf.mm": 93.5,
             "ql.mm": 6.3, "hol.mm": 16.7}),
    ],
    based_on="https://doi.org/10.5281/zenodo.21769846",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
