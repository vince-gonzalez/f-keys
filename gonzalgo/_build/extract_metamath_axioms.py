"""Build data/metamath-axioms-rows.json — every axiomatic assertion, five databases.

    python gonzalgo/_build/extract_metamath_axioms.py

Covers set.mm, iset.mm, nf.mm, ql.mm and hol.mm: ZFC, intuitionistic logic,
New Foundations, quantum logic and higher-order logic, measured by one engine.

Classification is by TYPECODE, not by name. A `$a` beginning `|-` asserts
something; one beginning `class`, `wff`, `term` or `type` is a well-formedness
constructor carrying no mathematical content. The `ax-`/`df-` prefix rule is a
set.mm house style — it agrees with the typecode on all 3,008 of set.mm's `$a`
statements and would misclassify ql.mm and hol.mm outright, since those use
`term` and `type` typecodes and different naming.

The source revision is recorded. The earlier per-database tables did not carry
one, and in the interval iset.mm gained 38 theorems and set.mm gained 4 `$a`
statements — so those figures cannot be reproduced exactly, which is what rule
R1 of the Kernel Trust Profile exists to prevent.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\Admin\OneDrive\Desktop\universal-cover\axioms")
import mmclosure  # noqa: E402

HERE = Path(__file__).resolve().parent
MM = Path(r"C:\Users\Admin\AppData\Local\Temp\claude"
          r"\C--Users-Admin-OneDrive-Desktop-Pro-Categories-Application-Prompt"
          r"\d97a5831-1ba4-43e9-9665-35367561fe9c\scratchpad\mm")

# github.com/metamath/set.mm @ develop, fetched 2026-08-13
REVISION = "7ddd528c948ae375618ad1ca476b28b9a0eec7d6"

FOUNDATION = {
    "set.mm":  "ZFC, classical first-order",
    "iset.mm": "intuitionistic",
    "nf.mm":   "Quine's New Foundations",
    "ql.mm":   "quantum logic",
    "hol.mm":  "higher-order logic",
}


def typecodes(path: Path) -> dict[str, str]:
    """label -> the typecode its $a statement opens with."""
    tc: dict[str, str] = {}
    it = mmclosure.tokens(path)
    label = None
    for t in it:
        if t == "$a":
            first = next(it, None)
            if label:
                tc[label] = first
            for u in it:
                if u == "$.":
                    break
            label = None
        elif t.startswith("$"):
            if t in ("$p", "$e", "$f"):
                for u in it:
                    if u == "$.":
                        break
            label = None
        else:
            label = t
    return tc


rows = []
summary = {}
for db in ("set.mm", "iset.mm", "nf.mm", "ql.mm", "hol.mm"):
    path = MM / db
    data = mmclosure.load(path)
    kind, clos, refs = data["kind"], data["clos"], data["refs"]
    tc = typecodes(path)
    theorems = [l for l, k in kind.items() if k == "p"]

    dependents = collections.Counter()
    for t in theorems:
        for a in clos[t]:
            dependents[a] += 1
    entry = collections.Counter()
    for t in theorems:
        for r in set(refs[t]):
            if kind.get(r) == "a":
                entry[r] += 1

    n_thm = len(theorems)
    for label, k in kind.items():
        if k != "a":
            continue
        code = tc.get(label, "?")
        n = dependents.get(label, 0)
        rows.append({
            "database": db,
            "foundation": FOUNDATION[db],
            "label": label,
            "typecode": code,
            "role": "assertion" if code == "|-" else "syntax constructor",
            "dependents": n,
            "share_of_db_pct": round(100 * n / n_thm, 2) if n_thm else 0.0,
            "entry_points": entry.get(label, 0),
        })
    summary[db] = {
        "theorems": n_thm,
        "a_statements": sum(1 for l, k in kind.items() if k == "a"),
        "assertions": sum(1 for l, k in kind.items()
                          if k == "a" and tc.get(l) == "|-"),
        "incomplete_proofs": len(data["incomplete"]),
        "entry_points_total": sum(entry.values()),
    }
    print(f"  {db:<9} theorems {n_thm:>6,}  $a {summary[db]['a_statements']:>5,}"
          f"  assertions {summary[db]['assertions']:>5,}"
          f"  incomplete {summary[db]['incomplete_proofs']}")

order = {"set.mm": 0, "iset.mm": 1, "nf.mm": 2, "ql.mm": 3, "hol.mm": 4}
rows.sort(key=lambda r: (order[r["database"]], -r["dependents"], r["label"]))

for r in rows:
    r["source_revision"] = REVISION

out = HERE / "data" / "metamath-axioms-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
(HERE / "data" / "metamath-axioms-summary.json").write_text(
    json.dumps({"revision": REVISION, "databases": summary}, indent=2),
    encoding="utf-8")

print(f"\n  wrote {out.name}: {len(rows):,} axiomatic assertions across "
      f"{len(summary)} databases")
print(f"  revision {REVISION[:12]}")
print(f"  incomplete proofs anywhere: "
      f"{sum(s['incomplete_proofs'] for s in summary.values())}")
