"""The Metamath Axiom Table — five foundations, one engine, one revision.

    python gonzalgo/_build/extract_metamath_axioms.py
    python gonzalgo/_build/mk_metamath_axioms.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from indexlib import Column, Index, build

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "data" / "metamath-axioms-rows.json").read_text(encoding="utf-8"))
summary = json.loads((HERE / "data" / "metamath-axioms-summary.json").read_text(encoding="utf-8"))
DBS = summary["databases"]
REV = summary["revision"]
THMS = sum(d["theorems"] for d in DBS.values())


def top(db):
    return max((r for r in rows if r["database"] == db),
               key=lambda r: r["dependents"])


idx = Index(
    slug="metamath-axioms",
    title="The Metamath Axiom Table",
    kicker="five foundations, one engine, one pinned revision",
    meta_title="The Metamath Axiom Table — every axiomatic assertion across five foundations",
    meta_description=(
        "All 4,424 axiomatic assertions in set.mm, iset.mm, nf.mm, ql.mm and "
        "hol.mm — ZFC, intuitionistic logic, New Foundations, quantum logic and "
        "higher-order logic — with the theorems depending on each. Classified by "
        "typecode rather than by name, and pinned to a source revision."),
    description=(
        "Every $a statement across five Metamath databases spanning five "
        "foundations, with the number of that database's theorems whose proof "
        "closure reaches it and the number citing it directly. Assertions are "
        "separated from well-formedness constructors by typecode."),
    lede=[
        f"Five databases, {THMS:,} theorems, one closure engine. The comparison "
        "is only possible because the same program reads all five; a measure "
        "computed by five different tools would be five measures.",
        "Assertions are separated from syntax constructors by <strong>typecode</strong>, "
        "not by name. A <code>$a</code> beginning <code>|-</code> asserts "
        "something; one beginning <code>class</code>, <code>wff</code>, "
        "<code>term</code> or <code>type</code> says a piece of notation is "
        "well formed and carries no mathematical content. Counting them together "
        "makes every total meaningless.",
    ],
    provenance=(
        'Measured with <a href="/gonzalgo/">gonzalgo</a>\'s closure engine '
        '&middot; github.com/metamath/set.mm @ <code>'
        + REV[:12] + '</code>, fetched 2026-08-13 &middot; '
        f'{THMS:,} theorems across five databases'),
    columns=[
        Column("database", "database"),
        Column("label", "label"),
        Column("role", "role", dim=True),
        Column("typecode", "typecode", dim=True),
        Column("dependents", "theorems depending", align="right"),
        Column("share_of_db_pct", "share of db", align="right", pct=True),
        Column("entry_points", "entry points", align="right"),
    ],
    rows=rows,
    row_limit=120,
    row_limit_note="Ordered by database, then by dependents.",
    measured={
        "databases": "set.mm, iset.mm, nf.mm, ql.mm, hol.mm",
        "revision": REV,
        "fetched": "2026-08-13",
    },
    notes=(
        "<em>dependents</em> counts theorems in that database whose proof closure "
        "reaches the statement, including everything inherited. <em>entry "
        "points</em> counts theorems whose own proof cites it directly. "
        "<em>share of db</em> is dependents over that database's own theorem "
        "count, so rows from different databases are comparable."),
    sections=[
        ("Not one incomplete proof, anywhere", [
            "Across all five databases and "
            f"{THMS:,} theorems, the number whose proof contains a <code>?</code> "
            "step is zero. Metamath marks an incomplete proof explicitly, so this "
            "is a check rather than an assumption, and it is the claim most worth "
            "making about a formal library.",
        ]),
        ("Why the typecode and not the name", [
            "<code>set.mm</code> names its axioms <code>ax-</code> and its "
            "definitions <code>df-</code>, and that rule agrees with the typecode "
            "on all 3,008 of its <code>$a</code> statements &mdash; checked, not "
            "assumed. It is still a house style. <code>ql.mm</code> and "
            "<code>hol.mm</code> use <code>term</code> and <code>type</code> "
            "typecodes with different naming, and a set.mm-trained prefix rule "
            "misclassifies them outright.",
            "This is the general point about measuring several libraries with one "
            "instrument: the convention you learned from the biggest one is not a "
            "property of the format.",
        ]),
        ("Why the revision is on the page", [
            "These databases move. Measured today, <code>iset.mm</code> has 38 "
            "more theorems and <code>set.mm</code> four more <code>$a</code> "
            "statements than when the earlier tables here were built, and those "
            "tables recorded no revision &mdash; so their figures cannot be "
            "reproduced exactly, only approximately.",
            "Rule R1 of the <a href=\"/gonzalgo/kernel-trust/\">Kernel Trust "
            "Profile</a> exists for this: every number must be derivable by a "
            "third party from a named revision. This table names one.",
        ]),
        ("The foundations, side by side", [
            " &middot; ".join(
                f"<strong>{db}</strong> {d['theorems']:,} theorems, "
                f"{d['assertions']} assertions, {d['a_statements']} $a"
                for db, d in DBS.items()),
            "The largest single dependency in each: "
            + ", ".join(f"<code>{top(db)['label']}</code> at "
                        f"{top(db)['share_of_db_pct']}% of {db}" for db in DBS),
        ]),
    ],
    reproduce=["pip install gonzalgo",
               "gonzalgo mm set.mm iset.mm nf.mm ql.mm hol.mm"],
    reproduce_note=(
        f"Databases from github.com/metamath/set.mm at <code>{REV[:12]}</code>. "
        "Method: <a href=\"https://doi.org/10.5281/zenodo.21769846\">"
        "10.5281/zenodo.21769846</a>."),
    keywords=["Metamath", "set.mm", "iset.mm", "New Foundations", "quantum logic",
              "higher-order logic", "intuitionistic logic", "axioms",
              "foundations of mathematics", "formal verification"],
    invariants=[
        ("all five databases are present",
         lambda rs: {r["database"] for r in rs}
         == {"set.mm", "iset.mm", "nf.mm", "ql.mm", "hol.mm"}),
        ("every row is an assertion or a syntax constructor, by typecode",
         lambda rs: all((r["role"] == "assertion") == (r["typecode"] == "|-")
                        for r in rs)),
        ("every row carries the source revision",
         lambda rs: all(r["source_revision"] == REV for r in rs)),
        ("dependents never exceed the database's theorem count",
         lambda rs: all(r["dependents"] <= DBS[r["database"]]["theorems"]
                        for r in rs)),
        ("every share recomputes against its own database",
         lambda rs: all(abs(round(100 * r["dependents"]
                                  / DBS[r["database"]]["theorems"], 2)
                            - r["share_of_db_pct"]) <= 0.01 for r in rs)),
        ("no database contains an incomplete proof",
         lambda rs: all(d["incomplete_proofs"] == 0 for d in DBS.values())),
        ("the assertion counts match the per-database summary",
         lambda rs: all(
             sum(1 for r in rs if r["database"] == db and r["role"] == "assertion")
             == d["assertions"] for db, d in DBS.items())),
    ],
    based_on="https://doi.org/10.5281/zenodo.21769846",
    citation=(
        'Cite: Gonzalez, V. (2026). <em>Where Formal Libraries Spend Their Axioms</em>. '
        'Zenodo. <a href="https://doi.org/10.5281/zenodo.21769846">'
        '10.5281/zenodo.21769846</a>'),
)

if __name__ == "__main__":
    build(idx)
