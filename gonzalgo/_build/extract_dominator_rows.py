"""Build data/dominator-table-rows.json from the deposited reproduction archive.

    python gonzalgo/_build/extract_dominator_rows.py

Source: dominator-analysis-code.zip, the archive attached to
10.5281/zenodo.21883963. Two files in it carry a `alone` count per constant and
they do not agree on 137 of the 1,500 they share — dominators.json says
Std.DHashMap.Internal.Raw.WF.out dominates 4,899 theorems, site_eligibility.json
says 4,892. The published note reports 4,899, so dominators.json is authoritative
here and only the categorical fields (area, statement_bound, route) are taken
from the other. Disagreements are recorded on the row rather than resolved
silently, and the count is printed on every run.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = Path(r"C:\Users\Admin\OneDrive\Desktop\PAPER-dominators"
               r"\dominator-analysis-code.zip")

KIND = {"D": "definition", "T": "theorem", "O": "other"}

z = zipfile.ZipFile(ARCHIVE)
dominators = json.loads(z.read("data/dominators.json"))
eligibility = {r["name"]: r for r in json.loads(z.read("data/site_eligibility.json"))}

rows = []
disagreements = 0
for rank, d in enumerate(dominators, start=1):
    e = eligibility.get(d["name"])
    row = {
        "rank": rank,
        "constant": d["name"],
        "kind": KIND.get(d["kind"], d["kind"]),
        "theorems_dominated": d["alone"],
        "area": e["area"] if e else None,
        # statement_bound: the constant's own TYPE is classical, so no
        # constructive replacement of it can exist. eligible is its negation.
        "eligible": (not e["statement_bound"]) if e else None,
        "route": " > ".join(e["chain"]) if e else None,
    }
    if e and e["alone"] != d["alone"]:
        row["count_in_eligibility_file"] = e["alone"]
        disagreements += 1
    rows.append(row)

out = HERE / "data" / "dominator-table-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

covered = sum(1 for r in rows if r["area"] is not None)
print(f"  wrote {out.name}: {len(rows):,} rows")
print(f"  eligibility fields available for {covered:,}")
print(f"  count disagreements between the two source files: {disagreements}")
