"""The Kernel Index — what formal libraries rest on, library by library.

    python gonzalgo/_build/mk_kernel_index.py

Rows come from data/kernel-index-rows.json, produced by:

    gonzalgo trust mathlib_split.tsv
    gonzalgo mm set.mm iset.mm nf.mm ql.mm hol.mm
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "kernel-index-rows.json").read_text(encoding="utf-8"))

idx = Index(
    slug="kernel-index",
    title="The Kernel Index",
    kicker="what formal libraries actually rest on",
    meta_title="The Kernel Index — what formal mathematical libraries rest on",
    meta_description=(
        "A measured table of what formal libraries rest on: theorems depending on "
        "an unfinished proof, on the compiler rather than the kernel, or on an "
        "optional axiom. Lean 4 and Metamath, six foundations, one program."),
    description=(
        "What formal mathematical libraries rest on: theorems depending on an "
        "unfinished proof, on the compiler rather than the kernel, and on an "
        "optional axiom. Measured by one program across two proof systems and "
        "six foundations."),
    lede=[
        "Each library here was measured directly. The two middle columns are the "
        "ones to read: how many theorems rest on a proof that was never finished, "
        "and how many were settled by running compiled code rather than by the "
        "kernel.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib &middot; Metamath <code>set.mm</code>, <code>iset.mm</code>, '
        '<code>nf.mm</code>, <code>ql.mm</code>, <code>hol.mm</code>'),
    columns=[
        Column("library", "library"),
        Column("system", "system"),
        Column("foundation", "foundation", dim=True),
        Column("theorems", "theorems", align="right"),
        Column("unfinished_theorems", "unfinished", align="right", emph=True),
        Column("compiler_trusting_theorems", "compiler-trusted", align="right", emph=True),
        Column("optional_reach_pct", "optional axiom", align="right", pct=True),
    ],
    rows=rows,
    measured={
        "Lean 4": "4.32.1 with Mathlib",
        "Metamath": "set.mm, iset.mm, nf.mm, ql.mm, hol.mm",
    },
    notes=(
        '<strong style="color:#ff8080">Red</strong> marks a non-zero count &mdash; '
        'theorems resting on an unfinished proof, or on the compiler. '
        '<em>unfinished</em> counts theorems reaching a <code>sorry</code> (Lean) or '
        'a <code>?</code>-bearing proof (Metamath) anywhere upstream, not only those '
        'that state one. <em>optional axiom</em> is the share of theorems depending '
        'on <code>Classical.choice</code> in Lean and on full choice in '
        '<code>set.mm</code>; the other databases declare no choice axiom.'),
    reproduce=[
        "pip install gonzalgo",
        "gonzalgo trust mathlib_split.tsv      # the Lean rows",
        "gonzalgo mm set.mm iset.mm nf.mm ql.mm hol.mm   # the Metamath rows",
    ],
    reproduce_note=(
        "Every figure comes from the proof system's own bookkeeping &mdash; Lean's "
        "<code>collectAxioms</code> and Metamath's proof structure. The extractors "
        "ship with the tool, so you can re-derive any row here yourself."),
    sections=[
        ("Why it exists", [
            "&ldquo;This library rests on nothing but the kernel&rdquo; is something "
            "people have had to take on faith, because checking it at library scale "
            "wasn't practical. The numbers above are that check. A zero in the "
            "middle columns means someone ran it and it came back empty.",
        ]),
    ],
    keywords=["formal verification", "Lean 4", "Mathlib", "Metamath",
              "proof assistant", "axiom", "sorry", "native_decide",
              "provenance", "trusted base"],
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
