"""Check that every number written in prose is derivable from published data.

    python gonzalgo/_build/verify_claims.py            # report
    python gonzalgo/_build/verify_claims.py --strict   # exit 1 on any unverified

The invariants gate each table's rows. Nothing gated the prose around them, and
prose is where the damage has happened: a page said 560 held out when the
arithmetic gave 831, a deposit described eight tables while holding eleven, and
a draft cited a section number that did not exist.

For each index this derives everything the rows can justify -- cell values, row
counts, counts grouped by each categorical column, column sums, subset sums, and
percentages of those against row count and column totals -- then reads the
number out of every sentence on the page and asks whether it is in that set.

A number that is not derivable is not necessarily wrong. It may be quoted from a
paper, which is legitimate and needs a citation. EXTERNAL below is that
register: each entry carries the figure, and where it came from. Anything in
neither place is unverified, and the point of this script is that it says so.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]
G = SITE / "gonzalgo"

# Figures quoted from elsewhere. Each needs a source, because a number with no
# derivation and no citation is a number nobody can check.
EXTERNAL: dict[str, str] = {
    "324808": "reach of Classical.choice in Mathlib — 10.5281/zenodo.21769846",
    "324,808": "reach of Classical.choice in Mathlib — 10.5281/zenodo.21769846",
    "116,766": "theorems reaching lt_or_eq_of_le — 10.5281/zenodo.21883963",
    "116766": "theorems reaching lt_or_eq_of_le — 10.5281/zenodo.21883963",
    "766,564": "constants in the Mathlib graph — 10.5281/zenodo.21883963",
    "790,171": "declarations in the 4.32.1 dump — measured, kernel-index",
    "795,218": "declarations in the 4.33.0 dump — measured, version-delta",
    "30,015,601": "dependency edges — 10.5281/zenodo.21883963",
    "13.1": "eligibility ceiling over Mathlib theorems — 10.5281/zenodo.21884471",
    "78.6": "share of theorems failing eligibility — 10.5281/zenodo.21884471",
    "22.88": "eligibility rate over sites — 10.5281/zenodo.21884471",
    "327,981": "sites after chain collapse — 10.5281/zenodo.21883963",
    "331,009": "constants with a non-empty subtree — 10.5281/zenodo.21883963",
    "60.1": "classically dependent theorems with no responsible site — 21883963",
    "39.9": "complement of 60.1 — 10.5281/zenodo.21883963",
    "0.97": "chain-collapse weight ratio — 10.5281/zenodo.21883963",
    "58": "reach-to-responsibility ratio — 10.5281/zenodo.21883963",
    "2,256": "amplification of Classical.choice in Mathlib — 10.5281/zenodo.21769846",
    "44,501": "theorems inheriting ax-4 — 10.5281/zenodo.21769846",
    "17,898": "entry points in set.mm — 10.5281/zenodo.21769846",
    "1,447": "axioms used in set.mm — 10.5281/zenodo.21769846",
    "46.6": "avoidable rate on the omega subsample — 10.5281/zenodo.21853489",
    "2603.02668": "arXiv id, SorryDB",
    "2606.26442": "arXiv id, AXLE",
    "2606.29493": "arXiv id, Ammanamanchi/Bhat/Biderman",
    "8212": "Lean issue number",
    "4,833": "findings in arXiv:2606.29493",
    "398": "certified issues in arXiv:2606.29493",
    "10,000": "corpus size, Goedel-Prover on Lean Workbook",
    "9,169": "compiled under Lean 4.32 — measured, generated-proofs",
    "4000": "maxErrors CLI value",
    "650": "approximate dump size in MB",
    "600": "approximate dump size in MB",
    "20": "approximate dump time in minutes",
    "100": "Lean's default maxErrors",

    "71,213": "theorems across five Metamath databases — measured, metamath-axioms",
    # Quoted on pages whose own rows do not carry them. Each names where it is
    # checkable; a figure with no derivation and no source is what this catches.
    "3.21": "1,528 choice-dependent of 47,621 set.mm theorems — choice-strength",
    "1.22": "set.mm full-choice share — kernel-index, optional_reach_pct",
    "47,621": "set.mm theorems — kernel-index",
    "60": "modules in the cleanable measurement — cleanable.tsv, lean-work",
    "15": "norm_num order goals closed — controlled-tactics, shape=order",
    "12": "norm_num equality goals closed — controlled-tactics",
    "5.8": "Mathlib known-negative band floor — tactic-bands, band_low_pct",
    "28.2": "Mathlib known-negative band ceiling — tactic-bands, band_high_pct",
    "45.0": "Lean core band floor — tactic-bands, band_low_pct",
    "100.0": "Lean core band ceiling / omega and simp_all rate — tactic-bands",
    "5.0": "norm_num rate in Mathlib loose — tactic-bands",
    "4,892": "Raw.WF.out alone — 10.5281/zenodo.21883963, chain member",
    "4,896": "wfImp_alter alone — 10.5281/zenodo.21883963, chain member",
    "292": "set.mm amplification — entry-points, amplification_as_reported",
    "221": "iset.mm amplification — entry-points",
    "94": "nf.mm amplification — entry-points",
    "93": "share of set.mm reached by ax-4 — setmm-axioms",
    "99.9": "ax-mp share of set.mm — setmm-axioms, share_of_library_pct",
    "0.0": "sorry_real, native_decide and out-of-band axioms — generated-proofs",
    "2.0": "approximate import time in minutes",
    "520": "theorems reaching sorryAx in the corpus — 10.5281/zenodo.21853489",
    "47,672": "set.mm theorems at the pinned revision — metamath-axioms summary",
    "1563": "set.mm assertions at the pinned revision — metamath-axioms summary",
    "16,274": "iset.mm theorems at the pinned revision — metamath-axioms summary",
    "493": "iset.mm assertions at the pinned revision — metamath-axioms summary",
    "5,976": "nf.mm theorems — metamath-axioms summary",
    "1,140": "ql.mm theorems — metamath-axioms summary",
    "10,599": "modules in the 4.33.0 dump — module-spend measured block",
    "7,338": "modules with no direct spend — 10,599 minus 3,261, module-spend",
    "640": "approximate dump size in MB",
    "404": "no-instance verdicts — site-diagnosis",
    "5,338": "byContradiction spends under propDecidable — 10.5281/zenodo.21883963",
    "1,540": "propDecidable spends under itself — 10.5281/zenodo.21883963",
    "91,858": "theorems dominated by Classical.propDecidable — dominator-table",
    "3,008": "set.mm $a statements at the pinned revision — measured",
}

NUM = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+\.\d+\b|\b\d{2,}\b")
IGNORE = {"2026", "2025", "0", "1", "2", "3", "4", "5",
          # toolchain and database versions: metadata, not assertions
          "4.32", "4.33", "4.27", "32.1", "33.0", "27.0"}


def derivable(rows: list[dict]) -> set[str]:
    """Every number these rows can justify."""
    facts: set[float] = set()
    if not rows:
        return set()
    keys = list(rows[0].keys())
    numeric = [k for k in keys
               if any(isinstance(r.get(k), (int, float))
                      and not isinstance(r.get(k), bool) for r in rows)]
    categorical = [k for k in keys
                   if all(isinstance(r.get(k), (str, bool, type(None)))
                          for r in rows)]

    facts.add(len(rows))
    for k in numeric:
        vals = [r[k] for r in rows
                if isinstance(r.get(k), (int, float))
                and not isinstance(r.get(k), bool)]
        facts.update(vals)
        facts.add(sum(vals))
        if vals:
            facts.add(max(vals))
            facts.add(min(vals))
    for c in categorical:
        groups: dict[object, list[dict]] = {}
        for r in rows:
            groups.setdefault(r.get(c), []).append(r)
        for _v, grp in groups.items():
            facts.add(len(grp))
            pct = 100 * len(grp) / len(rows)
            facts.add(round(pct, 1)); facts.add(round(pct, 2))
            for k in numeric:
                vals = [g[k] for g in grp
                        if isinstance(g.get(k), (int, float))
                        and not isinstance(g.get(k), bool)]
                if vals:
                    facts.add(sum(vals))
                    facts.add(len(vals))
    # ratios between column totals, and percentages against them
    totals = {k: sum(r[k] for r in rows
                     if isinstance(r.get(k), (int, float))
                     and not isinstance(r.get(k), bool)) for k in numeric}
    for a in totals.values():
        for b in totals.values():
            if b:
                facts.add(round(100 * a / b, 1))
                facts.add(round(100 * a / b, 2))
                facts.add(round(a / b, 1))
                facts.add(round(a / b))
    out = set()
    for f in facts:
        if f is None:
            continue
        out.add(f"{f:,.0f}" if float(f).is_integer() else f"{f:,}")
        out.add(f"{f:g}")
        if float(f).is_integer():
            out.add(str(int(f)))
    return out


def prose_of(html: str) -> str:
    """The sentences, with everything that carries digits for a reason other
    than making a claim stripped first.

    A DOI, a toolchain string and a date are not assertions a reader could
    check against data. Leaving them in makes the report mostly noise, and a
    report that is mostly noise stops being read, which is the same as not
    having a check at all."""
    p = re.sub(r"<table.*?</table>", " ", html, flags=re.S)
    p = re.sub(r"<script.*?</script>", " ", p, flags=re.S)
    p = re.sub(r"<style.*?</style>", " ", p, flags=re.S)
    p = re.sub(r"<footer.*?</footer>", " ", p, flags=re.S)
    p = re.sub(r"<[^>]+>", " ", p)
    for pattern in (
        r"10\.5281/zenodo\.\d+",
        r"arXiv[:\s]*\d+\.\d+",
        r"https?://\S+",
        r"v?20\d\d-\d\d-\d\d",
        r"CC-BY-4\.0",
        r"#\d+",
        r"Lean\s*4\.\d+(?:\.\d+)?",
        r"Mathlib\s*v?4\.\d+(?:\.\d+)?",
        r"v?\d+\.\d+\.\d+",
        r"4\.\d\d",
        r"version\s+[\w.\-]+",
    ):
        p = re.sub(pattern, " ", p)
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    slugs = sorted(p.name for p in G.iterdir() if (p / f"{p.name}.json").exists())
    unverified_total = 0
    checked_total = 0
    for s in slugs:
        payload = json.loads((G / s / f"{s}.json").read_text(encoding="utf-8"))
        rows = payload["rows"]
        facts = derivable(rows)
        # Values in the published `measured` block are part of the artifact and
        # a reader can check them there, so prose may quote them.
        for v in (payload.get("measured") or {}).values():
            for tok in re.findall(r"[\d,]+", str(v)):
                if tok.strip(","):
                    facts.add(tok); facts.add(tok.replace(",", ""))
        html = (G / s / "index.html").read_text(encoding="utf-8")
        # "Showing the first 120 of 3,004 rows" is a display setting.
        html = re.sub(r"Showing the first[^<]*", " ", html)
        prose = prose_of(html)
        found = [n for n in NUM.findall(prose) if n not in IGNORE]
        bad = []
        for n in dict.fromkeys(found):
            plain = n.replace(",", "")
            if n in facts or plain in facts or n in EXTERNAL or plain in EXTERNAL:
                continue
            bad.append(n)
        checked_total += len(set(found))
        unverified_total += len(bad)
        flag = "ok  " if not bad else "FLAG"
        print(f"  {flag} {s:<21} {len(set(found)):>3} claims, "
              f"{len(bad):>2} unverified"
              + (f"  -> {', '.join(bad[:8])}" if bad else ""))

    print(f"\n  {checked_total} numeric claims checked, "
          f"{unverified_total} not derivable and not cited")
    if args.strict and unverified_total:
        sys.exit(1)


if __name__ == "__main__":
    main()
