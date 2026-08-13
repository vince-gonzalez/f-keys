"""Build data/module-spend-rows.json — which files spend choice, and on what.

    python gonzalgo/_build/extract_module_spend.py

Reads the 4.33.0 declaration dump and counts, per module, declarations whose own
proof term names a choice primitive DIRECTLY. This is spending, not reach: a
module with no direct spend can still be full of theorems that depend on choice
through something they import.

Direct spending is what a maintainer can act on. "324,808 theorems depend on
choice" names no file; "this module spends it 168 times" names one.

The primitives are counted separately because they are not interchangeable.
`Classical.byContradiction` is excluded middle, `Classical.propDecidable` is the
decidability fallback, and `Classical.choice` proper is choosing from a family.
A repair aimed at one does nothing for the others.

Cheap on purpose: one streamed pass, no closure, no graph. The expensive
question — how far each spend reaches — is the Dominator Table's.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DUMP = Path(r"C:\Users\Admin\lean-work\opaquedisc\mathlib_split.tsv")

PRIMS = ["Classical.choice", "Classical.propDecidable",
         "Classical.byContradiction", "Classical.em",
         "Classical.indefiniteDescription", "Classical.byCases"]
PRIMSET = set(PRIMS)
SHORT = {p: p.split(".")[-1] for p in PRIMS}

mod = collections.defaultdict(collections.Counter)
with open(DUMP, encoding="utf-8", errors="replace") as f:
    for line in f:
        p = line.rstrip("\n").rstrip("\r").split("\t")
        if len(p) < 5:
            continue
        kind, _name, stmt, proof, module = p[0], p[1], p[2], p[3], p[4]
        c = mod[module]
        c["declarations"] += 1
        if kind == "T":
            c["theorems"] += 1
        hits = set(proof.split()) & PRIMSET
        if hits:
            c["spends"] += 1
            for h in hits:
                c[SHORT[h]] += 1
        if set(stmt.split()) & PRIMSET:
            # The primitive is in the theorem's TYPE, so no proof can avoid it.
            c["statement_names_primitive"] += 1

rows = []
for module, c in mod.items():
    if not c["spends"]:
        continue                      # only modules that actually spend
    rows.append({
        "module": module,
        "library": module.split(".")[0],
        "declarations": c["declarations"],
        "theorems": c["theorems"],
        "spends": c["spends"],
        "spend_rate_pct": round(100 * c["spends"] / c["declarations"], 1),
        **{SHORT[p]: c[SHORT[p]] for p in PRIMS},
        "statement_names_primitive": c["statement_names_primitive"],
    })
rows.sort(key=lambda r: (-r["spends"], r["module"]))

out = HERE / "data" / "module-spend-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

tot = sum(r["spends"] for r in rows)
print(f"  wrote {out.name}: {len(rows):,} modules that spend, "
      f"of {len(mod):,} measured")
print(f"  declarations spending directly: {tot:,}")
for p in PRIMS:
    print(f"    {SHORT[p]:<24}{sum(r[SHORT[p]] for r in rows):>7,}")
print(f"  by library: "
      f"{dict(collections.Counter(r['library'] for r in rows).most_common(6))}")
