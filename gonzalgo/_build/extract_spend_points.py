"""Build data/spend-point-rows.json from the deposited reproduction archive.

    python gonzalgo/_build/extract_spend_points.py

Source: dominator-analysis-code.zip, attached to 10.5281/zenodo.21883963.

Dominance says which site a theorem's classical dependence is responsible to.
It does not say where the axiom is actually SPENT — a site can dominate tens of
thousands of theorems while every primitive use of choice sits above it in the
graph. `spenders` counts declarations inside the site's dominator subtree that
cite a choice primitive directly, and `primitives` names which and how many.

A site with a large subtree and zero spenders is inheriting, not spending.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = Path(r"C:\Users\Admin\OneDrive\Desktop\PAPER-dominators"
               r"\dominator-analysis-code.zip")

z = zipfile.ZipFile(ARCHIVE)
sites = json.loads(z.read("data/spendpoints.json"))
sites.sort(key=lambda s: -s["alone"])

rows = []
for rank, s in enumerate(sites, start=1):
    prims = s.get("prims") or {}
    rows.append({
        "rank": rank,
        "site": s["site"],
        "theorems_dominated": s["alone"],
        "subtree_constants": s["subtree"],
        "spenders": s["spenders"],
        "spends_directly": bool(prims),
        "primitives": ", ".join(f"{k} x{v}" for k, v in sorted(prims.items()))
                      or "(none — inherits)",
        "example_dependents": " ; ".join((s.get("examples") or [])[:3]),
    })

out = HERE / "data" / "spend-point-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

inherit = [r for r in rows if not r["spends_directly"]]
print(f"  wrote {out.name}: {len(rows)} sites")
print(f"  sites that spend a primitive inside their subtree: "
      f"{len(rows) - len(inherit)}")
print(f"  sites that inherit only (zero spenders): {len(inherit)}, "
      f"dominating {sum(r['theorems_dominated'] for r in inherit):,} theorems")
