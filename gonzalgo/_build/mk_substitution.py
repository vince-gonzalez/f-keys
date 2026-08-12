"""The Substitution Ledger — what survived the kernel, at the top of the ranking.

    python gonzalgo/_build/extract_substitution.py
    python gonzalgo/_build/mk_substitution.py
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "substitution-rows.json").read_text(encoding="utf-8"))

OCC = sum(r["occurrences"] for r in rows)
TESTABLE = sum(r["testable"] for r in rows)
FREE = sum(r["kernel_verified_choice_free"] for r in rows)
WON = [r for r in rows if r["kernel_verified_choice_free"]]

idx = Index(
    slug="substitution-ledger",
    title="The Substitution Ledger",
    kicker="what actually came out, checked by the kernel",
    meta_title="The Substitution Ledger — kernel-verified removal of classical dependence in Mathlib",
    meta_description=(
        "Substitution attempted on the 20 largest sites of classical dependence in "
        "Mathlib: 114 occurrences of Classical.propDecidable, 21 reachable by the "
        "harness, 8 replaced by a constructive instance the kernel accepted, in 3 "
        "declarations."),
    description=(
        "Kernel-verified substitution attempted against the 20 largest sites of "
        "classical dependence in Mathlib. For each declaration: occurrences of "
        "Classical.propDecidable in its proof term, how many the harness could "
        "reach, how many had a Decidable instance synthesised, and how many "
        "produced a term the kernel accepted."),
    lede=[
        "Every other measure in this program ranks or bounds. This one removes. A "
        "site is only shown to be repairable when a substituted proof term is "
        "accepted by Lean's kernel, which is the same standard the library itself "
        "is held to and the only measure here that has ever discriminated.",
        f"Run against the top of the dominance ranking it returns {FREE} of {OCC} "
        f"occurrences, in {len(WON)} declarations. That is the result: at the very "
        "top of the ranking, substitution almost entirely fails.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 &middot; substituted terms accepted by the Lean kernel, '
        'not by the elaborator'),
    columns=[
        Column("declaration", "declaration"),
        Column("theorems_dominated", "dominates", align="right"),
        Column("occurrences", "occurrences", align="right"),
        Column("testable", "testable", align="right"),
        Column("synthesised", "synthesised", align="right"),
        Column("kernel_verified_choice_free", "choice-free", align="right", emph=True),
    ],
    rows=rows,
    measured={
        "Lean 4": "4.32.1 with Mathlib v4.32.1",
        "target": "Classical.propDecidable",
        "acceptance": "Lean kernel",
    },
    notes=(
        "The four counts narrow in sequence. <em>occurrences</em> is uses of "
        "<code>Classical.propDecidable</code> in the proof term; <em>testable</em> "
        "is how many the harness could reach; <em>synthesised</em> is how many had "
        "a <code>Decidable</code> instance found; <em>choice-free</em> is how many "
        "produced a term the kernel accepted. Only the last column means a removal "
        "happened."),
    sections=[
        ("The bottleneck is not synthesis", [
            f"Of {OCC} occurrences only {TESTABLE} were testable at all. The rest "
            "occur under binders, where the proposition is not closed and cannot be "
            "handed to instance synthesis from outside its declaration. That is a "
            "limit of this harness rather than a fact about the proofs, so the "
            f"{FREE} here is a floor. Re-running inside each declaration's own "
            "context is the obvious next move and has not been done.",
            f"Where an occurrence was testable, synthesis and the kernel agreed "
            f"every time: {FREE} synthesised, {FREE} accepted, no term that "
            "elaborated and then failed to check.",
        ]),
        ("What came out, and what it says", [
            "All three successes are private lemmas about <code>Nat</code> and "
            "<code>Int</code> — bit arithmetic, modular arithmetic, a cast — where "
            "the propositions are decidable by computation and a constructive "
            "instance already exists. That is the same population the controlled "
            "experiment identifies: on Nat and Int the free instance is there and "
            "the classical one was taken anyway.",
            "Nothing at the head of the ranking moved. "
            "<code>Classical.propDecidable</code> dominates 91,858 theorems, has a "
            "choice-free type, passes the eligibility test, and cannot be made "
            "constructive. <code>lt_or_eq_of_le</code> dominates 2,018 and its one "
            "occurrence was not testable. The ranking is good at finding what is "
            "load-bearing and it does not follow that what is load-bearing can be "
            "moved.",
        ]),
    ],
    reproduce=[
        "lake env lean -D maxErrors=4000 lean/Subst2.lean",
    ],
    reproduce_note=(
        "<code>ConstantInfo.value?</code> must be passed "
        "<code>allowOpaque := true</code> or theorem proof terms read as empty and "
        "every occurrence count here comes back zero. Code and derived data: "
        "<a href=\"https://doi.org/10.5281/zenodo.21883963\">"
        "10.5281/zenodo.21883963</a>."),
    keywords=["formal verification", "Lean 4", "Mathlib", "axiom of choice",
              "Classical.propDecidable", "Decidable", "constructive mathematics",
              "kernel", "proof assistant", "provenance"],
    invariants=[
        ("the four counts narrow in sequence on every row",
         lambda rs: all(r["kernel_verified_choice_free"] <= r["synthesised"]
                        <= r["testable"] <= r["occurrences"] for r in rs)),
        ("the totals are 114 occurrences, 21 testable, 8 synthesised, 8 choice-free",
         lambda rs: (sum(r["occurrences"] for r in rs),
                     sum(r["testable"] for r in rs),
                     sum(r["synthesised"] for r in rs),
                     sum(r["kernel_verified_choice_free"] for r in rs))
         == (114, 21, 8, 8)),
        ("everything synthesised was also accepted by the kernel",
         lambda rs: all(r["synthesised"] == r["kernel_verified_choice_free"]
                        for r in rs)),
        ("exactly 3 declarations yielded a removal, all private Nat/Int lemmas",
         lambda rs: [r["declaration"] for r in rs
                     if r["kernel_verified_choice_free"]]
         and sum(1 for r in rs if r["kernel_verified_choice_free"]) == 3
         and all(r["declaration"].startswith("_private.Init.Data.")
                 for r in rs if r["kernel_verified_choice_free"])),
        ("nothing at the head of the dominance ranking moved",
         lambda rs: all(r["kernel_verified_choice_free"] == 0 for r in rs
                        if (r["theorems_dominated"] or 0) >= 2018)),
        ("every row that names a dominance count also names its route to the axiom",
         lambda rs: all(r["route_to_axiom"] for r in rs
                        if r["theorems_dominated"] is not None)),
    ],
    based_on="https://doi.org/10.5281/zenodo.21883963",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Which Constant Is Responsible? Dominator '
        'Analysis of Classical Dependence in Mathlib</em>. Zenodo. '
        '<a href="https://doi.org/10.5281/zenodo.21883963">10.5281/zenodo.21883963</a>'),
)

if __name__ == "__main__":
    build(idx)
