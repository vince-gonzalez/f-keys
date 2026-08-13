"""The Choice Strength Table — which choice principle each theorem actually needs.

    python gonzalgo/_build/extract_choice_strength.py
    python gonzalgo/_build/mk_choice_strength.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "choice-strength-rows.json").read_text(encoding="utf-8"))

THEOREMS = 47621
P = collections.Counter(r["strongest"] for r in rows)
REACH = {k: sum(1 for r in rows if r[f"reaches_{k}_choice"])
         for k in ("full", "countable", "dependent")}

idx = Index(
    slug="choice-strength",
    title="The Choice Strength Table",
    kicker="not whether a theorem uses choice, but how much of it",
    meta_title="The Choice Strength Table — full, countable and dependent choice in set.mm",
    meta_description=(
        "Every theorem in Metamath's set.mm that depends on a choice principle, "
        "labelled with the strongest one it reaches. 583 need full choice, 879 need "
        "only countable choice, 66 only dependent choice — more theorems rest on "
        "countable choice than on choice proper."),
    description=(
        "The 1,528 theorems in Metamath's set.mm whose proofs reach a choice "
        "principle, each labelled with the strongest of the three the database "
        "declares separately — full choice, countable choice, dependent choice — "
        "together with the raw membership in all three."),
    lede=[
        "&ldquo;Depends on choice&rdquo; is usually reported as one bit. "
        "<code>set.mm</code> declares three choice principles as separate axioms, "
        "so for this library it does not have to be.",
        f"Of {THEOREMS:,} theorems, {len(rows):,} reach one "
        f"({100*len(rows)/THEOREMS:.2f}%). "
        f"{P['full choice']} need full choice. "
        f"{P['countable choice']} need only countable choice. "
        f"{P['dependent choice']} need only dependent choice. "
        "The weaker principle carries more of the library than the strong one "
        "does.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Metamath '
        '<code>set.mm</code> &middot; proof closure of all 47,621 theorems against '
        '<code>ax-ac</code>, <code>ax-ac2</code>, <code>ax-cc</code> and '
        '<code>ax-dc</code>'),
    columns=[
        Column("theorem", "theorem"),
        Column("strongest", "strongest principle needed"),
        Column("axioms_reached", "axioms reached", dim=True),
    ],
    rows=rows,
    row_limit=120,
    row_limit_note="Grouped by principle, strongest first.",
    measured={"Metamath": "set.mm", "theorems": THEOREMS,
              "principles": "ax-ac, ax-ac2, ax-cc, ax-dc"},
    notes=(
        "<em>strongest</em> partitions these theorems: a theorem reaching full "
        "choice is counted there even if it also reaches the weaker principles. "
        "The raw memberships overlap and are in the data &mdash; "
        f"{REACH['full']} reach full choice, {REACH['countable']} reach countable, "
        f"{REACH['dependent']} reach dependent, with 137 theorems in both full and "
        "countable alone."),
    sections=[
        ("The weaker axiom does more work", [
            f"{REACH['countable']} theorems reach countable choice against "
            f"{REACH['full']} reaching choice proper. Countable choice is the "
            "weaker principle and it is load-bearing for more of this library, "
            "which is not what a single choice-dependence figure would suggest.",
            "It also changes what a repair would mean. A theorem resting only on "
            "countable choice is already closer to a constructive setting than the "
            "same theorem resting on full choice, and reporting both as "
            "&ldquo;classical&rdquo; erases the distinction the database went to "
            "the trouble of making.",
        ]),
        ("Why this differs from the Kernel Index figure", [
            "The <a href=\"/gonzalgo/kernel-index/\">Kernel Index</a> reports "
            "set.mm at 1.22%, which is 583 theorems reaching full choice over "
            f"{THEOREMS:,}. Counting every choice principle gives {len(rows):,}, or "
            f"{100*len(rows)/THEOREMS:.2f}%. Neither number is wrong; they answer "
            "different questions, and this table is where the difference is "
            "visible rather than implicit.",
            "Lean has no counterpart to this row. <code>Classical.choice</code> is "
            "a single axiom with no weaker sibling in the core, so a Lean library "
            "cannot be stratified this way at all &mdash; the distinction exists "
            "here because set.mm's authors declared the principles separately.",
        ]),
    ],
    reproduce=["pip install gonzalgo", "gonzalgo mm set.mm"],
    reproduce_note=(
        "Method: <a href=\"https://doi.org/10.5281/zenodo.21769846\">"
        "10.5281/zenodo.21769846</a>."),
    keywords=["Metamath", "set.mm", "axiom of choice", "countable choice",
              "dependent choice", "ZFC", "constructive mathematics",
              "foundations of mathematics", "formal verification"],
    invariants=[
        ("the partition is 583 full, 879 countable, 66 dependent",
         lambda rs: dict(collections.Counter(r["strongest"] for r in rs))
         == {"full choice": 583, "countable choice": 879,
             "dependent choice": 66}),
        ("every row reaches at least one choice principle",
         lambda rs: all(r["reaches_full_choice"] or r["reaches_countable_choice"]
                        or r["reaches_dependent_choice"] for r in rs)),
        ("strongest agrees with the reach flags on every row",
         lambda rs: all(
             r["strongest"] == ("full choice" if r["reaches_full_choice"]
                                else "countable choice"
                                if r["reaches_countable_choice"]
                                else "dependent choice") for r in rs)),
        ("raw reach is 583 full, 1,016 countable, 88 dependent",
         lambda rs: [sum(1 for r in rs if r[f"reaches_{k}_choice"])
                     for k in ("full", "countable", "dependent")]
         == [583, 1016, 88]),
        ("countable choice reaches more theorems than full choice",
         lambda rs: sum(1 for r in rs if r["reaches_countable_choice"])
         > sum(1 for r in rs if r["reaches_full_choice"])),
        ("every row names the axioms it reached",
         lambda rs: all(r["axioms_reached"] for r in rs)),
        ("the full-choice count matches the Kernel Index's set.mm figure",
         lambda rs: sum(1 for r in rs if r["reaches_full_choice"]) == 583),
    ],
    based_on="https://doi.org/10.5281/zenodo.21769846",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
