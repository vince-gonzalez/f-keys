"""The set.mm Axiom Table — every axiomatic assertion and what rests on it.

    python gonzalgo/_build/extract_setmm_axioms.py
    python gonzalgo/_build/mk_setmm_axioms.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "setmm-axioms-rows.json").read_text(encoding="utf-8"))

THEOREMS = 47621
USED = [r for r in rows if r["dependents"] > 0]
UNUSED = [r for r in rows if r["dependents"] == 0]
BY_ROLE = collections.Counter(r["role"] for r in USED)
UNUSED_AX = [r for r in UNUSED if r["role"] == "axiom"]


def dep(label):
    return next(r["dependents"] for r in rows if r["label"] == label)


idx = Index(
    slug="setmm-axioms",
    title="The set.mm Axiom Table",
    kicker="every axiomatic assertion in set.mm, and how much rests on it",
    meta_title="The set.mm Axiom Table — dependents of every axiom, definition and syntax constructor",
    meta_description=(
        "All 3,004 axiomatic assertions in Metamath's set.mm with the number of the "
        "library's 47,621 theorems depending on each. ax-mp reaches 99.9%; 213 are "
        "declared and never reached at all, 8 of them axioms."),
    description=(
        "Every $a statement in Metamath's set.mm — logical axioms, definitions and "
        "syntax constructors kept apart — with the number of the library's 47,621 "
        "theorems whose proof closure reaches it, and that count as a share of the "
        "library."),
    lede=[
        "A formal library's foundation is usually described rather than counted. "
        f"This is the count: all {len(rows):,} axiomatic assertions in "
        f"<code>set.mm</code>, each with how many of the library's {THEOREMS:,} "
        "theorems reach it.",
        "The three kinds have to be kept apart or the total means nothing. "
        f"{BY_ROLE['axiom']} are logical or set-theoretic axioms, "
        f"{BY_ROLE['definition']:,} are definitions, and "
        f"{BY_ROLE['syntax constructor']:,} are well-formedness constructors "
        "carrying no mathematical content — <code>wi</code> says an implication is "
        "a formula. All three are <code>$a</code> statements and a naive count adds "
        "them together.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Metamath '
        '<code>set.mm</code> &middot; proof closure of all 47,621 theorems, taken '
        "from the database's own proof structure"),
    columns=[
        Column("label", "label"),
        Column("role", "role", dim=True),
        Column("dependents", "theorems depending", align="right"),
        Column("share_of_library_pct", "share of library", align="right", pct=True),
        Column("entry_points", "entry points", align="right"),
        Column("amplification", "amplification", align="right", fmt="{:,.1f}"),
    ],
    rows=rows,
    row_limit=120,
    row_limit_note="The tail is mostly definitions used by a handful of theorems.",
    measured={"Metamath": "set.mm", "theorems": THEOREMS},
    notes=(
        "<em>entry points</em> counts theorems whose own proof names this "
        "statement directly, as opposed to reaching it through another theorem. "
        "<em>amplification</em> is dependents per entry point, left blank where "
        "nothing cites it directly. Do not rank on amplification &mdash; it is a "
        "property of how the library was factored, not of the mathematics, and "
        "the <a href=\"/gonzalgo/entry-points/\">Entry-Point Table</a> gives the "
        "argument. "
        "<em>theorems depending</em> counts theorems whose proof closure reaches "
        "this statement, so it includes everything inherited through other "
        "theorems rather than only direct citations. A count of 0 means no theorem "
        "in the library reaches it at all."),
    sections=[
        ("The concentration", [
            f"<code>ax-mp</code>, modus ponens, is reached by {dep('ax-mp'):,} "
            f"theorems — {round(100*dep('ax-mp')/THEOREMS,1)}% of the library. "
            f"<code>ax-gen</code> reaches {dep('ax-gen'):,}. The top of this table "
            "is not a ranking so much as a description of what it means to be a "
            "logical foundation: nearly everything rests on nearly all of it.",
            "The interesting part is how fast it falls away. Past the propositional "
            "and first-order core the counts drop into the hundreds and then the "
            "single digits, which is why a measure of what a theorem rests on is "
            "worth computing rather than assuming.",
        ]),
        ("Declared and never reached", [
            f"{len(UNUSED)} of these statements are reached by no theorem in the "
            f"library, and {len(UNUSED_AX)} of them are axioms: "
            + ", ".join(f"<code>{r['label']}</code>" for r in UNUSED_AX) + ". "
            "A declared axiom nothing depends on is not a defect — a database can "
            "state a principle for completeness, or keep one for a development that "
            "was never built out — but it is the kind of fact that is easier to "
            "measure than to remember.",
        ]),
        ("One proof step, ninety-three percent of the library", [
            "<code>ax-4</code> is cited directly in exactly one proof and reached "
            "by 44,501 theorems &mdash; 93.4% of set.mm. That is the whole case "
            "for computing provenance rather than reading a changelog: the set of "
            "theorems that <em>use</em> an axiom and the set that <em>depend</em> "
            "on it are almost disjoint, and only one of them is visible by "
            "inspection.",
        ]),
        ("Where the 1,447 comes from", [
            "The <a href=\"/gonzalgo/entry-points/\">Entry-Point Table</a> reports "
            f"1,447 axioms used for set.mm. That figure is the "
            f"{BY_ROLE['axiom']} axioms plus the {BY_ROLE['definition']:,} "
            "definitions that at least one theorem reaches, and it excludes both "
            "the syntax constructors and everything nothing reaches. This table is "
            "where that number decomposes.",
        ]),
    ],
    reproduce=["pip install gonzalgo", "gonzalgo mm set.mm"],
    reproduce_note=(
        "Every figure comes from set.mm's own proof structure. Method: "
        "<a href=\"https://doi.org/10.5281/zenodo.21769846\">"
        "10.5281/zenodo.21769846</a>."),
    keywords=["Metamath", "set.mm", "ZFC", "axioms", "definitions",
              "formal verification", "foundations of mathematics",
              "proof assistant", "dependency analysis"],
    invariants=[
        ("rows are ordered by dependents, descending",
         lambda rs: all(rs[i]["dependents"] >= rs[i + 1]["dependents"]
                        for i in range(len(rs) - 1))),
        ("no statement is reached by more theorems than the library has",
         lambda rs: all(r["dependents"] <= THEOREMS for r in rs)),
        ("every share recomputes from its own count",
         lambda rs: all(abs(round(100 * r["dependents"] / THEOREMS, 2)
                            - r["share_of_library_pct"]) <= 0.01 for r in rs)),
        ("every row is classified as axiom, definition or syntax constructor",
         lambda rs: all(r["role"] in ("axiom", "definition", "syntax constructor")
                        for r in rs)),
        ("the role follows the label prefix",
         lambda rs: all(r["role"] == ("axiom" if r["label"].startswith("ax-")
                                      else "definition" if r["label"].startswith("df-")
                                      else "syntax constructor") for r in rs)),
        # The identity that ties this table to the Entry-Point Table. It holds over
        # REACHED statements only, which is what "axioms used" means.
        ("reached axioms plus reached definitions give the 1,447 used",
         lambda rs: sum(1 for r in rs if r["dependents"] > 0
                        and r["role"] in ("axiom", "definition")) == 1447),
        ("213 statements are reached by nothing, 8 of them axioms",
         lambda rs: sum(1 for r in rs if r["dependents"] == 0) == 213
         and sum(1 for r in rs if r["dependents"] == 0
                 and r["role"] == "axiom") == 8),
        ("entry points on axioms and definitions total the 17,898 the paper reports",
         lambda rs: sum(r["entry_points"] for r in rs
                        if r["role"] in ("axiom", "definition")) == 17898),
        ("ax-4 is cited once and reached by 44,501",
         lambda rs: (lambda r: r["entry_points"] == 1
                     and r["dependents"] == 44501)(
             next(r for r in rs if r["label"] == "ax-4"))),
        ("amplification is present exactly where something cites it",
         lambda rs: all((r["amplification"] is not None) == (r["entry_points"] > 0)
                        for r in rs)),
        ("amplification recomputes as dependents over entry points",
         lambda rs: all(abs(round(r["dependents"] / r["entry_points"], 1)
                            - r["amplification"]) <= 0.05
                        for r in rs if r["entry_points"])),
        ("ax-mp heads the table at 47,562",
         lambda rs: rs[0]["label"] == "ax-mp" and rs[0]["dependents"] == 47562),
    ],
    based_on="https://doi.org/10.5281/zenodo.21769846",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
