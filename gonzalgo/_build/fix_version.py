"""Correct the version string on a published Zenodo record.

    python gonzalgo/_build/fix_version.py 21922825 1.2.0

A metadata edit keeps the DOI, so nothing anyone has cited moves.

Needed because deposit.py read the version off a freshly created draft, which
inherits metadata from the concept's FIRST version rather than its newest. That
produced 1.0.0 -> 1.1.0 twice and left two published records claiming the same
version. deposit.py now derives it from the newest published record instead;
this repairs the record that was already minted.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://zenodo.org/api"


def call(method, url, token, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:400]}


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("  usage: fix_version.py RECORD_ID VERSION")
    rid, version = sys.argv[1], sys.argv[2]
    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        sys.exit("  ZENODO_TOKEN is not set")

    c, _ = call("POST", f"{API}/deposit/depositions/{rid}/actions/edit", token)
    if c not in (200, 201, 400):          # 400 == already unlocked
        sys.exit(f"  cannot unlock ({c})")

    c, live = call("GET", f"{API}/deposit/depositions/{rid}", token)
    if c != 200:
        sys.exit(f"  cannot read ({c})")
    m = dict(live["metadata"])
    print(f"  {rid}: version {m.get('version')} -> {version}")
    m["version"] = version
    # The records API reports schemes the deposit API refuses to take back.
    for ri in m.get("related_identifiers", []) or []:
        ri.pop("scheme", None)

    c, r = call("PUT", f"{API}/deposit/depositions/{rid}", token, {"metadata": m})
    if c not in (200, 201):
        sys.exit(f"  PUT failed {c}: {str(r.get('error',''))[:200]}")
    c, r = call("POST", f"{API}/deposit/depositions/{rid}/actions/publish", token)
    if c not in (200, 201, 202):
        sys.exit(f"  edited but NOT republished ({c}) — visible in the UI, "
                 f"needs a human: {str(r.get('error',''))[:160]}")
    print("  republished; DOI unchanged")


if __name__ == "__main__":
    main()
