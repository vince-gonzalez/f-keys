"""Build data/cleanable-rows.json — every declaration a rewrite was attempted on.

    python gonzalgo/_build/extract_cleanable.py

Sources, both from the Lean workspace this was measured in:
  cleanable.tsv   module, declaration, the generated proof term inside it
  rewrite.tsv     outcome per proof term, with the kernel's reason on failure

The unit is a compiler-generated `_proof_N` term, not a lemma anyone wrote. That
is the point rather than a limitation: the removable classical dependence in
these libraries lives in terms the elaborator emitted, so it is removed by
changing the tactic that emits them, not by editing a proof.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = Path(r"C:\Users\Admin\lean-work\opaquedisc")


def rows_of(path: Path, width: int) -> list[list[str]]:
    """Split on tabs, rejoining rows whose last field carried a newline.

    Lean's error text contains newlines and these files are not quoted, so a
    naive line-per-row read silently turns a continuation into a row with a
    kernel message where its status should be."""
    out: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= width and out is not None and "\t" in line:
            out.append(parts[:width - 1] + ["\t".join(parts[width - 1:])])
        elif out:
            out[-1][-1] += "\n" + line
    return out


cleanable = rows_of(WORK / "cleanable.tsv", 3)
rewrite = rows_of(WORK / "rewrite.tsv", 7)

outcome = {r[1]: r for r in rewrite}
rows = []
for module, declaration, term in cleanable:
    r = outcome.get(term)
    status = r[0] if r else None
    rows.append({
        "library": module.split(".")[0],
        "module": module,
        "declaration": declaration,
        "generated_term": term,
        "occurrences": int(r[2]) if r else None,
        "outcome": {"CLEAN": "removed", "FAIL": "kernel rejected",
                    "kept-choice": "still classical"}.get(status, status),
        "kernel_reason": (r[6].strip() if r and status == "FAIL" else None),
    })

rows.sort(key=lambda r: (r["library"], r["module"], r["declaration"]))

out = HERE / "data" / "cleanable-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

import collections
print(f"  wrote {out.name}: {len(rows)} declarations, "
      f"{len({r['module'] for r in rows})} modules")
print("  by outcome:", dict(collections.Counter(r["outcome"] for r in rows)))
print("  by library:", dict(collections.Counter(r["library"] for r in rows)))
assert len(rewrite) == 280 and len(cleanable) == 280, "row counts moved"
assert sum(1 for r in rows if r["outcome"] == "removed") == 275
print("  275 removed, matching the published figure")
