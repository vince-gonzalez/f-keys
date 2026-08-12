"""The Spend-Point Table — where the axiom is spent, not where it is inherited.

    python gonzalgo/_build/extract_spend_points.py
    python gonzalgo/_build/mk_spend_points.py
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "spend-point-rows.json").read_text(encoding="utf-8"))

INHERIT = [r for r in rows if not r["spends_directly"]]

idx = Index(
    slug="spend-points",
    title="The Spend-Point Table",
    kicker="where choice is spent, and where it is only inherited",
    meta_title="The Spend-Point Table — where Mathlib actually spends the axiom of choice",
    meta_description=(
        "The 20 largest sites of classical dependence in Mathlib, showing which "
        "contain a direct use of a choice primitive and which only inherit one. "
        "15 of the 20 spend nothing: they dominate 25,992 theorems between them "
        "with every primitive use sitting above them in the graph."),
    description=(
        "The 20 largest sites of classical dependence in Mathlib, each with the "
        "number of declarations in its dominator subtree that cite a choice "
        "primitive directly. Separates sites where the axiom is spent from sites "
        "that dominate theorems while inheriting the axiom from further up."),
    lede=[
        "Dominance says which site a theorem's classical dependence is responsible "
        "to. It does not say where the axiom is actually spent, and the two come "
        "apart hard.",
        f"{len(INHERIT)} of these 20 sites contain no direct use of a choice "
        f"primitive anywhere in their subtree. Between them they dominate "
        f"{sum(r['theorems_dominated'] for r in INHERIT):,} theorems while spending "
        "nothing — every primitive use is above them in the graph. Rebuilding such "
        "a site does not remove a use of choice; it removes a route to one.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 &middot; dominator subtrees over 766,564 constants, '
        'primitives counted where cited directly'),
    columns=[
        Column("rank", "#", align="right"),
        Column("site", "site"),
        Column("theorems_dominated", "theorems dominated", align="right"),
        Column("subtree_constants", "subtree", align="right"),
        Column("spenders", "spenders", align="right"),
        Column("primitives", "primitives cited", dim=True),
    ],
    rows=rows,
    measured={
        "Lean 4": "4.32.1 with Mathlib v4.32.1",
        "axiom": "Classical.choice, via its primitives",
    },
    notes=(
        "<em>subtree</em> is the constants under the site in the dominator tree. "
        "<em>spenders</em> is how many of them cite a choice primitive "
        "(<code>Classical.propDecidable</code>, <code>byContradiction</code>, "
        "<code>indefiniteDescription</code>, <code>em</code>) directly rather than "
        "through another constant. Zero means the site inherits the axiom "
        "entirely."),
    sections=[
        ("The two that carry almost everything", [
            "<code>Classical.propDecidable</code> has 6,775 spenders in its subtree "
            "and <code>Classical.byContradiction</code> 1,854. Between them they "
            "account for nearly all direct spending in the library, and "
            "propDecidable's own subtree spends byContradiction 5,338 times against "
            "its own 1,540 — the decidability fallback reaches the axiom mostly "
            "through excluded middle rather than directly.",
            "Everything below them in this table is structural. A functor category "
            "instance dominates 5,271 theorems and spends nothing. Hash-map "
            "well-formedness dominates 4,899 and spends nothing. These are places "
            "classical dependence passes through, not places it originates.",
        ]),
        ("Why the distinction changes what you would do", [
            "A repair aimed at a spend point removes a use of the axiom. A repair "
            "aimed at a pure dominator reroutes a large number of theorems without "
            "removing anything, and only helps if the route it removes was the only "
            "one. Both are visible as large numbers in a dominance ranking and they "
            "are not the same kind of target.",
            "<code>String.toList</code> is the sharpest case here: 1,111 theorems "
            "dominated, a subtree of 4,557 constants, and no spender in any of them.",
        ]),
    ],
    reproduce=[
        "lake env lean -D maxErrors=4000 lean/Dump.lean",
        "python analysis/spendpoints.py",
    ],
    reproduce_note=(
        "Code and derived data: "
        "<a href=\"https://doi.org/10.5281/zenodo.21883963\">"
        "10.5281/zenodo.21883963</a>."),
    keywords=["formal verification", "Lean 4", "Mathlib", "axiom of choice",
              "dominator tree", "Classical.propDecidable", "excluded middle",
              "proof assistant", "provenance"],
    invariants=[
        ("ranks are 1..N with no gaps",
         lambda rs: [r["rank"] for r in rs] == list(range(1, len(rs) + 1))),
        ("rank order matches the dominated count, descending",
         lambda rs: all(rs[i]["theorems_dominated"] >= rs[i + 1]["theorems_dominated"]
                        for i in range(len(rs) - 1))),
        ("a subtree is never smaller than what the site dominates",
         lambda rs: all(r["subtree_constants"] >= r["theorems_dominated"]
                        for r in rs)),
        ("spends_directly agrees with the primitives column on every row",
         lambda rs: all(r["spends_directly"] == (r["primitives"] != "(none — inherits)")
                        for r in rs)),
        ("a site with no spenders cites no primitive, and vice versa",
         lambda rs: all((r["spenders"] > 0) == r["spends_directly"] for r in rs)),
        # The two figures the lede states.
        ("15 of the 20 sites inherit only, dominating 25,992 theorems",
         lambda rs: sum(1 for r in rs if not r["spends_directly"]) == 15
         and sum(r["theorems_dominated"] for r in rs
                 if not r["spends_directly"]) == 25992),
        ("propDecidable and byContradiction carry 6,775 and 1,854 spenders",
         lambda rs: [next(r["spenders"] for r in rs if r["site"] == n)
                     for n in ("Classical.propDecidable",
                               "Classical.byContradiction")] == [6775, 1854]),
    ],
    based_on="https://doi.org/10.5281/zenodo.21883963",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Which Constant Is Responsible? Dominator '
        'Analysis of Classical Dependence in Mathlib</em>. Zenodo. '
        '<a href="https://doi.org/10.5281/zenodo.21883963">10.5281/zenodo.21883963</a>'),
)

if __name__ == "__main__":
    build(idx)
