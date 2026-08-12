"""The Tactic Background Table — every rate against the band that calibrates it.

    python gonzalgo/_build/extract_tactic_bands.py
    python gonzalgo/_build/mk_tactic_bands.py
"""
from __future__ import annotations

import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "tactic-band-rows.json").read_text(encoding="utf-8"))


def cell(lib, mode, tactic, key="rate_pct"):
    return next(r[key] for r in rows
                if r["library"] == lib and r["attribution"] == mode
                and r["tactic"] == tactic)


ESCAPES = [r for r in rows if r["escapes_band"] and r["role"] == "candidate"]
UNEXAMINED = [r for r in rows if r["escapes_band"] and r["role"] == "not examined"]

idx = Index(
    slug="tactic-bands",
    title="The Tactic Background Table",
    kicker="every rate, against the band that says whether it means anything",
    meta_title="The Tactic Background Table — Lean tactic classical-dependence rates and their calibration",
    meta_description=(
        "Classical-dependence rates for Lean tactics across four libraries and two "
        "attribution rules, each against the band spanned by tactics that cannot "
        "introduce a classical instance. The background is 5.8-28.2% in Mathlib and "
        "45.0-100.0% in Lean core."),
    description=(
        "Rates at which Lean tactics' proofs carry an avoidable classical dependence, "
        "across four libraries under two attribution rules, each shown against the "
        "band spanned by known-negative tactics in the same library and rule. The "
        "band is what makes a rate interpretable, and it is wide."),
    lede=[
        "Scoring a tactic by how often its proofs carry a removable dependence on "
        "choice looks like it should find the tactics at fault. The number it "
        "produces is mostly a property of the theorems the tactic gets used on.",
        "The calibration is the whole table. A <em>known-negative</em> is a tactic "
        "that cannot introduce a classical instance at all — <code>rfl</code>, "
        "<code>intro</code>, <code>exfalso</code> — so whatever rate it shows is the "
        "background of its population. In Mathlib that background spans "
        f"{cell('Mathlib','loose','rfl','band_low_pct')}&ndash;"
        f"{cell('Mathlib','loose','rfl','band_high_pct')}% across 30 controls; in "
        f"Lean core {cell('Init','loose','rfl','band_low_pct')}&ndash;"
        f"{cell('Init','loose','rfl','band_high_pct')}%. The variation inside one "
        "library is as large as the variation between libraries, so no threshold "
        "survives normalisation.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 &middot; four libraries, two attribution rules, cells with '
        'at least 20 proofs'),
    columns=[
        Column("library", "library"),
        Column("attribution", "rule", dim=True),
        Column("tactic", "tactic"),
        Column("role", "role", dim=True),
        Column("proofs", "proofs", align="right"),
        Column("classical", "classical", align="right"),
        Column("eligible", "eligible", align="right"),
        Column("rate_pct", "rate", align="right", pct=True),
        Column("position", "vs band"),
    ],
    rows=rows,
    measured={
        "Lean 4": "4.32.1 with Mathlib v4.32.1",
        "libraries": "Mathlib, Init, Std, Batteries",
        "threshold": "cells with at least 20 proofs",
    },
    notes=(
        "<em>rate</em> is eligible over classical: of the proofs using this tactic "
        "that depend on <code>Classical.choice</code>, the share whose statement is "
        "choice-free, so the proof introduced the dependence. <em>rule</em> is how a "
        "proof is attributed &mdash; <code>strict</code> counts only proofs where "
        "the tactic is the sole tactic, <code>loose</code> counts every proof it "
        "appears in. <em>role</em> marks whether a tactic is a known-negative "
        "control, one of the 15 candidates the paper tests, or a tactic that was "
        "measured but never examined."),
    sections=[
        ("What escapes, and why it does not help", [
            f"{len(ESCAPES)} of the examined candidates rise above their own "
            "library's band. Four of the seven are <code>grind</code>, which proves "
            "by refuting the negation and is therefore classical by construction "
            "rather than by defect. One is <code>omega</code>, whose avoidable "
            "dependence is real and independently established &mdash; and "
            "<code>simp_all</code> ties it at exactly 100.0% in the same library "
            "under the same rule, so even there the rate does not single it out.",
            f"<code>norm_num</code> carries a genuinely avoidable dependence, "
            "demonstrated by direct construction in the "
            "<a href=\"/gonzalgo/controlled-tactics/\">controlled experiment</a>. "
            f"It sits at {cell('Mathlib','loose','norm_num')}% in Mathlib, below the "
            "known-negative floor, beneath <code>rfl</code> and "
            "<code>exfalso</code> and every other tactic that cannot introduce "
            "choice at all. The instrument ranks the one tactic with a proven defect "
            "beneath tactics incapable of the defect.",
            "Widening the rule does not rescue it. Under <code>strict</code>, "
            "<code>induction</code> reaches 87.5% and widens Mathlib's band until "
            "nothing escapes at all. The instrument either fires on the wrong tactic "
            "or does not fire.",
        ]),
        ("One cell the paper did not test", [
            "The published count of seven is over the 15 candidate tactics its script "
            "examines. Rates were computed for every tactic meeting the threshold, "
            "and one more escapes: "
            + ", ".join(f"<code>{r['tactic']}</code> in {r['library']} under "
                        f"{r['attribution']} at {r['rate_pct']}% against a "
                        f"{r['band_high_pct']}% band, over {r['proofs']:,} proofs"
                        for r in UNEXAMINED)
            + ". It is neither a known-negative nor on the candidate list, so nothing "
            "in the pipeline looked at it.",
            "It does not disturb the conclusion — an extra escape that nobody has a "
            "mechanism for is more evidence that the rate is not selecting on "
            "defectiveness — but it is in the data and belongs on the page rather "
            "than in a drawer.",
        ]),
        ("Why the unit is wrong, not just the statistic", [
            "In the generated corpus <code>interval_cases</code> scores 100%. Its "
            "proofs close with <code>&lt;;&gt; norm_num</code>, and the score belongs "
            "to norm_num. A surface tactic inherits the axiom behaviour of whatever "
            "it delegates to, so attributing a proof to the tactic named in it is "
            "the wrong unit regardless of which statistic is computed over it. That "
            "is the finding this table exists to support.",
        ]),
    ],
    reproduce=["python analysis/final_table.py"],
    reproduce_note=(
        "Code and derived data: "
        "<a href=\"https://doi.org/10.5281/zenodo.21853489\">"
        "10.5281/zenodo.21853489</a>. The bands here are recomputed from the cells "
        "and checked against the ones the archive stores, so a row and its band "
        "cannot come from different runs."),
    keywords=["Lean 4", "Mathlib", "tactics", "grind", "omega", "norm_num",
              "axiom of choice", "calibration", "known-negative controls",
              "formal verification", "negative result"],
    invariants=[
        ("every rate recomputes as eligible over classical",
         lambda rs: all(r["classical"] == 0
                        or abs(round(100 * r["eligible"] / r["classical"], 1)
                               - r["rate_pct"]) <= 0.05 for r in rs)),
        ("eligible never exceeds classical, which never exceeds proofs",
         lambda rs: all(r["eligible"] <= r["classical"] <= r["proofs"] for r in rs)),
        ("every cell meets the 20-proof threshold",
         lambda rs: all(r["proofs"] >= 20 for r in rs)),
        ("each row's position agrees with its own rate and band",
         lambda rs: all(r["position"] == ("above band" if r["rate_pct"] > r["band_high_pct"]
                                          else "below band" if r["rate_pct"] < r["band_low_pct"]
                                          else "inside band") for r in rs)),
        ("no known-negative is ever counted as an escape",
         lambda rs: not any(r["escapes_band"] for r in rs
                            if r["role"] == "known-negative")),
        # The published figures, checked against the rows that render beneath them.
        ("Mathlib's loose band is 5.8-28.2% from 30 controls, widest exfalso",
         lambda rs: all((r["band_low_pct"], r["band_high_pct"],
                         r["controls_in_band"], r["band_widest"])
                        == (5.8, 28.2, 30, "exfalso") for r in rs
                        if r["library"] == "Mathlib" and r["attribution"] == "loose")),
        ("Lean core's loose band is 45.0-100.0%, widest trivial",
         lambda rs: all((r["band_low_pct"], r["band_high_pct"], r["band_widest"])
                        == (45.0, 100.0, "trivial") for r in rs
                        if r["library"] == "Init" and r["attribution"] == "loose")),
        ("exactly 7 of the paper's candidates escape, 4 of them grind",
         lambda rs: (lambda e: len(e) == 7
                     and sum(1 for r in e if r["tactic"] == "grind") == 4)(
             [r for r in rs if r["escapes_band"] and r["role"] == "candidate"])),
        ("omega and simp_all tie at 100.0% in Init strict",
         lambda rs: [next(r["rate_pct"] for r in rs if r["library"] == "Init"
                          and r["attribution"] == "strict" and r["tactic"] == t)
                     for t in ("omega", "simp_all")] == [100.0, 100.0]),
        ("norm_num sits below Mathlib's known-negative floor",
         lambda rs: next(r["position"] for r in rs if r["library"] == "Mathlib"
                         and r["attribution"] == "loose"
                         and r["tactic"] == "norm_num") == "below band"),
        ("exactly one escaping cell was never examined by the paper",
         lambda rs: sum(1 for r in rs if r["escapes_band"]
                        and r["role"] == "not examined") == 1),
    ],
    based_on="https://doi.org/10.5281/zenodo.21853489",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Why Tactic-Level Rates Cannot Attribute '
        'Classical Dependencies</em>. Zenodo. '
        '<a href="https://doi.org/10.5281/zenodo.21853489">10.5281/zenodo.21853489</a>'),
)

if __name__ == "__main__":
    build(idx)
