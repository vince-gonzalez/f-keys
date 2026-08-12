"""Put the Software Heritage archive link back, in a form Zenodo will take.

    python gonzalgo/_build/add_swh.py --apply

The deposit API rejects a bare SWHID (`swh:1:snp:...`) because swh is not one of
the identifier schemes it validates. The resolvable URL carries the same
identifier and goes in as a plain URL, so the archive link is not lost — only
its notation changes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://zenodo.org/api"
SWHID = "swh:1:snp:b2955af0bc594c5972fcaf7689365c9243d3b9fb"
URL = f"https://archive.softwareheritage.org/{SWHID}"
TARGETS = [21853490, 21866882, 21811488, 21866855]


def http(method, url, token, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "gonzalgo-swh")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not args.apply:
        print(f"  would add to {len(TARGETS)} records:\n    isSupplementedBy  {URL}")
        return
    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        sys.exit("  ZENODO_TOKEN is not set")

    for rid in TARGETS:
        c, live = http("GET", f"{API}/deposit/depositions/{rid}", token)
        if c != 200:
            print(f"  {rid}: cannot read ({c})"); continue
        meta = live["metadata"]
        ids = meta.get("related_identifiers") or []
        if any(URL.lower() == x.get("identifier", "").lower() for x in ids):
            print(f"  {rid}: already has it"); continue

        ec, _ = http("POST", f"{API}/deposit/depositions/{rid}/actions/edit",
                     token)
        if ec not in (200, 201, 400):
            print(f"  {rid}: cannot unlock ({ec})"); continue

        meta["related_identifiers"] = [
            {k: v for k, v in x.items() if k != "scheme"} for x in ids
        ] + [{"relation": "isSupplementedBy", "identifier": URL}]
        c, r = http("PUT", f"{API}/deposit/depositions/{rid}", token,
                    {"metadata": meta})
        if c not in (200, 201):
            print(f"  {rid}: failed {c} {str(r.get('error',''))[:120]}")
            continue
        pc, _ = http("POST", f"{API}/deposit/depositions/{rid}/actions/publish",
                     token)
        print(f"  {rid}: added ({len(meta['related_identifiers'])} total)"
              if pc in (200, 201, 202)
              else f"  {rid}: edited but NOT republished ({pc})")
        time.sleep(0.3)


if __name__ == "__main__":
    main()
