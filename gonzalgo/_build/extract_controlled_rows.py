"""Build data/controlled-tactic-rows.json from the deposited archive.

    python gonzalgo/_build/extract_controlled_rows.py

Source: dominator-analysis-code.zip, attached to 10.5281/zenodo.21883963.
`lean/Controlled.lean` is the generated experiment — one goal per row, one tactic
per column — and `data/controlled_out.txt` is what Lean printed running it.

The goal statement is joined back on from the Lean source, because a table of
cell names is not readable and the point of the experiment is that the goal is
held fixed while the tactic varies.

A cell whose axiom set contains sorryAx is the tactic failing to close the goal,
not a proof resting on something unfinished. Those are marked `failed` and are
excluded from every rate, since a tactic that did not run cannot have introduced
an axiom.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = Path(r"C:\Users\Admin\OneDrive\Desktop\PAPER-dominators"
               r"\dominator-analysis-code.zip")

z = zipfile.ZipFile(ARCHIVE)
source = z.read("lean/Controlled.lean").decode("utf-8")
output = z.read("data/controlled_out.txt").decode("utf-8")

# theorem c_le_nat_0_norm_num : (3 : Nat) <= 5 := by norm_num
goals = {}
for m in re.finditer(r"^theorem\s+(c_\S+)\s*:\s*(.+?)\s*:=\s*by\s+(\S+)\s*$",
                     source, re.M):
    goals[m.group(1)] = (m.group(2), m.group(3))

cell = re.compile(
    r"'(c_(.+?)_(\d+)_([A-Za-z_0-9']+))' "
    r"(?:depends on axioms: \[(.*?)\]|does not depend on any axioms)")

# Order goals are the comparisons; the boundary the experiment found runs
# between these and the equality/divisibility families.
ORDER = {"le_nat", "lt_nat", "ge_nat", "le_int", "lt_int"}

rows = []
for m in cell.finditer(output):
    name, family, index, tactic = m.group(1), m.group(2), int(m.group(3)), m.group(4)
    axioms = [a.strip() for a in (m.group(5) or "").split(",") if a.strip()]
    statement, declared = goals.get(name, (None, None))
    assert declared in (None, tactic), f"{name}: source says {declared}"
    failed = "sorryAx" in axioms
    rows.append({
        "family": family,
        "goal_index": index,
        "goal": statement,
        "shape": "order" if family in ORDER else "equality/divisibility",
        "tactic": tactic,
        "closed": not failed,
        "classical": (not failed) and "Classical.choice" in axioms,
        "axioms": " ".join(axioms) if axioms else "(none)",
    })

rows.sort(key=lambda r: (r["family"], r["goal_index"], r["tactic"]))

out = HERE / "data" / "controlled-tactic-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

fams = sorted({r["family"] for r in rows})
tacs = sorted({r["tactic"] for r in rows})
closed = [r for r in rows if r["closed"]]
print(f"  wrote {out.name}: {len(rows)} cells")
print(f"  {len(fams)} families x 3 goals x {len(tacs)} tactics")
print(f"  closed {len(closed)}, failed {len(rows) - len(closed)}, "
      f"classical {sum(1 for r in closed if r['classical'])}")
print(f"  goal statements joined: {sum(1 for r in rows if r['goal'])}/{len(rows)}")
