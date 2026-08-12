"""Build data/substitution-rows.json from the deposited reproduction archive.

    python gonzalgo/_build/extract_substitution.py

Source: dominator-analysis-code.zip, attached to 10.5281/zenodo.21883963.
`data/substitution_out.txt` is what Lean printed; `data/subst_targets.json`
carries each target's dominance and its route to the axiom.

The four counts per declaration narrow in sequence:

  occurrences   uses of Classical.propDecidable in the declaration's proof term
  testable      those the harness could reach — an occurrence under a binder
                cannot be tested outside its declaration's context
  synthesised   those where a Decidable instance was found for the proposition
  choice-free   those where the substituted term was accepted by the KERNEL

choice-free is the only column that means removal actually happened; the others
are stages on the way to finding out. testable < occurrences is the harness's
limit rather than a property of the proof, so the totals here are a floor.
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
text = z.read("data/substitution_out.txt").decode("utf-8")
targets = {t["name"]: t for t in json.loads(z.read("data/subst_targets.json"))}

rows, totals = [], None
for line in text.splitlines():
    line = line.strip()
    if line.startswith("TOTAL"):
        m = re.match(r"TOTAL occurrences (\d+), testable (\d+), "
                     r"synthesised (\d+), choice-free (\d+)", line)
        totals = tuple(int(g) for g in m.groups())
        continue
    parts = [p.strip() for p in line.split("|")]
    if len(parts) != 5 or parts[0] == "declaration":
        continue
    name, occ, testable, synth, free = parts
    t = targets.get(name, {})
    rows.append({
        "declaration": name,
        "theorems_dominated": t.get("dominates"),
        "route_to_axiom": " > ".join(t.get("route", [])) or None,
        "occurrences": int(occ),
        "testable": int(testable),
        "synthesised": int(synth),
        "kernel_verified_choice_free": int(free),
    })

rows.sort(key=lambda r: (-(r["theorems_dominated"] or 0), r["declaration"]))

out = HERE / "data" / "substitution-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

got = (sum(r["occurrences"] for r in rows), sum(r["testable"] for r in rows),
       sum(r["synthesised"] for r in rows),
       sum(r["kernel_verified_choice_free"] for r in rows))
assert got == totals, f"row sums {got} disagree with the file's TOTAL {totals}"

print(f"  wrote {out.name}: {len(rows)} declarations")
print(f"  occurrences {got[0]}, testable {got[1]}, synthesised {got[2]}, "
      f"kernel-verified choice-free {got[3]}")
print(f"  declarations with any removal: "
      f"{sum(1 for r in rows if r['kernel_verified_choice_free'])}")
print(f"  row sums match the file's own TOTAL line")
