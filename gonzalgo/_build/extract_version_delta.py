"""Normalise diff_dumps output into index rows.

    python gonzalgo/_build/extract_version_delta.py

diff_dumps writes its two value columns under the version labels themselves,
which reads well in a terminal and is useless as a CSV schema — the column names
would change every time a new version is measured. This flattens them to
`old_value` / `new_value` with the labels carried as their own columns, so a
third measurement appends rows instead of breaking every consumer.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "data" / "version-delta-rows.json"

d = json.loads(SRC.read_text(encoding="utf-8"))
old_label, new_label = d["old_label"], d["new_label"]

rows = []
for r in d["rows"]:
    rows.append({
        "quantity": r["quantity"],
        "from_version": old_label,
        "to_version": new_label,
        "old_value": r.get(old_label),
        "new_value": r.get(new_label),
        "delta": r["delta"],
        "pct_change": r.get("pct_change"),
        "note": r.get("note") or "",
    })

ax = d["axioms"]
rows.append({
    "quantity": "axiom roster",
    "from_version": old_label, "to_version": new_label,
    "old_value": len(ax[old_label]), "new_value": len(ax[new_label]),
    "delta": len(ax[new_label]) - len(ax[old_label]),
    "pct_change": 0.0,
    "note": ("unchanged: " + ", ".join(ax[new_label])) if not (ax["added"] or ax["removed"])
            else ("added " + ", ".join(ax["added"]) + "; removed " + ", ".join(ax["removed"])),
})

out = HERE / "data" / "version-delta-index-rows.json"
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"  wrote {out.name}: {len(rows)} rows, {old_label} -> {new_label}")
print(f"  axiom roster: {len(ax[new_label])} axioms, "
      f"{'unchanged' if not (ax['added'] or ax['removed']) else 'CHANGED'}")
for r in rows:
    o = "" if r["old_value"] is None else f"{r['old_value']:,}"
    n = "" if r["new_value"] is None else f"{r['new_value']:,}"
    print(f"    {r['quantity']:<24}{o:>10}{n:>12}{r['delta']:>+12,}")
