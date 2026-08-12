"""Build data/site-diagnosis-rows.json — why a classical site could not be cleaned.

    python gonzalgo/_build/extract_site_diagnosis.py

Source: sites_retest.tsv from the Lean workspace. An earlier pass,
propdec_sites.tsv, is superseded: it spent 404 of its verdicts on synthesis
timeouts against this run's 12, and had no `not-a-goal` category at all, so it
was mostly measuring its own time limit.

The Cleanable Table publishes what came out. This is what did not, and why,
which is the denominator that makes the numerator readable.

Verdicts:
  no-instance     no Decidable instance could be synthesised for the proposition
  not-a-goal      the occurrence is not in a position where an instance would be
                  supplied, so there is nothing to substitute
  choice-needed   an instance exists and itself depends on choice
  timeout         synthesis did not finish inside the limit
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path(r"C:\Users\Admin\lean-work\opaquedisc\sites_retest.tsv")

VERDICTS = {"no-instance", "not-a-goal", "choice-needed", "timeout"}
EXPLAIN = {
    "no-instance": "no Decidable instance found",
    "not-a-goal": "not an instance position",
    "choice-needed": "instance exists but needs choice",
    "timeout": "synthesis timed out",
}

rows, merged = [], 0
for line in SRC.read_text(encoding="utf-8").splitlines():
    parts = line.split("\t")
    if parts and parts[0] in VERDICTS:
        parts = (parts + [""] * 5)[:5]
        rows.append({
            "verdict": parts[0],
            "meaning": EXPLAIN[parts[0]],
            "library": parts[1].split(".")[0],
            "module": parts[1],
            "declaration": parts[2],
            "proposition": parts[3],
        })
    elif rows:
        # Lean prints propositions containing newlines and the file is unquoted.
        rows[-1]["proposition"] += " " + line.strip()
        merged += 1

rows.sort(key=lambda r: (r["verdict"], r["module"], r["declaration"]))

out = HERE / "data" / "site-diagnosis-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

counts = collections.Counter(r["verdict"] for r in rows)
print(f"  wrote {out.name}: {len(rows)} sites ({merged} continuation lines merged)")
print("  verdicts:", dict(counts))
print(f"  modules {len({r['module'] for r in rows})}, "
      f"declarations {len({r['declaration'] for r in rows})}")
print(f"  never testable at all (not-a-goal): "
      f"{100 * counts['not-a-goal'] / len(rows):.1f}%")
