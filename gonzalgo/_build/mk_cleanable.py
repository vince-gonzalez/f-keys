"""The Cleanable Table — every declaration whose classical dependence came out.

    python gonzalgo/_build/extract_cleanable.py
    python gonzalgo/_build/mk_cleanable.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "cleanable-rows.json").read_text(encoding="utf-8"))

BY_LIB = collections.Counter(r["library"] for r in rows)
REMOVED = [r for r in rows if r["outcome"] == "removed"]

idx = Index(
    slug="cleanable",
    title="The Cleanable Table",
    kicker="the declarations whose dependence on choice actually came out",
    meta_title="The Cleanable Table — 275 kernel-verified removals of classical dependence in Lean",
    meta_description=(
        "Every declaration in Lean core, Std, Batteries and Mathlib where a classical "
        "dependence was rewritten away and the kernel accepted the result: 275 "
        "removed, 4 rejected, 1 still classical, across 60 modules. 223 of them are "
        "in Lean core."),
    description=(
        "Declarations in Lean 4 core, Std, Batteries, Mathlib and Plausible where a "
        "rewrite removing a classical dependence was attempted, with the module, the "
        "compiler-generated proof term carrying the dependence, the outcome, and the "
        "kernel's reason where it refused."),
    lede=[
        f"{len(REMOVED)} declarations across {len({r['module'] for r in rows})} "
        "modules were rewritten to remove a dependence on the axiom of choice, and "
        "the Lean kernel accepted every one. Four were refused and one kept its "
        "dependence. This is the list.",
        "The unit is a compiler-generated <code>_proof_N</code> term rather than a "
        "lemma anyone wrote, and that is the finding rather than a caveat. The "
        "removable dependence in these libraries sits in terms the elaborator "
        "emitted, so it comes out by changing the tactic that emits them and not by "
        "editing a proof.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 &middot; every rewrite checked by the Lean kernel, not the '
        'elaborator'),
    columns=[
        Column("library", "library"),
        Column("module", "module", dim=True),
        Column("declaration", "declaration"),
        Column("occurrences", "occurrences", align="right"),
        Column("outcome", "outcome"),
    ],
    rows=rows,
    measured={
        "Lean 4": "4.32.1 with Mathlib v4.32.1",
        "target": "Classical.propDecidable",
        "acceptance": "Lean kernel",
    },
    notes=(
        "<em>occurrences</em> is how many uses of "
        "<code>Classical.propDecidable</code> the generated term carried. "
        "<em>outcome</em> is <code>removed</code> where the kernel accepted the "
        "rewritten term, <code>kernel rejected</code> where it refused, and "
        "<code>still classical</code> where the rewrite left the dependence in "
        "place. The full data carries the generated term's name and, for the four "
        "refusals, the kernel's message verbatim."),
    sections=[
        ("Where it lives", [
            "The distribution is the useful part: "
            + ", ".join(f"{lib} {n}" for lib, n in BY_LIB.most_common())
            + ". Four fifths of the removable classical dependence in this "
            "measurement is in Lean core, and only nine declarations are in Mathlib.",
            "That matters for what anyone can do about it. Lean core's position on "
            "the tactic behaviour behind most of these is on record: avoiding choice "
            "is a deliberate non-goal there, stated in response to the "
            "<code>omega</code> report and without disputing any figure. So the "
            "largest share of what is removable sits where removal is not wanted, "
            "and the share sitting where it might be welcomed is small.",
        ]),
        ("The four the kernel refused", [
            "Every refusal is a type mismatch rather than a timeout or a missing "
            "instance: the substituted term elaborated and then failed to check. "
            "Those are the interesting ones, because they are cases where a "
            "<code>Decidable</code> instance exists and is still not "
            "interchangeable with the classical one at the point it is used. The "
            "kernel's message is carried verbatim in the data for each.",
        ]),
        ("What this is not", [
            "It is not a claim that 275 theorems were made constructive. Removing a "
            "use of <code>Classical.propDecidable</code> from a generated term "
            "removes one route to the axiom; whether the declaration still reaches "
            "choice by another route is a separate question this table does not "
            "answer. The <a href=\"/gonzalgo/dominator-table/\">Dominator Table</a> "
            "is where routes are counted.",
        ]),
    ],
    reproduce=[
        "lake env lean -D maxErrors=4000 lean/Substitute.lean",
    ],
    reproduce_note=(
        "<code>ConstantInfo.value?</code> must be passed "
        "<code>allowOpaque := true</code> or theorem proof terms read as empty and "
        "every occurrence count comes back zero. Method: "
        "<a href=\"https://doi.org/10.5281/zenodo.21769846\">"
        "10.5281/zenodo.21769846</a>."),
    keywords=["Lean 4", "Mathlib", "Batteries", "Lean core", "axiom of choice",
              "Classical.propDecidable", "Decidable", "kernel",
              "constructive mathematics", "formal verification"],
    invariants=[
        ("275 removed, 4 rejected, 1 still classical",
         lambda rs: dict(collections.Counter(r["outcome"] for r in rs))
         == {"removed": 275, "kernel rejected": 4, "still classical": 1}),
        ("every row names its library, module and declaration",
         lambda rs: all(r["library"] and r["module"] and r["declaration"]
                        for r in rs)),
        ("the library is the first component of the module path",
         lambda rs: all(r["module"].split(".")[0] == r["library"] for r in rs)),
        ("every refusal carries the kernel's reason and nothing else does",
         lambda rs: all((r["kernel_reason"] is not None)
                        == (r["outcome"] == "kernel rejected") for r in rs)),
        ("every row carries a positive occurrence count",
         lambda rs: all(isinstance(r["occurrences"], int) and r["occurrences"] > 0
                        for r in rs)),
        ("the library split is Init 223, Std 41, Mathlib 9, Batteries 3, Lean 3, "
         "Plausible 1",
         lambda rs: dict(collections.Counter(r["library"] for r in rs))
         == {"Init": 223, "Std": 41, "Mathlib": 9, "Batteries": 3, "Lean": 3,
             "Plausible": 1}),
    ],
    based_on="https://doi.org/10.5281/zenodo.21769846",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
