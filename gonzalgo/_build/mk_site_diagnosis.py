"""The Site Diagnosis Table — why a classical site could not be cleaned.

    python gonzalgo/_build/extract_site_diagnosis.py
    python gonzalgo/_build/mk_site_diagnosis.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "site-diagnosis-rows.json").read_text(encoding="utf-8"))

C = collections.Counter(r["verdict"] for r in rows)
N = len(rows)


def pct(k):
    return round(100 * C[k] / N, 1)


idx = Index(
    slug="site-diagnosis",
    title="The Site Diagnosis Table",
    kicker="the sites that did not come out, and what stopped each one",
    meta_title="The Site Diagnosis Table — why classical dependencies in Lean resist removal",
    meta_description=(
        "765 sites of classical dependence in Lean examined for removal, with the "
        "reason each resisted: 395 had no Decidable instance, 340 were not in an "
        "instance position at all, 18 needed choice anyway, 12 timed out."),
    description=(
        "Sites of classical dependence in Lean 4 examined for constructive "
        "replacement and not removed, each with the reason: no instance could be "
        "synthesised, the occurrence was not in a position where an instance is "
        "supplied, the available instance itself depends on choice, or synthesis "
        "timed out."),
    lede=[
        "The <a href=\"/gonzalgo/cleanable/\">Cleanable Table</a> lists what came "
        "out. On its own that is a numerator with no denominator, and a numerator "
        "with no denominator is how a removal rate gets quoted as though it were a "
        "possibility rate. This is the rest.",
        f"Of {N} sites examined, {C['not-a-goal']} &mdash; {pct('not-a-goal')}% "
        "&mdash; were never testable. The occurrence is not in a position where an "
        "instance would be supplied, so there is no proposition to hand to "
        "synthesis and nothing to substitute. That is a fact about the shape of the "
        "proof term rather than about whether the mathematics needs choice.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a> &middot; Lean 4.32.1 with '
        'Mathlib v4.32.1 &middot; instance synthesis attempted per occurrence, '
        'inside the declaration\'s own context'),
    columns=[
        Column("verdict", "verdict"),
        Column("meaning", "what stopped it", dim=True),
        Column("library", "library"),
        Column("declaration", "declaration"),
        Column("proposition", "proposition", dim=True),
    ],
    rows=rows,
    row_limit=120,
    row_limit_note="Grouped by verdict, so the head of the table is one category.",
    measured={
        "Lean 4": "4.32.1 with Mathlib v4.32.1",
        "target": "Classical.propDecidable",
        "sites": N,
    },
    notes=(
        "<em>proposition</em> is the goal an instance would have had to be found "
        "for, where there was one. A <code>not-a-goal</code> row often shows "
        "<code>Classical.propDecidable</code> bare or partly applied, which is the "
        "case where there is nothing to decide."),
    sections=[
        ("What the four verdicts mean for a repair", [
            f"<strong>no instance</strong> ({C['no-instance']}, {pct('no-instance')}%) "
            "is the honest negative: the proposition is there, synthesis was asked, "
            "and Lean has no constructive way to decide it. These are the sites "
            "where the classical dependence is doing real work.",
            f"<strong>not an instance position</strong> ({C['not-a-goal']}, "
            f"{pct('not-a-goal')}%) is not a negative at all. Nothing was tested. "
            "Counting these as failures understates removability and counting them "
            "as successes overstates it, which is why they are their own category "
            "rather than folded into either.",
            f"<strong>needs choice anyway</strong> ({C['choice-needed']}) is the "
            "sharpest case: an instance exists, and it depends on choice itself, so "
            "substituting it moves the dependence rather than removing it. Any "
            "measure that stops at whether an instance exists would score these as "
            "wins.",
            f"<strong>timed out</strong> ({C['timeout']}) is unknown, not negative. "
            "It is small here, which is the improvement this run represents.",
        ]),
        ("Why an earlier pass is not used", [
            "A previous run over the same question returned 404 synthesis timeouts "
            "against this run's 12, and had no <code>not-a-goal</code> category at "
            "all, so nearly every site it could not clean was recorded as a time "
            "limit being hit. It was measuring its own budget. Its numbers are not "
            "reproduced here.",
        ]),
        ("Reading it with the Cleanable Table", [
            "Together the two tables give the shape of the problem rather than a "
            "single rate. Removal succeeded where a decidable proposition sat in an "
            "instance position and the constructive instance existed. Where any of "
            "those three fails it fails for a different reason, and only one of the "
            "three is about mathematics.",
        ]),
    ],
    reproduce=["lake env lean -D maxErrors=4000 lean/Substitute.lean"],
    reproduce_note=(
        "Method: <a href=\"https://doi.org/10.5281/zenodo.21769846\">"
        "10.5281/zenodo.21769846</a>."),
    keywords=["Lean 4", "Mathlib", "Classical.propDecidable", "Decidable",
              "instance synthesis", "axiom of choice",
              "constructive mathematics", "formal verification",
              "negative result"],
    invariants=[
        (f"{N} sites, and the four verdicts partition them",
         lambda rs: len(rs) == 765
         and dict(collections.Counter(r["verdict"] for r in rs))
         == {"no-instance": 395, "not-a-goal": 340, "choice-needed": 18,
             "timeout": 12}),
        ("every verdict carries its plain-language meaning, consistently",
         lambda rs: len({(r["verdict"], r["meaning"]) for r in rs}) == 4),
        ("every row names a library, module and declaration",
         lambda rs: all(r["library"] and r["module"] and r["declaration"]
                        for r in rs)),
        ("the library is the first component of the module path",
         lambda rs: all(r["module"].split(".")[0] == r["library"] for r in rs)),
        ("every row that was actually tested names a proposition",
         lambda rs: all(r["proposition"] for r in rs
                        if r["verdict"] in ("no-instance", "choice-needed"))),
        ("the untestable share quoted in the lede is 44.4%",
         lambda rs: abs(100 * sum(1 for r in rs if r["verdict"] == "not-a-goal")
                        / len(rs) - 44.4) <= 0.05),
    ],
    based_on="https://doi.org/10.5281/zenodo.21769846",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
