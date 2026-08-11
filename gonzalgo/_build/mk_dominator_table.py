"""The Dominator Table — which constants Mathlib's classical dependence rests on.

    python gonzalgo/_build/extract_dominator_rows.py
    python gonzalgo/_build/mk_dominator_table.py
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "dominator-table-rows.json").read_text(encoding="utf-8"))

idx = Index(
    slug="dominator-table",
    title="The Dominator Table",
    kicker="which constants Mathlib's use of choice actually rests on",
    meta_title="The Dominator Table — which constants Mathlib's classical dependence rests on",
    meta_description=(
        "3,000 Mathlib constants ranked by how many theorems would stop depending "
        "on the axiom of choice if that one constant were rebuilt. Dominance, not "
        "reachability: the two answers differ by 58x on the first case examined."),
    description=(
        "Mathlib constants ranked by how many theorems each is uniquely responsible "
        "for making classical — the number that would stop depending on the axiom of "
        "choice if that constant alone were rebuilt. Computed as a dominator tree "
        "over the reversed dependency graph rooted at the axiom."),
    lede=[
        "Asking which constant a theorem's classical dependence is <em>responsible</em> "
        "for is not the same as asking which constants its proof touches, and the "
        "answers are far apart. 116,766 theorems reach the order lemma "
        "<code>lt_or_eq_of_le</code>; 2,018 would stop being classical if it were "
        "rebuilt. Reachability overstates responsibility by 58x in that one case.",
        "The column below is the second number. A constant's count is the theorems "
        "whose every route to <code>Classical.choice</code> passes through it, so "
        "repairing it repairs exactly them and nothing else.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 &middot; 790,171 declarations, 30,015,601 dependency edges, '
        'one dominator tree over all 766,564 constants'),
    columns=[
        Column("rank", "#", align="right"),
        Column("constant", "constant"),
        Column("kind", "kind", dim=True),
        Column("area", "area", dim=True),
        Column("theorems_dominated", "theorems dominated", align="right"),
        Column("eligible", "eligible"),
    ],
    rows=rows,
    measured={
        "Lean 4": "4.32.1 with Mathlib v4.32.1",
        "graph": "790,171 declarations, 30,015,601 edges",
        "axiom": "Classical.choice",
    },
    row_limit=100,
    row_limit_note=(
        "The tail is long and flat &mdash; rank 3,000 dominates 10 theorems."),
    notes=(
        "<em>theorems dominated</em> counts theorems for which this constant is the "
        "sole route to the axiom. <em>eligible</em> is false when the constant's own "
        "type is classical, so no constructive replacement for it can exist; it is "
        "false for only 2 of the 1,500 constants where it was computed, which is the "
        "negative result in the eligibility note &mdash; the test does not "
        "discriminate among load-bearing constants. <em>area</em> and "
        "<em>eligible</em> were computed for the top 1,500 only; below that they are "
        "blank rather than guessed."),
    reproduce=[
        "# regenerate the declaration graph (~3 min, ~600 MB)",
        "lake env lean -D maxErrors=4000 lean/Dump.lean",
        "python analysis/dominators.py",
    ],
    reproduce_note=(
        "<code>ConstantInfo.value?</code> must be passed "
        "<code>allowOpaque := true</code> or theorem proofs read as empty and every "
        "statement-versus-proof figure is wrong rather than imprecise. Code and "
        "derived data: <a href=\"https://doi.org/10.5281/zenodo.21883963\">"
        "10.5281/zenodo.21883963</a>."),
    sections=[
        ("Two results worth reading off it", [
            "60.1% of classically dependent theorems have no responsible constant at "
            "all. Their immediate dominator is the axiom itself, so no local repair "
            "anywhere in the library reaches them. That is the ceiling on what this "
            "kind of work can do, and it was not previously known.",
            "Outside classical logic proper, the largest sites are infrastructure "
            "rather than mathematics: a functor category instance at 5,271, hash-map "
            "well-formedness at 4,899, the powerset Boolean algebra at 3,430, string "
            "conversion at 1,111. The places where choice is load-bearing are not the "
            "places anyone would have pointed at.",
        ]),
        ("A disagreement in the source data", [
            "The reproduction archive carries two files with a count per constant, "
            "and they disagree on 137 of the 1,500 they share &mdash; hash-map "
            "well-formedness is 4,899 in one and 4,892 in the other. The published "
            "note reports 4,899, so that file is used here for every count and the "
            "other only for the categorical columns. Where they differ, the row "
            "carries a <code>count_in_eligibility_file</code> field so the "
            "disagreement is visible in the data rather than resolved out of sight.",
        ]),
        ("What is not here yet", [
            "A reach column. The 58x figure above is one measured pair; computing "
            "reach for every row means a second traversal of the full graph and it "
            "has not been run. It is missing rather than estimated.",
        ]),
    ],
    keywords=["formal verification", "Lean 4", "Mathlib", "axiom of choice",
              "dominator tree", "dependency graph", "classical logic",
              "proof assistant", "provenance", "constructive mathematics"],
    based_on="https://doi.org/10.5281/zenodo.21883963",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Which Constant Is Responsible? Dominator '
        'Analysis of Classical Dependence in Mathlib</em>. Zenodo. '
        '<a href="https://doi.org/10.5281/zenodo.21883963">10.5281/zenodo.21883963</a>'),
)

if __name__ == "__main__":
    build(idx)
