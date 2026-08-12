"""The Dominator Table — which sites Mathlib's classical dependence rests on.

    python gonzalgo/_build/extract_dominator_rows.py
    python gonzalgo/_build/mk_dominator_table.py
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "dominator-table-rows.json").read_text(encoding="utf-8"))


def _count(rs, name):
    return next(r["theorems_dominated"] for r in rs if r["site"] == name)


idx = Index(
    slug="dominator-table",
    title="The Dominator Table",
    kicker="which sites Mathlib's use of choice actually rests on",
    meta_title="The Dominator Table — which sites Mathlib's classical dependence rests on",
    meta_description=(
        "The 1,500 largest sites of classical dependence in Mathlib, ranked by how "
        "many theorems would stop depending on the axiom of choice if that site were "
        "rebuilt. Dominance, not reachability: the two differ by 58x on the first "
        "case examined."),
    description=(
        "Sites of classical dependence in Mathlib ranked by how many theorems each is "
        "uniquely responsible for — the number that would stop depending on the axiom "
        "of choice if that site alone were rebuilt. Computed as a dominator tree over "
        "the reversed dependency graph rooted at the axiom, with chains of constants "
        "that free the same theorems collapsed to a single site."),
    lede=[
        "Asking which constant a theorem's classical dependence is <em>responsible</em> "
        "to is not the same as asking which constants its proof touches, and the "
        "answers are far apart. 116,766 theorems reach the order lemma "
        "<code>lt_or_eq_of_le</code>; 2,018 would stop being classical if it were "
        "rebuilt. Reachability overstates responsibility by 58x in that one case.",
        "The column below is the second number. A site's count is the theorems whose "
        "every route to <code>Classical.choice</code> passes through it, so repairing "
        "it repairs exactly them and nothing else.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 &middot; 790,171 declarations, 30,015,601 dependency edges, '
        'one dominator tree over all 766,564 constants'),
    columns=[
        Column("rank", "#", align="right"),
        Column("site", "site"),
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
        "unit": "sites, chains collapsed at a 0.97 weight ratio",
    },
    row_limit=100,
    row_limit_note="The tail is long and flat &mdash; rank 1,500 dominates 16.",
    notes=(
        "<em>theorems dominated</em> counts theorems for which this site is the sole "
        "route to the axiom. <em>eligible</em> is false when the site's own type is "
        "classical, so no constructive replacement for it can exist &mdash; true of "
        "only 2 of the 1,500, which is the negative result in the eligibility note: "
        "the test does not discriminate among load-bearing sites. The full data "
        "carries each site's <code>chain</code>, and <code>constant_alone</code> "
        "where the site's label constant dominates fewer theorems by itself than the "
        "chain does together."),
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
            "60.1% of classically dependent theorems have no responsible site at all. "
            "Their immediate dominator is the axiom itself, so no local repair "
            "anywhere in the library reaches them. That is the ceiling on what this "
            "kind of work can do, and it was not previously known.",
            "Outside classical logic proper, the largest sites are infrastructure "
            "rather than mathematics: a functor category instance at 5,271, hash-map "
            "well-formedness at 4,899, the powerset Boolean algebra at 3,430, string "
            "conversion at 1,111. The places where choice is load-bearing are not the "
            "places anyone would have pointed at.",
        ]),
        ("Why sites rather than constants", [
            "A run of constants that each dominate the next, losing no theorems "
            "between them, is one repair and not several &mdash; severing any member "
            "frees the same theorems. Counting them separately would count one repair "
            "many times. 182 of the 1,500 rows here are such chains; the rest are "
            "single constants.",
            "The hash-map row is the clearest case. "
            "<code>Std.DHashMap.Internal.Raw.WF.out</code>, <code>wfImp_alter</code> "
            "and <code>isHashSelf_updateBucket_alter</code> dominate 4,892, 4,896 and "
            "4,899 theorems taken individually, and they are one site of 4,899. Read "
            "as three constants they look like three findings; read as a site they are "
            "one piece of infrastructure.",
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
    invariants=[
        ("ranks are 1..N with no gaps",
         lambda rs: [r["rank"] for r in rs] == list(range(1, len(rs) + 1))),
        ("rank order matches the dominated count, descending",
         lambda rs: all(rs[i]["theorems_dominated"] >= rs[i + 1]["theorems_dominated"]
                        for i in range(len(rs) - 1))),
        # Every figure quoted in the prose above or in llms.txt, checked against
        # the rows that render underneath it.
        ("Classical.propDecidable heads the table at 91,858",
         lambda rs: rs[0]["site"] == "Classical.propDecidable"
         and rs[0]["theorems_dominated"] == 91858),
        ("the four infrastructure sites read 5,271 / 4,899 / 3,430 / 1,111, as the "
         "deposited note reports them",
         lambda rs: [_count(rs, n) for n in (
             "CategoryTheory.Functor.category",
             "Std.DHashMap.Internal.Raw.WF.out",
             "Set.instCompleteAtomicBooleanAlgebra",
             "String.toList")] == [5271, 4899, 3430, 1111]),
        ("lt_or_eq_of_le dominates the 2,018 the 58x comparison depends on",
         lambda rs: _count(rs, "lt_or_eq_of_le") == 2018),
        ("every row carries its area and eligibility",
         lambda rs: all(r["area"] is not None and r["eligible"] is not None
                        for r in rs)),
        ("exactly 2 sites are ineligible, the eligibility note's cliff",
         lambda rs: sum(1 for r in rs if not r["eligible"]) == 2),
        ("182 rows are collapsed chains and every one names its members",
         lambda rs: sum(1 for r in rs if r["chain_length"] > 1) == 182
         and all(r["chain"] for r in rs)),
    ],
    based_on="https://doi.org/10.5281/zenodo.21883963",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Which Constant Is Responsible? Dominator '
        'Analysis of Classical Dependence in Mathlib</em>. Zenodo. '
        '<a href="https://doi.org/10.5281/zenodo.21883963">10.5281/zenodo.21883963</a>'),
)

if __name__ == "__main__":
    build(idx)
