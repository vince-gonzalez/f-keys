"""Audit and patch the metadata on every Zenodo deposit under one ORCID.

    python gonzalgo/_build/metadata_sweep.py                 # audit, write a plan
    python gonzalgo/_build/metadata_sweep.py --apply         # apply the plan

Metadata edits on a published record keep the same DOI, so this is not a
versioning operation and does not disturb anyone's citation.

The plan is written to metadata_plan.json and is meant to be READ AND EDITED
before applying. Nothing here invents content: language comes from the record
already being English, related identifiers are links between the author's own
deposits and to repositories that exist, and a record with nothing verifiable to
add gets no patch. Anything requiring a judgement — resource type above all —
is reported and left alone.

--apply walks the plan and PUTs each patch. It skips any record whose live
metadata has changed since the plan was written, so an edited plan cannot
silently overwrite something done in the web UI in the meantime.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = HERE / "metadata_plan.json"
ORCID = "0009-0005-3640-014X"
API = "https://zenodo.org/api"

# Types that state something about where a work appeared. A Zenodo-only deposit
# is not a journal article, and DataCite carries that claim downstream.
OVERCLAIMING = {"Journal article", "Book", "Data paper", "Book section",
                "Conference paper"}

# Repositories that exist and hold the code behind a deposit.
REPO = {
    "gonzalgo": "https://github.com/zengineco/gonzalgo",
    "opticquiz": "https://github.com/zengineco/opticquiz.com",
}
CATALOGUE = "https://f-keys.com/gonzalgo/data/"

# Clusters of the author's own work, so a reader landing on one finds the rest.
# Every DOI here is checked to exist before it is written.
AXIOM_SERIES = ["10.5281/zenodo.21769846", "10.5281/zenodo.21853489",
                "10.5281/zenodo.21883963", "10.5281/zenodo.21884471",
                "10.5281/zenodo.21900625"]


def http(method, url, token=None, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("User-Agent", "gonzalgo-metadata-sweep")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def deposits() -> list[str]:
    # ORCID serves XML unless JSON is asked for explicitly.
    req = urllib.request.Request(
        f"https://pub.orcid.org/v3.0/{ORCID}/works",
        headers={"Accept": "application/json",
                 "User-Agent": "gonzalgo-metadata-sweep"})
    d = json.loads(urllib.request.urlopen(req).read().decode())
    out = []
    for g in d["group"]:
        for e in g.get("external-ids", {}).get("external-id", []):
            v = e["external-id-value"].lower()
            if e["external-id-type"] == "doi" and "zenodo." in v:
                out.append(v.split("zenodo.")[-1])
    return list(dict.fromkeys(out))


def plan_for(rec: dict) -> tuple[dict, list[str]]:
    """Return (patch, notes-for-the-human). Patch is only verifiable additions."""
    m = rec["metadata"]
    patch, flags = {}, []
    title = m["title"].lower()

    if not m.get("language"):
        patch["language"] = "eng"

    rel = {(r.get("relation"), r.get("identifier"))
           for r in m.get("related_identifiers", [])}
    add = []
    for key, url in REPO.items():
        if key in title and ("isSupplementedBy", url) not in rel:
            add.append({"relation": "isSupplementedBy", "identifier": url,
                        "scheme": "url", "resource_type": "software"})
    # A version record carries its own DOI and its concept DOI, and linking to
    # either is a self-reference. Both have to be excluded, not just the first.
    own = {(rec.get("doi") or "").lower(), (rec.get("conceptdoi") or "").lower()}
    own.discard("")
    if any(k in title for k in ("axiom", "classical depend", "dominator",
                                "eligibility", "tactic-level", "gonzalgo")):
        for sib in AXIOM_SERIES:
            if sib.lower() in own:
                continue
            if ("isRelatedTo", sib) not in rel and ("isSupplementTo", sib) not in rel:
                add.append({"relation": "isRelatedTo", "identifier": sib,
                            "scheme": "doi"})
        if ("isDocumentedBy", CATALOGUE) not in rel:
            add.append({"relation": "isDocumentedBy", "identifier": CATALOGUE,
                        "scheme": "url"})
    if add:
        patch["related_identifiers"] = m.get("related_identifiers", []) + add

    if m["resource_type"]["title"] in OVERCLAIMING:
        flags.append(f"resource type is {m['resource_type']['title']!r} — "
                     "not decided here")
    if not m.get("keywords"):
        flags.append("no keywords")
    if not m.get("references"):
        flags.append("no references")
    return patch, flags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.apply:
        token = os.environ.get("ZENODO_TOKEN")
        if not token:
            sys.exit("  ZENODO_TOKEN is not set")
        if not PLAN.exists():
            sys.exit("  no metadata_plan.json — run without --apply first")
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        done = skipped = 0
        for entry in plan["records"]:
            if not entry["patch"]:
                continue
            rid = entry["id"]
            c, live = http("GET", f"{API}/deposit/depositions/{rid}", token)
            if c != 200:
                print(f"  {rid}: cannot open ({c})"); skipped += 1; continue
            if live["metadata"].get("title") != entry["title_full"]:
                print(f"  {rid}: changed since the plan was written, skipping")
                skipped += 1; continue
            merged = dict(live["metadata"]); merged.update(entry["patch"])
            c, _ = http("PUT", f"{API}/deposit/depositions/{rid}", token,
                        {"metadata": merged})
            if c in (200, 201):
                http("POST", f"{API}/deposit/depositions/{rid}/actions/publish",
                     token)
                print(f"  {rid}: {', '.join(entry['patch'])}")
                done += 1
            else:
                print(f"  {rid}: PUT failed {c}"); skipped += 1
            time.sleep(0.3)
        print(f"\n  {done} updated, {skipped} skipped")
        return

    records, flagged = [], 0
    for rid in deposits():
        c, rec = http("GET", f"{API}/records/{rid}")
        if c != 200:
            continue
        patch, flags = plan_for(rec)
        records.append({"id": rec["id"], "doi": rec.get("doi"),
                        "title": rec["metadata"]["title"][:70],
                        "title_full": rec["metadata"]["title"],
                        "type": rec["metadata"]["resource_type"]["title"],
                        "patch": patch, "needs_a_decision": flags})
        flagged += bool(flags)
        time.sleep(0.15)

    seen, uniq = set(), []
    for r in records:
        if r["id"] in seen:
            continue
        seen.add(r["id"]); uniq.append(r)
    PLAN.write_text(json.dumps({"records": uniq}, indent=2, ensure_ascii=False),
                    encoding="utf-8")

    patched = [r for r in uniq if r["patch"]]
    print(f"  {len(uniq)} records, {len(patched)} with a verifiable patch")
    for r in patched:
        print(f"    {r['id']:<10}{', '.join(r['patch']):<40}{r['title'][:40]}")
    print(f"\n  needing a decision, left alone: {flagged}")
    for r in uniq:
        if r["needs_a_decision"]:
            print(f"    {r['id']:<10}{'; '.join(r['needs_a_decision'])[:70]}")
    print(f"\n  plan written to {PLAN.name} — read it, edit it, then --apply")


if __name__ == "__main__":
    main()
