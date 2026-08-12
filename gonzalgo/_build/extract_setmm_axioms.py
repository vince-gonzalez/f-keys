"""Build data/setmm-axioms-rows.json — every axiomatic assertion in set.mm.

    python gonzalgo/_build/extract_setmm_axioms.py

Source: closure.pkl from the Metamath run — `clos` maps each of set.mm's 47,621
theorems to the frozenset of axiomatic assertions its proof reaches, `kind` gives
each label's Metamath statement kind.

set.mm's `$a` statements are three different things sharing one mechanism, and
mixing them makes any count meaningless:

  axiom       ax-*   a logical or set-theoretic assumption
  definition  df-*   a definition, eliminable in principle
  syntax      other  a well-formedness constructor, wi wn wb wa, carrying no
                     mathematical content at all

The paper's "axioms used: 1,447" for set.mm is axioms plus definitions and
excludes the 1,344 syntax constructors; that identity is asserted below rather
than described, so it breaks if either number moves.
"""
from __future__ import annotations

import collections
import json
import pickle
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLOSURE = Path(r"C:\Users\Admin\OneDrive\Desktop\universal-cover\axioms\closure.pkl")

d = pickle.loads(CLOSURE.read_bytes())
clos, kind = d["clos"], d["kind"]
theorems = len(clos)

dependents = collections.Counter()
for reached in clos.values():
    for label in reached:
        dependents[label] += 1


def classify(label: str) -> str:
    if label.startswith("ax-"):
        return "axiom"
    if label.startswith("df-"):
        return "definition"
    return "syntax constructor"


rows = []
for label, k in kind.items():
    if k != "a":                       # $a only: $p are theorems, $e hypotheses
        continue
    n = dependents.get(label, 0)
    rows.append({
        "label": label,
        "role": classify(label),
        "dependents": n,
        "share_of_library_pct": round(100 * n / theorems, 2),
    })

rows.sort(key=lambda r: (-r["dependents"], r["label"]))

out = HERE / "data" / "setmm-axioms-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

by_role = collections.Counter(r["role"] for r in rows)
unused = [r for r in rows if r["dependents"] == 0]
print(f"  wrote {out.name}: {len(rows):,} axiomatic assertions over "
      f"{theorems:,} theorems")
print("  by role:", dict(by_role))
print(f"  axioms + definitions = "
      f"{by_role['axiom'] + by_role['definition']:,}  "
      f"(the paper's 'axioms used' for set.mm)")
print(f"  declared and never reached: {len(unused)}")
print(f"  top: " + ", ".join(f"{r['label']} {r['dependents']:,}" for r in rows[:4]))
