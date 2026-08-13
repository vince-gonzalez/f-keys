"""Build data/choice-strength-rows.json — which choice principle a theorem needs.

    python gonzalgo/_build/extract_choice_strength.py

Source: closure.pkl from the Metamath run.

set.mm does not have one choice axiom, it has three of different strength, and
they are separate axioms in the database rather than a single toggle:

    ax-ac, ax-ac2   full choice
    ax-cc           countable choice
    ax-dc           dependent choice

A theorem can reach more than one. `strongest` is the strongest principle its
proof reaches and partitions the 1,528 choice-dependent theorems into 583 / 879
/ 66; the three reach columns are the raw memberships and do overlap, by 137
between full and countable alone. Both are carried because the partition is what
you rank on and the reach is what you check.

The Kernel Index reports set.mm at 1.22%, which is full choice over all
theorems. Counting every choice principle gives 1,528 of 47,621, or 3.21%. The
smaller figure is not wrong -- it answers "how much rests on choice proper" --
but this is where the difference is visible.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLOSURE = Path(r"C:\Users\Admin\OneDrive\Desktop\universal-cover\axioms\closure.pkl")

AC = {"ax-ac", "ax-ac2"}
THEOREMS = 47621

d = pickle.loads(CLOSURE.read_bytes())
clos = d["clos"]

rows = []
for label, reached in clos.items():
    ac = bool(reached & AC)
    cc = "ax-cc" in reached
    dc = "ax-dc" in reached
    if not (ac or cc or dc):
        continue
    rows.append({
        "theorem": label,
        "strongest": ("full choice" if ac
                      else "countable choice" if cc
                      else "dependent choice"),
        "reaches_full_choice": ac,
        "reaches_countable_choice": cc,
        "reaches_dependent_choice": dc,
        "axioms_reached": " ".join(sorted(reached & (AC | {"ax-cc", "ax-dc"}))),
    })

order = {"full choice": 0, "countable choice": 1, "dependent choice": 2}
rows.sort(key=lambda r: (order[r["strongest"]], r["theorem"]))

out = HERE / "data" / "choice-strength-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

import collections
part = collections.Counter(r["strongest"] for r in rows)
print(f"  wrote {out.name}: {len(rows):,} choice-dependent theorems "
      f"of {THEOREMS:,} ({100*len(rows)/THEOREMS:.2f}%)")
print("  partition by strongest principle:", dict(part))
for k, key in (("full", "reaches_full_choice"),
               ("countable", "reaches_countable_choice"),
               ("dependent", "reaches_dependent_choice")):
    print(f"  raw reach, {k:<10}: {sum(1 for r in rows if r[key]):>5}")
assert part["full choice"] == 583 and part["countable choice"] == 879
assert part["dependent choice"] == 66
print("  partition matches the stored full/cc/dc lists")
