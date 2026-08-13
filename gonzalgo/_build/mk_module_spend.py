"""The Module Spend Table — which files spend choice, and on which primitive.

    python gonzalgo/_build/extract_module_spend.py
    python gonzalgo/_build/mk_module_spend.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "module-spend-rows.json").read_text(encoding="utf-8"))

TOTAL_MODULES = 10599
SPENDS = sum(r["spends"] for r in rows)
BY_PRIM = {k: sum(r[k] for r in rows) for k in
           ("choice", "propDecidable", "byContradiction", "em",
            "indefiniteDescription", "byCases")}
BY_LIB = collections.Counter(r["library"] for r in rows)

idx = Index(
    slug="module-spend",
    title="The Module Spend Table",
    kicker="which files spend the axiom, and on which primitive",
    meta_title="The Module Spend Table — where Mathlib spends the axiom of choice, by file",
    meta_description=(
        "3,261 of Mathlib's 10,599 modules contain a declaration whose proof names "
        "a choice primitive directly. 18,109 declarations spend, and only 209 of "
        "them cite Classical.choice itself — the rest arrive through "
        "byContradiction and propDecidable."),
    description=(
        "Modules containing at least one declaration whose own proof term names a "
        "choice primitive directly, with the count broken down by primitive. "
        "Spending, as opposed to reach: a module with no direct spend can still be "
        "full of theorems that depend on choice through what they import."),
    lede=[
        f"A library-wide figure names no file. {SPENDS:,} declarations across "
        f"{len(rows):,} of Mathlib's {TOTAL_MODULES:,} modules name a choice "
        "primitive in their own proof, and this is where they are.",
        f"Only {BY_PRIM['choice']} of those cite <code>Classical.choice</code> "
        f"itself. {BY_PRIM['byContradiction']:,} go through "
        f"<code>Classical.byContradiction</code> and {BY_PRIM['propDecidable']:,} "
        "through <code>Classical.propDecidable</code> — excluded middle and the "
        "decidability fallback. A repair aimed at one does nothing for the others, "
        "which is why they are counted apart.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.33.0 with '
        'Mathlib v4.33.0 &middot; one streamed pass over 795,218 declarations, no '
        'closure computed'),
    columns=[
        Column("module", "module"),
        Column("library", "library", dim=True),
        Column("declarations", "declarations", align="right"),
        Column("spends", "spends", align="right", emph=True),
        Column("spend_rate_pct", "rate", align="right", pct=True),
        Column("byContradiction", "byContradiction", align="right"),
        Column("propDecidable", "propDecidable", align="right"),
        Column("choice", "choice", align="right"),
    ],
    rows=rows,
    row_limit=120,
    row_limit_note="Ordered by spends. The tail is long: most spending modules do "
                   "it once or twice.",
    measured={
        "Lean 4": "4.33.0 with Mathlib v4.33.0",
        "modules measured": TOTAL_MODULES,
        "unit": "direct citation in a proof term, not reach",
    },
    notes=(
        "<em>spends</em> counts declarations in the module whose own proof names a "
        "primitive; a declaration naming two is counted once here and once under "
        "each primitive, so the primitive columns can exceed it. <em>rate</em> is "
        "spends over declarations in that module. Modules with no direct spend are "
        "omitted &mdash; there are "
        f"{TOTAL_MODULES - len(rows):,} of them, and their theorems can still "
        "depend on choice through imports."),
    sections=[
        ("Spending is not reach", [
            "This table answers where the axiom is <em>used</em>. It does not say "
            "how far each use travels, and the two are wildly different: 324,808 "
            "theorems depend on choice while "
            f"{SPENDS:,} declarations spend it. One spend in "
            "<code>Mathlib.Logic.Basic</code> can be inherited by a hundred "
            "thousand theorems, and one in a leaf file by none.",
            "The <a href=\"/gonzalgo/dominator-table/\">Dominator Table</a> is the "
            "other half — how many theorems each site is responsible for. Read "
            "together they say which file to open and whether opening it is worth "
            "anything.",
        ]),
        ("What the primitives mean", [
            "<code>Classical.byContradiction</code> is excluded middle: proving P "
            "by refuting its negation. <code>Classical.propDecidable</code> is the "
            "decidability fallback, supplied where an instance was wanted and none "
            "was synthesised. <code>Classical.choice</code> proper is choosing from "
            "a family, and is the rarest of the three by two orders of magnitude.",
            "That ordering matters for anyone trying to reduce classical "
            "dependence. The common cases are not choice in the mathematician's "
            "sense at all — they are a proof style and a missing instance.",
        ]),
        ("Where it concentrates", [
            "The heaviest single module is "
            f"<code>{rows[0]['module']}</code> at {rows[0]['spends']} spends across "
            f"{rows[0]['declarations']} declarations. By library the split is "
            + ", ".join(f"{k} {v:,}" for k, v in BY_LIB.most_common()) + " modules "
            "containing at least one spend.",
        ]),
    ],
    reproduce=[
        "lake env lean -D maxErrors=4000 Split.lean",
        "python extract_module_spend.py",
    ],
    reproduce_note=(
        "One pass, about seven seconds over a 640 MB dump. The module column comes "
        "from the extractor; a dump without it cannot answer this question at all. "
        "Method: <a href=\"https://doi.org/10.5281/zenodo.21769846\">"
        "10.5281/zenodo.21769846</a>."),
    keywords=["Lean 4", "Mathlib", "axiom of choice", "Classical.propDecidable",
              "excluded middle", "module", "formal verification", "provenance",
              "constructive mathematics"],
    invariants=[
        ("every listed module actually spends",
         lambda rs: all(r["spends"] > 0 for r in rs)),
        ("spends never exceed declarations",
         lambda rs: all(r["spends"] <= r["declarations"] for r in rs)),
        ("the rate recomputes from its own two columns",
         lambda rs: all(abs(round(100 * r["spends"] / r["declarations"], 1)
                            - r["spend_rate_pct"]) <= 0.05 for r in rs)),
        ("the primitive columns are at least the spend count, never less",
         lambda rs: all(r["byContradiction"] + r["propDecidable"] + r["choice"]
                        + r["em"] + r["indefiniteDescription"] + r["byCases"]
                        >= r["spends"] for r in rs)),
        ("the library is the first component of the module path",
         lambda rs: all(r["module"].split(".")[0] == r["library"] for r in rs)),
        ("18,109 declarations spend across 3,261 modules",
         lambda rs: sum(r["spends"] for r in rs) == 18109 and len(rs) == 3261),
        ("byContradiction and propDecidable dominate, choice proper is rare",
         lambda rs: sum(r["choice"] for r in rs) == 209
         and sum(r["byContradiction"] for r in rs) == 9442
         and sum(r["propDecidable"] for r in rs) == 8440),
    ],
    based_on="https://doi.org/10.5281/zenodo.21769846",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
