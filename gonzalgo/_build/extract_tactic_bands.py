"""Build data/tactic-band-rows.json from the deposited reproduction archive.

    python gonzalgo/_build/extract_tactic_bands.py

Source: tactic-attribution-code.zip, attached to 10.5281/zenodo.21853489,
fetched once to _build/source/ and read from there.

The measure is: of the proofs using a tactic that depend on Classical.choice,
what share have a choice-free STATEMENT — that is, a dependence the proof
introduced rather than the theorem requiring. rate = eligible / classical.

A rate on its own says nothing, because the population a tactic is used on
determines it. The calibration is the point: `known_negatives` are tactics that
cannot introduce a classical instance at all, so whatever rate they show is the
background of the population, not an effect of the tactic. A tactic is only a
candidate if it escapes the band its own library's controls establish.

`strict` attributes a proof to a tactic only when it is the sole tactic in the
proof; `loose` counts every proof the tactic appears in. Strict is cleaner and
starves most cells below the n threshold, which is why both are carried.
"""
from __future__ import annotations

import json
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "source" / "tactic-attribution-code.zip"
URL = ("https://zenodo.org/api/records/21866882/files/"
       "tactic-attribution-code.zip/content")

if not SRC.exists():
    SRC.parent.mkdir(parents=True, exist_ok=True)
    print(f"  fetching {URL}")
    urllib.request.urlretrieve(URL, SRC)

z = zipfile.ZipFile(SRC)
c = json.loads(z.read("data/canonical.json"))
KNOWN_NEGATIVE = set(c["known_negatives"])
MIN_N = c["min_n"]

# The 15 tactics analysis/final_table.py tests against the bands. The paper's
# "seven escapes" is a count over these, not over every tactic in the data:
# simpa, for one, is neither a known-negative nor on this list, so it was never
# examined. Carried as a column so the paper's figure is reproducible from these
# rows and the untested cells are visible rather than absent.
PAPER_CANDIDATES = {
    "omega", "norm_num", "grind", "decide", "simp", "simp_all", "nlinarith",
    "linarith", "positivity", "tauto", "aesop", "norm_cast", "ring",
    "field_simp", "interval_cases",
}

rows = []
for library, lib in c["libraries"].items():
    for mode in ("strict", "loose"):
        cells = lib[mode]
        band = lib.get(f"band_{mode}")
        if not band:
            continue
        lo, hi = band["min"], band["max"]
        # The band is recomputed from the cells and checked against the one the
        # archive stores, so a row and its band cannot come from different runs.
        controls = [v["rate"] for t, v in cells.items()
                    if t in KNOWN_NEGATIVE and v["n"] >= MIN_N
                    and v["rate"] is not None]
        assert controls and (min(controls), max(controls)) == (lo, hi), (
            f"{library}/{mode}: recomputed band disagrees with the stored one")
        assert len(controls) == band["n_tactics"]
        for tactic, v in cells.items():
            if v["n"] < MIN_N or v["rate"] is None:
                continue
            neg = tactic in KNOWN_NEGATIVE
            rows.append({
                "library": library,
                "attribution": mode,
                "tactic": tactic,
                "proofs": v["n"],
                "classical": v["classical"],
                "eligible": v["eligible"],
                "rate_pct": round(100 * v["rate"], 1),
                "role": ("known-negative" if neg
                         else "candidate" if tactic in PAPER_CANDIDATES
                         else "not examined"),
                "band_low_pct": round(100 * lo, 1),
                "band_high_pct": round(100 * hi, 1),
                "band_widest": band["argmax"],
                "position": ("above band" if v["rate"] > hi
                             else "below band" if v["rate"] < lo
                             else "inside band"),
                "escapes_band": (not neg) and v["rate"] > hi,
                "controls_in_band": len(controls),
            })

rows.sort(key=lambda r: (r["library"], r["attribution"], -r["rate_pct"]))

out = HERE / "data" / "tactic-band-rows.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

esc = [r for r in rows if r["escapes_band"]]
print(f"  wrote {out.name}: {len(rows)} cells "
      f"(n >= {MIN_N}, {len(KNOWN_NEGATIVE)} known-negative tactics)")
for lib in sorted({r["library"] for r in rows}):
    for mode in ("loose", "strict"):
        m = [r for r in rows if r["library"] == lib and r["attribution"] == mode]
        if m:
            print(f"    {lib:<10} {mode:<7} band "
                  f"{m[0]['band_low_pct']}%-{m[0]['band_high_pct']}% "
                  f"from {m[0]['controls_in_band']} controls, {len(m)} cells")
paper = [r for r in esc if r["role"] == "candidate"]
print(f"  escapes among the paper's 15 examined candidates: {len(paper)}")
for r in sorted(paper, key=lambda r: -r["rate_pct"]):
    print(f"    {r['tactic']:<10} {r['library']:<10} {r['attribution']:<7} "
          f"{r['rate_pct']}%  vs band top {r['band_high_pct']}%  n={r['proofs']}")
other = [r for r in esc if r["role"] == "not examined"]
print(f"  escapes among tactics the paper did not examine: {len(other)}")
for r in sorted(other, key=lambda r: -r["rate_pct"]):
    print(f"    {r['tactic']:<10} {r['library']:<10} {r['attribution']:<7} "
          f"{r['rate_pct']}%  vs band top {r['band_high_pct']}%  n={r['proofs']}")
