"""Build the bundle and push a new Zenodo version, without the web form.

    set ZENODO_TOKEN=...            (once, see below)
    python gonzalgo/_build/deposit.py            # build + upload, leave a draft
    python gonzalgo/_build/deposit.py --publish  # ...and mint the version DOI

Getting a token, once: zenodo.org > your account > Applications > Personal
access tokens > New token, scopes `deposit:write` and `deposit:actions`. Put it
in the environment. It is never read from a file here and never printed.

What this does that the form cannot: the description, the table list and the row
counts are GENERATED from the indexes that actually exist at the moment of
deposit. The first deposit went out describing eight tables because a human
wrote that sentence once and the table count moved underneath it. That cannot
happen again.

Publishing is irreversible and mints a DOI, so it is behind a flag. Without
--publish you get a draft URL to look at.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]
GONZALGO = SITE / "gonzalgo"
BUNDLE = HERE / "dist" / "gonzalgo-indexes.zip"

API = "https://zenodo.org/api"
CONCEPT_RECORD = "21900626"          # any published version of the series
ORCID = "0009-0005-3640-014X"

RELATED = [
    ("isSupplementTo", "10.5281/zenodo.21769846", "doi"),
    ("isSupplementTo", "10.5281/zenodo.21853489", "doi"),
    ("isSupplementTo", "10.5281/zenodo.21883963", "doi"),
    ("isSupplementTo", "10.5281/zenodo.21884471", "doi"),
    ("isCompiledBy", "https://github.com/vince-gonzalez/gonzalgo", "url"),
    ("isDocumentedBy", "https://f-keys.com/gonzalgo/data/", "url"),
]
KEYWORDS = ["formal verification", "Lean 4", "Mathlib", "Metamath",
            "proof assistant", "axiom of choice", "dependency graph",
            "dominator tree", "constructive mathematics", "provenance",
            "reproducibility"]


# --------------------------------------------------------------------------
def collect() -> list[dict]:
    """Every index currently published on the site, read from its own JSON."""
    out = []
    for path in sorted(GONZALGO.glob("*/*.json")):
        if path.stem != path.parent.name:
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        if "rows" not in d or "sha256" not in d:
            continue
        out.append({"slug": path.stem, "title": d["name"], "rows": len(d["rows"]),
                    "version": d["version"], "sha256": d["sha256"],
                    "url": d["url"], "description": d["description"]})
    if not out:
        sys.exit("  no indexes found — run build_all.py first")
    return sorted(out, key=lambda m: -m["rows"])


def build_bundle(meta: list[dict]) -> Path:
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BUNDLE, "w", zipfile.ZIP_DEFLATED) as z:
        for m in meta:
            for ext in ("json", "csv"):
                z.write(GONZALGO / m["slug"] / f"{m['slug']}.{ext}",
                        f"data/{m['slug']}.{ext}")
        for p in sorted(HERE.glob("*.py")):
            z.write(p, f"build/{p.name}")
        for p in sorted((HERE / "data").glob("*.json")):
            z.write(p, f"build/data/{p.name}")
        z.writestr("manifest.json", json.dumps(
            {"name": "gonzalgo indexes", "license": "CC-BY-4.0",
             "doi": "https://doi.org/10.5281/zenodo.21900625",
             "catalogue": "https://f-keys.com/gonzalgo/data/",
             "software": "https://pypi.org/project/gonzalgo/",
             "indexes": meta}, indent=2))
    return BUNDLE


def description(meta: list[dict]) -> str:
    rows = sum(m["rows"] for m in meta)
    lines = [
        f"<p>{len(meta)} tables measuring what formal mathematical libraries "
        f"depend on, produced by one program (gonzalgo) reading proofs that Lean 4 "
        f"and Metamath have already checked. {rows:,} rows, each table as JSON and "
        f"CSV.</p>", "<ul>"]
    for m in meta:
        lines.append(f"<li><strong>{m['slug']}</strong> ({m['rows']:,} rows) — "
                     f"{m['description']}</li>")
    lines += ["</ul>",
              "<p>Every figure comes from the proof system's own bookkeeping — "
              "Lean's collectAxioms and Metamath's proof structure. The tool proves "
              "nothing itself and checks no proofs. Each table carries a sha256 over "
              "its rows, and each declares the arithmetic relations its published "
              "prose depends on and will not build if one fails.</p>",
              "<p>Measured against Lean 4.32.1 with Mathlib v4.32.1, and Metamath "
              "set.mm, iset.mm, nf.mm, ql.mm, hol.mm. Live catalogue: "
              "<a href=\"https://f-keys.com/gonzalgo/data/\">"
              "f-keys.com/gonzalgo/data/</a></p>"]
    return "\n".join(lines)


# --------------------------------------------------------------------------
def call(method: str, url: str, token: str, data=None, ctype="application/json"):
    body = data if isinstance(data, bytes) else (
        json.dumps(data).encode() if data is not None else None)
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        # never echo the request; the token rides in the header
        sys.exit(f"  Zenodo {e.code} on {method} {url.split('?')[0]}\n  {raw[:400]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true",
                    help="mint the version DOI (irreversible)")
    ap.add_argument("--version", default=None, help="e.g. 1.1.0")
    args = ap.parse_args()

    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        sys.exit("  ZENODO_TOKEN is not set. zenodo.org > Applications >\n"
                 "  Personal access tokens, scopes deposit:write deposit:actions")

    meta = collect()
    total = sum(m["rows"] for m in meta)
    print(f"  {len(meta)} indexes, {total:,} rows")
    build_bundle(meta)
    print(f"  bundle {BUNDLE.name}: {BUNDLE.stat().st_size:,} bytes")

    # A half-finished draft may already exist — started in the web UI, or left
    # behind by an interrupted run. Zenodo refuses to open a second one, so
    # reuse it rather than asking anyone to go clean up by hand.
    _, published = call("GET", f"{API}/deposit/depositions/{CONCEPT_RECORD}",
                        token)
    concept = published.get("conceptrecid")
    _, siblings = call(
        "GET",
        f"{API}/deposit/depositions?q=conceptrecid:{concept}&all_versions=1"
        f"&size=50&sort=mostrecent", token)
    drafts = [d for d in siblings if not d.get("submitted")]

    if drafts:
        draft = drafts[0]
        print(f"  reusing existing draft {draft['id']}")
    else:
        _, dep = call(
            "POST",
            f"{API}/deposit/depositions/{CONCEPT_RECORD}/actions/newversion",
            token)
        _, draft = call("GET", dep["links"]["latest_draft"], token)
        print(f"  new draft {draft['id']}")
    draft_id = draft["id"]
    # Re-read: a draft from the listing carries a thinner file record.
    _, draft = call("GET", f"{API}/deposit/depositions/{draft_id}", token)

    # A draft inherits the previous version's files and they CAN be removed here,
    # which is the only place in Zenodo where that is true.
    for f in draft.get("files", []):
        call("DELETE", f"{API}/deposit/depositions/{draft_id}/files/{f['id']}",
             token)
        print(f"  dropped inherited {f['filename']}")

    bucket = draft["links"]["bucket"]
    call("PUT", f"{bucket}/{BUNDLE.name}", token, BUNDLE.read_bytes(),
         "application/octet-stream")
    print(f"  uploaded {BUNDLE.name}")

    # The version has to come from the newest PUBLISHED record, not the draft.
    # A fresh draft inherits metadata from the concept's first version, so
    # reading it here produced 1.0.0 -> 1.1.0 twice and minted two records
    # claiming the same version.
    _, published_all = call(
        "GET",
        f"{API}/deposit/depositions?q=conceptrecid:{concept}&all_versions=1"
        f"&size=100&sort=mostrecent", token)
    versions = [d["metadata"].get("version") for d in published_all
                if d.get("submitted") and d["metadata"].get("version")]

    def key(v):
        try:
            return tuple(int(x) for x in str(v).lstrip("v").split("."))
        except Exception:
            return (0,)

    prev = max(versions, key=key) if versions else "1.0.0"
    print(f"  published versions: {sorted(set(versions), key=key)} -> newest {prev}")
    if args.version:
        newver = args.version
    else:
        parts = prev.split(".")
        parts[1] = str(int(parts[1]) + 1)
        parts[2] = "0"
        newver = ".".join(parts)

    payload = {"metadata": {
        "title": ("The gonzalgo Indexes: standing measurements of what formal "
                  "mathematical libraries rest on"),
        "upload_type": "dataset",
        "description": description(meta),
        "creators": [{"name": "Gonzalez, Vincent", "orcid": ORCID,
                      "affiliation": "F-Keys"}],
        "access_right": "open",
        "license": "cc-by-4.0",
        "version": newver,
        "language": "eng",
        "keywords": KEYWORDS,
        "related_identifiers": [
            {"relation": r, "identifier": i, "scheme": s}
            for r, i, s in RELATED],
    }}
    call("PUT", f"{API}/deposit/depositions/{draft_id}", token, payload)
    print(f"  metadata set, version {prev} -> {newver}")

    if args.publish:
        _, pub = call("POST",
                      f"{API}/deposit/depositions/{draft_id}/actions/publish",
                      token)
        print(f"  PUBLISHED  doi {pub.get('doi')}")
        print(f"  {pub['links'].get('record_html', '')}")
    else:
        print(f"  draft ready, not published:\n"
              f"    https://zenodo.org/uploads/{draft_id}\n"
              f"  re-run with --publish to mint the DOI")


if __name__ == "__main__":
    main()
