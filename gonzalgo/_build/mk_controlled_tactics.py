"""The Controlled Tactic Table — same goal, ten tactics, axioms recorded per cell.

    python gonzalgo/_build/extract_controlled_rows.py
    python gonzalgo/_build/mk_controlled_tactics.py
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "controlled-tactic-rows.json").read_text(encoding="utf-8"))

TACTICS = sorted({r["tactic"] for r in rows})


def closed(rs, **f):
    return [r for r in rs if r["closed"] and all(r[k] == v for k, v in f.items())]


def rate_row(tactic):
    c = closed(rows, tactic=tactic)
    n = sum(1 for r in c if r["classical"])
    pct = f"{100 * n / len(c):.0f}%" if c else "&mdash;"
    return (f"<tr><td><code>{tactic}</code></td>"
            f"<td class='num'>{len(c)}</td><td class='num'>{n}</td>"
            f"<td class='num'>{pct}</td></tr>")


# The summary is computed from the same rows the table renders, so a figure in
# the prose cannot disagree with the data underneath it.
SUMMARY = ("<div class='wrap'><table><thead><tr><th>tactic</th>"
           "<th style='text-align:right'>goals closed</th>"
           "<th style='text-align:right'>classical</th>"
           "<th style='text-align:right'>rate</th></tr></thead><tbody>"
           + "".join(rate_row(t) for t in TACTICS) + "</tbody></table></div>")

nn_order = closed(rows, tactic="norm_num", shape="order")
nn_eq = closed(rows, tactic="norm_num", shape="equality/divisibility")

idx = Index(
    slug="controlled-tactics",
    title="The Controlled Tactic Table",
    kicker="same goal, ten tactics, axioms recorded per cell",
    meta_title="The Controlled Tactic Table — which Lean tactics introduce the axiom of choice",
    meta_description=(
        "270 cells: 27 arithmetic goals over Nat and Int put to ten Lean tactics "
        "each, with the axiom set recorded per cell. norm_num is classical on all "
        "15 order goals and none of the 12 equality goals, while decide, omega and "
        "trivial close all 27 choice-free."),
    description=(
        "A controlled experiment over Lean tactics. 27 arithmetic goals over Nat and "
        "Int, each put to ten tactics, with the axiom set recorded for every cell. "
        "Holding the goal fixed and varying only the tactic separates a classical "
        "dependence introduced by the proof from one required by the statement."),
    lede=[
        "Every observational measure in this program has the same weakness: a "
        "theorem's classical dependence can come from what it says or from how it "
        "was proved, and a census cannot tell you which. This is the intervention "
        "that can. The goal is held fixed, the tactic varies, and anything that "
        "changes between cells is the tactic's doing.",
        "The result is a boundary rather than a gradient. <code>norm_num</code> "
        f"introduces the axiom of choice on all {len(nn_order)} order goals "
        f"(<code>&le;</code>, <code>&lt;</code>, <code>&ge;</code> over "
        f"<code>Nat</code> and <code>Int</code>) and on none of the {len(nn_eq)} "
        "equality and divisibility goals. On the same 27 goals "
        "<code>decide</code>, <code>omega</code> and <code>trivial</code> introduce "
        "it nowhere, so no goal here ever required it.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 &middot; 9 goal families &times; 3 goals &times; 10 tactics '
        '= 270 cells, every cell a separate theorem with its own '
        '<code>#print axioms</code>'),
    columns=[
        Column("goal", "goal"),
        Column("shape", "shape", dim=True),
        Column("tactic", "tactic"),
        Column("closed", "closed"),
        Column("classical", "classical"),
        Column("axioms", "axioms", dim=True),
    ],
    rows=rows,
    measured={
        "Lean 4": "4.32.1 with Mathlib v4.32.1",
        "design": "9 families x 3 goals x 10 tactics, fully crossed",
    },
    notes=(
        "<em>closed</em> is false where the tactic did not prove the goal. Lean "
        "records those as depending on <code>sorryAx</code>, which is the tactic "
        "failing rather than a proof resting on something unfinished, so they are "
        "excluded from every rate below &mdash; a tactic that never ran cannot have "
        "introduced an axiom. <em>classical</em> means "
        "<code>Classical.choice</code> appears in the cell's axiom set."),
    sections=[
        ("Rates, over goals each tactic actually closed", [SUMMARY]),
        ("What the boundary means", [
            "<code>norm_num</code>'s dependence is not a property of the arithmetic. "
            "The same numbers, stated as an equality, come out choice-free from the "
            "same tactic. It is the order goals specifically, and on "
            "<code>Nat</code> and <code>Int</code> the constructive decidability "
            "instance exists and is axiom-free, so the classical route was taken "
            "where a free one was available.",
            "<code>grind</code> is classical on every goal it closes and that is not "
            "a defect: it is architecturally classical. Reporting it beside "
            "<code>norm_num</code> without that distinction is exactly the error the "
            "attribution paper is about &mdash; a rate cannot separate a tactic that "
            "is designed classical from one that reached for choice unnecessarily.",
            "<code>aesop</code> and <code>simp</code> agree on all 27 goals, cell for "
            "cell. aesop's classical cells are simp's classical cells. A search "
            "procedure built over a simp set inherits that set's axiom behaviour "
            "rather than adding to it.",
        ]),
        ("Why this is worth more than the census", [
            "Per-tactic rates measured across a library vary as much within a library "
            "as between them &mdash; 5.8&ndash;28.2% in Mathlib, 45&ndash;100% in Lean "
            "core &mdash; because eligibility is a property of the theorem while the "
            "defect is a property of the proof term. Fixing the goal removes that "
            "confound entirely. Every difference in this table is attributable, "
            "because nothing else was allowed to vary.",
        ]),
    ],
    reproduce=[
        "lake env lean -D maxErrors=4000 lean/Controlled.lean",
    ],
    reproduce_note=(
        "<code>set_option maxErrors</code> inside the file is ignored; only the "
        "command-line flag works, and without it Lean halts at 100 errors long "
        "before the last theorem. The generator and the raw output are in "
        "<a href=\"https://doi.org/10.5281/zenodo.21883963\">10.5281/zenodo.21883963</a>."),
    keywords=["Lean 4", "tactics", "norm_num", "omega", "decide", "grind",
              "aesop", "axiom of choice", "controlled experiment",
              "formal verification", "Mathlib"],
    invariants=[
        ("the design is fully crossed: 9 families x 3 goals x 10 tactics = 270",
         lambda rs: len(rs) == 270
         and len({r["family"] for r in rs}) == 9
         and len({r["tactic"] for r in rs}) == 10
         and len({(r["family"], r["goal_index"], r["tactic"]) for r in rs}) == 270),
        ("every cell carries its goal statement",
         lambda rs: all(r["goal"] for r in rs)),
        ("failed cells are exactly the sorryAx cells",
         lambda rs: all((not r["closed"]) == ("sorryAx" in r["axioms"]) for r in rs)),
        ("no failed cell counts as classical",
         lambda rs: all(r["closed"] for r in rs if r["classical"])),
        # The headline, checked against the cells that render beneath it.
        ("norm_num is classical on all 15 order goals and none of the 12 others",
         lambda rs: (len(closed(rs, tactic="norm_num", shape="order")) == 15
                     and all(r["classical"] for r in closed(rs, tactic="norm_num", shape="order"))
                     and len(closed(rs, tactic="norm_num", shape="equality/divisibility")) == 12
                     and not any(r["classical"] for r in
                                 closed(rs, tactic="norm_num", shape="equality/divisibility")))),
        ("decide, omega and trivial close all 27 goals and none classically",
         lambda rs: all(len(closed(rs, tactic=t)) == 27
                        and not any(r["classical"] for r in closed(rs, tactic=t))
                        for t in ("decide", "omega", "trivial"))),
        ("grind is classical on every goal it closes",
         lambda rs: all(r["classical"] for r in closed(rs, tactic="grind"))),
        ("aesop matches simp cell for cell on all 27 goals",
         lambda rs: all(
             next(r["classical"] for r in rs if r["tactic"] == "aesop"
                  and (r["family"], r["goal_index"]) == g)
             == next(r["classical"] for r in rs if r["tactic"] == "simp"
                     and (r["family"], r["goal_index"]) == g)
             for g in {(r["family"], r["goal_index"]) for r in rs})),
    ],
    based_on="https://doi.org/10.5281/zenodo.21853489",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Why Tactic-Level Rates Cannot Attribute '
        'Classical Dependencies</em>. Zenodo. '
        '<a href="https://doi.org/10.5281/zenodo.21853489">10.5281/zenodo.21853489</a>'),
)

if __name__ == "__main__":
    build(idx)
