"""Build data/dominator-table-rows.json from the deposited reproduction archive.

    python gonzalgo/_build/extract_dominator_rows.py

Source: dominator-analysis-code.zip, attached to 10.5281/zenodo.21883963.

The archive holds two files and they measure different things. `dominators.json`
counts CONSTANTS: what each one alone dominates. `site_eligibility.json` counts
SITES: a run of constants each dominating the next, with no theorems lost
between them, is one site, because severing any member frees the same set. The
note is explicit — "Std.DHashMap.Internal.Raw.WF.out, wfImp_alterₘ and
isHashSelf_updateBucket_alter carry 4,892, 4,896 and 4,899 and are one site, not
three" — and reports 4,899.

The site is the publishable unit and the one the note's figures refer to, so the
table is built from the sites file. Verified on every row: a site's count is the
maximum over its chain, and equals its chain head's own constant count. Where a
site's label differs in count from that constant taken alone, both are carried:
`theorems_dominated` is the site, `constant_alone` is the label constant.
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
constants = {r["name"]: r["alone"]
             for r in json.loads(z.read("data/dominators.json"))}
sites = json.loads(z.read("data/site_eligibility.json"))
sites.sort(key=lambda s: -s["alone"])

rows = []
collapsed = 0
for rank, s in enumerate(sites, start=1):
    chain = s["chain"]
    members = [constants[c] for c in chain if c in constants]
    assert s["alone"] == max(members), f"{s['name']}: not the max over its chain"
    assert s["alone"] == constants[chain[0]], f"{s['name']}: head count differs"
    if len(chain) > 1:
        collapsed += 1
    row = {
        "rank": rank,
        "site": s["name"],
        "kind": KIND.get(s["kind"], s["kind"]),
        "theorems_dominated": s["alone"],
        "area": s["area"],
        # statement_bound: the constant's own type is classical, so no
        # constructive replacement can exist. eligible is its negation.
        "eligible": not s["statement_bound"],
        "chain_length": len(chain),
        "chain": " > ".join(chain),
    }
    alone = constants.get(s["name"])
    if alone is not None and alone != s["alone"]:
        row["constant_alone"] = alone
    rows.append(row)

out = HERE / "data" / "dominator-table-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"  wrote {out.name}: {len(rows):,} sites")
print(f"  collapsed chains (more than one constant): {collapsed}")
print(f"  label constant differs from its site count: "
      f"{sum(1 for r in rows if 'constant_alone' in r)}")
print(f"  ineligible sites: {sum(1 for r in rows if not r['eligible'])}")
