"""Put back related identifiers that the sweep's retry wiped.

    python gonzalgo/_build/restore_related.py            # show what would go back
    python gonzalgo/_build/restore_related.py --apply

A PUT to Zenodo replaces metadata wholesale. When the sweep hit a 400 naming
related_identifiers it dropped the entire field and retried, the retry
succeeded, and the field came back empty — the arXiv prior-art citations, the
Lean and Mathlib links and the Software Heritage identifier all went with it.
Dropping a whole field to get past a validation error is only safe for a field
that was empty to begin with.

metadata_plan.json still holds the full pre-damage list for each record, because
it was written before the apply that lost them.

This restores the maximum subset the API will take. If the full list is refused
it removes one entry at a time to find which are rejected, keeps everything
else, and reports exactly what could not go back rather than leaving a silent
hole.
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
API = "https://zenodo.org/api"
TARGETS = [21853490, 21866882, 21811488, 21866855]


def http(method, url, token, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "gonzalgo-restore")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def clean(ids):
    out = []
    for x in ids:
        y = {k: v for k, v in x.items() if k != "scheme"}
        out.append(y)
    return out


def try_put(rid, token, meta, ids):
    m = dict(meta)
    m["related_identifiers"] = ids
    c, r = http("PUT", f"{API}/deposit/depositions/{rid}", token,
                {"metadata": m})
    return c, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    wanted = {r["id"]: clean(r["patch"].get("related_identifiers", []))
              for r in plan["records"] if r["id"] in TARGETS}

    if not args.apply:
        for rid, ids in wanted.items():
            print(f"{rid}: would restore {len(ids)}")
            for x in ids:
                print(f"    {x.get('relation'):<18}{x.get('identifier','')[:56]}")
        print("\n  re-run with --apply")
        return

    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        sys.exit("  ZENODO_TOKEN is not set")

    for rid, ids in wanted.items():
        c, live = http("GET", f"{API}/deposit/depositions/{rid}", token)
        if c != 200:
            print(f"  {rid}: cannot read ({c})"); continue
        meta = live["metadata"]
        if meta.get("related_identifiers"):
            print(f"  {rid}: already has "
                  f"{len(meta['related_identifiers'])}, leaving alone")
            continue

        ec, _ = http("POST", f"{API}/deposit/depositions/{rid}/actions/edit",
                     token)
        if ec not in (200, 201, 400):
            print(f"  {rid}: cannot unlock ({ec})"); continue

        keep, refused = list(ids), []
        c, r = try_put(rid, token, meta, keep)
        while c == 400 and keep:
            # Find the offender rather than discarding the set: drop each
            # candidate in turn and keep the first list the API accepts.
            found = False
            for i in range(len(keep)):
                trial = keep[:i] + keep[i + 1:]
                tc, tr = try_put(rid, token, meta, trial)
                if tc in (200, 201):
                    refused.append(keep[i]); keep = trial
                    c, r = tc, tr; found = True
                    break
            if not found:
                break
        if c in (200, 201):
            pc, _ = http("POST",
                         f"{API}/deposit/depositions/{rid}/actions/publish",
                         token)
            state = "restored" if pc in (200, 201, 202) else \
                "edited but NOT republished"
            print(f"  {rid}: {state} {len(keep)}/{len(ids)}")
            for x in refused:
                print(f"      refused by Zenodo: {x.get('identifier','')[:60]}")
        else:
            print(f"  {rid}: could not restore — "
                  f"{str(r.get('error',''))[:130]}")
        time.sleep(0.3)


if __name__ == "__main__":
    main()
