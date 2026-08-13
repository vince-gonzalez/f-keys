"""The Version Delta Table — what moved in Mathlib between two releases.

    python gonzalgo/_build/extract_version_delta.py
    python gonzalgo/_build/mk_version_delta.py
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "version-delta-index-rows.json").read_text(encoding="utf-8"))


def q(name, field="delta"):
    return next(r[field] for r in rows if r["quantity"] == name)


REPROVED = q("reproved only")
NEW_THEOREMS = q("theorems")
AXIOMS = next(r for r in rows if r["quantity"] == "axiom roster")

idx = Index(
    slug="version-delta",
    title="The Version Delta Table",
    kicker="what moved in Mathlib between two releases",
    meta_title="The Version Delta Table — Mathlib v4.32.1 to v4.33.0, measured",
    meta_description=(
        "What changed in Mathlib's declaration graph between v4.32.1 and v4.33.0: "
        "the axiom roster held at 15, 5,047 declarations were added net, and 24,172 "
        "theorems kept their statement while their proof changed."),
    description=(
        "Declaration-graph differences between two Mathlib releases, measured by "
        "the same extractor on both sides. Separates declarations added and removed "
        "from those that kept their name — and among those, separates a changed "
        "statement from a changed proof."),
    lede=[
        "Every other measurement here is a snapshot. This is the first that needed "
        "two, and it answers a question that could not be asked before: what happens "
        "to a formal library's trusted base when it ships a release.",
        f"For v4.32.1 to v4.33.0 the answer is that the trusted base did not move. "
        f"The axiom roster is the same {AXIOMS['new_value']} axioms on both sides. "
        f"Everything else grew.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 against Lean 4.33.0 with Mathlib v4.33.0 (tag '
        '<code>db584cd6</code>) &middot; the same extractor on both sides'),
    columns=[
        Column("quantity", "quantity"),
        Column("old_value", "v4.32.1", align="right"),
        Column("new_value", "v4.33.0", align="right"),
        Column("delta", "delta", align="right", fmt="{:+,}"),
        Column("note", "note", dim=True),
    ],
    rows=rows,
    measured={
        "from": "Lean 4.32.1, Mathlib v4.32.1",
        "to": "Lean 4.33.0, Mathlib v4.33.0",
        "extractor": "the same on both sides",
    },
    notes=(
        "<em>statements changed</em> and <em>reproved only</em> are both computed "
        "over declarations present in both releases under the same name. A changed "
        "statement means the declaration's type dependencies moved, so it is a "
        "different claim wearing an old name. <em>reproved only</em> means the "
        "statement held and the proof dependencies moved."),
    sections=[
        ("The trusted base held", [
            f"The axiom roster is identical across the release: "
            f"{AXIOMS['new_value']} axioms, none added, none removed. That is the "
            "sentence anyone depending on Mathlib wants and nobody could state "
            "before, because stating it requires measuring both sides with the same "
            "instrument rather than reading a changelog.",
            "It is also the row most worth re-running every release. An axiom "
            "appearing is the one change to a library that no test suite catches and "
            "no diff summarises.",
        ]),
        ("Proofs churn faster than the library grows", [
            f"{REPROVED:,} theorems kept their exact statement and got different "
            f"proof dependencies. Net new theorems over the same release: "
            f"{NEW_THEOREMS:,}. Proof churn runs roughly "
            f"{REPROVED / NEW_THEOREMS:.0f}x growth.",
            "Neither number is visible to a text diff. A diff sees a file changed; "
            "it cannot see that a theorem's proof dependencies moved while its "
            "statement stood still. That distinction is the whole reason to compute "
            "this from a provenance dump.",
            "It also bounds how stale a provenance measurement gets. Any figure "
            "about what proofs rest on is measuring a population that turns over at "
            "this rate, which is the argument for republishing per release rather "
            "than citing a number from a year ago.",
        ]),
        ("What this does not say", [
            "It does not say the reproved theorems changed what they rest on. A "
            "different proof can reach exactly the same axioms. Establishing that "
            "requires computing the closure on both sides, which is a separate and "
            "much more expensive measurement than this one.",
            "Two dumps from different extractors cannot be compared, so both labels "
            "are recorded in the data. The comparison here used one extractor across "
            "both releases.",
        ]),
    ],
    reproduce=[
        "lake env lean -D maxErrors=4000 Split.lean   # once per release",
        "python diff_dumps.py OLD.tsv NEW.tsv --old-label v4.32.1 --new-label v4.33.0",
    ],
    reproduce_note=(
        "A Mathlib dump takes roughly twenty minutes and 650 MB per side. Method: "
        "<a href=\"https://doi.org/10.5281/zenodo.21769846\">"
        "10.5281/zenodo.21769846</a>."),
    keywords=["Lean 4", "Mathlib", "formal verification", "software evolution",
              "trusted computing base", "axioms", "library versioning",
              "dependency graph", "reproducibility"],
    invariants=[
        ("every row names both versions it compares",
         lambda rs: all(r["from_version"] == "v4.32.1"
                        and r["to_version"] == "v4.33.0" for r in rs)),
        ("the axiom roster is unchanged at 15 on both sides",
         lambda rs: (lambda r: r["old_value"] == r["new_value"] == 15
                     and r["delta"] == 0)(
             next(r for r in rs if r["quantity"] == "axiom roster"))),
        ("declaration totals agree with the measured dumps",
         lambda rs: (lambda r: (r["old_value"], r["new_value"])
                     == (790171, 795218))(
             next(r for r in rs if r["quantity"] == "declarations"))),
        ("theorem totals agree with the measured dumps",
         lambda rs: (lambda r: (r["old_value"], r["new_value"])
                     == (532605, 535601))(
             next(r for r in rs if r["quantity"] == "theorems"))),
        ("added minus removed equals the net declaration change",
         lambda rs: (next(r["delta"] for r in rs if r["quantity"] == "declarations added")
                     + next(r["delta"] for r in rs if r["quantity"] == "declarations removed"))
         == next(r["delta"] for r in rs if r["quantity"] == "declarations")),
        ("the kinds sum to the declaration total on both sides",
         lambda rs: all(
             sum(next(r[f] for r in rs if r["quantity"] == k)
                 for k in ("theorems", "definitions", "others", "axioms"))
             == next(r[f] for r in rs if r["quantity"] == "declarations")
             for f in ("old_value", "new_value"))),
        ("more theorems were reproved than added",
         lambda rs: next(r["delta"] for r in rs if r["quantity"] == "reproved only")
         > next(r["delta"] for r in rs if r["quantity"] == "theorems")),
    ],
    based_on="https://doi.org/10.5281/zenodo.21769846",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
