"""Create the Kernel Trust Profile deposit on Zenodo. New record, not a version.

    set ZENODO_TOKEN=...                                  (already set)
    python gonzalgo/_build/deposit_spec.py                # build + draft
    python gonzalgo/_build/deposit_spec.py --publish      # ...and mint the DOI

deposit.py versions an existing record. A specification is a different artifact
class from the measurement series and needs its own identity: bundling them
would give the spec a version number that moves every time a table changes.

The bundle is assembled from what is actually published at
gonzalgo/kernel-trust — SPEC.md, the JSON Schema, and every profile — so the
deposit cannot describe files the site does not serve. Profile count and schema
version are read off the bundle rather than typed into the description.

Publishing mints a DOI and cannot be undone, so it is behind --publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]
SRC = SITE / "gonzalgo" / "kernel-trust"
BUNDLE = HERE / "dist" / "kernel-trust-profile-0.1.zip"
API = "https://zenodo.org/api"
ORCID = "0009-0005-3640-014X"


def call(method, url, token, data=None, ctype="application/json"):
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
        sys.exit(f"  Zenodo {e.code} on {method} {url.split('?')[0]}\n"
                 f"  {e.read().decode()[:500]}")


def build_bundle():
    profiles = sorted((SRC / "profiles").glob("*.json"))
    schema = next(SRC.glob("*.schema.json"))
    if not profiles or not (SRC / "SPEC.md").exists():
        sys.exit("  gonzalgo/kernel-trust is not built — run mk_kernel_trust.py")
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BUNDLE, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(SRC / "SPEC.md", "SPEC.md")
        z.write(schema, f"schema/{schema.name}")
        for p in profiles:
            z.write(p, f"profiles/{p.name}")
        z.writestr("README.md",
                   "# Kernel Trust Profile 0.1\n\n"
                   "SPEC.md is the specification. schema/ holds the JSON Schema a\n"
                   "profile must validate against. profiles/ holds worked examples,\n"
                   "one per library, emitted by `gonzalgo profile` from the Kernel\n"
                   "Index.\n\n"
                   "Those examples carry `null` in four fields. Under rule R2 `null`\n"
                   "means not measured and `0` is a positive claim, so the gaps are\n"
                   "left visible rather than filled from a different measurement.\n\n"
                   "Canonical home: https://f-keys.com/gonzalgo/kernel-trust/\n"
                   "Specification CC-BY-4.0; implementations unencumbered.\n")
    ver = json.loads(schema.read_text(encoding="utf-8")).get("title", "")
    return profiles, schema, ver


def description(n_profiles: int) -> str:
    return (
        "<p>A specification for declaring what a body of machine-checked "
        "mathematics rests on.</p>"
        "<p><code>CITATION.cff</code> standardises how to cite a project and SPDX "
        "standardises its licence. Nothing standardises what it <em>rests on</em> "
        "&mdash; whether a theorem is standing on an unfinished proof several "
        "files upstream, or was obtained by trusting a compiler rather than a "
        "kernel. Both look exactly like success and neither is visible to anyone "
        "downstream. A Kernel Trust Profile is that statement, in a fixed shape, "
        "computed from the artifact rather than asserted by its author.</p>"
        "<p>Six design rules keep a profile from becoming a badge. It must be "
        "mechanically recomputable by a third party from the named revision (R1). "
        "Absence is not zero &mdash; <code>null</code> means not measured, while "
        "<code>0</code> is a positive claim that must be backed by a measurement "
        "(R2). Statement and proof dependencies stay separate, because a statement "
        "dependency changes what was proved and a proof dependency changes only "
        "how (R3). Reach is invariant under inlining and factoring while "
        "amplification is not, so a profile must report reach and must not rank by "
        "amplification (R4). There is no composite trustworthiness score: a theorem "
        "either reaches an unfinished proof or it does not, and averaging that "
        "against anything invents precision the measurement does not have (R5). "
        "And it must be emittable by any tool that can compute a declaration "
        "graph, since a format only one program can produce is a file format and "
        "not a standard (R6).</p>"
        f"<p>Includes the JSON Schema and {n_profiles} worked profiles covering "
        "Lean 4 libraries and five Metamath databases &mdash; ZFC, intuitionistic "
        "logic, New Foundations, quantum logic and higher-order logic. Those "
        "examples exist to test the specification against data gathered before the "
        "specification was written; four fields are <code>null</code> across every "
        "profile because those measurements were never taken, which is R2 doing "
        "its job.</p>"
        "<p>A profile carries no claim about correctness, quality or importance "
        "and is not a certificate. It reports provenance: which trust assumptions "
        "a library's theorems actually reach.</p>"
        "<p>Specification CC-BY-4.0; implementations unencumbered. Canonical home: "
        "<a href=\"https://f-keys.com/gonzalgo/kernel-trust/\">"
        "f-keys.com/gonzalgo/kernel-trust/</a></p>")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true",
                    help="mint the DOI (irreversible)")
    args = ap.parse_args()

    profiles, schema, _ = build_bundle()
    size = BUNDLE.stat().st_size
    sha = hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
    print(f"  bundle {BUNDLE.name}: {size:,} bytes, "
          f"{len(profiles)} profiles, schema {schema.name}")
    print(f"  sha256 {sha}")

    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        sys.exit("  ZENODO_TOKEN is not set")

    metadata = {"metadata": {
        "title": ("Kernel Trust Profile 0.1: a machine-readable declaration of "
                  "what a body of machine-checked mathematics rests on"),
        "upload_type": "publication",
        "publication_type": "technicalnote",
        "description": description(len(profiles)),
        "creators": [{"name": "Gonzalez, Vincent", "orcid": ORCID,
                      "affiliation": "F-Keys"}],
        "access_right": "open",
        "license": "cc-by-4.0",
        "version": "0.1",
        "language": "eng",
        "keywords": [
            "formal verification", "specification", "trusted computing base",
            "Lean 4", "Metamath", "provenance", "reproducibility",
            "proof assistant", "axiom of choice", "metadata standard",
            "CITATION.cff", "SPDX",
        ],
        "related_identifiers": [
            {"relation": "isSupplementTo", "identifier": "10.5281/zenodo.21769846"},
            {"relation": "references", "identifier": "10.5281/zenodo.21900625"},
            {"relation": "isDocumentedBy",
             "identifier": "https://f-keys.com/gonzalgo/kernel-trust/"},
            {"relation": "isSupplementedBy",
             "identifier": "https://github.com/zengineco/gonzalgo"},
        ],
        "notes": ("The specification is CC-BY-4.0 and implementations are "
                  "unencumbered. Worked profiles were emitted by gonzalgo 0.5.2; "
                  "rule R6 requires the format be emittable by any tool that can "
                  "compute a declaration graph."),
    }}

    _, dep = call("POST", f"{API}/deposit/depositions", token, metadata)
    dep_id = dep["id"]
    print(f"  created draft {dep_id}")

    call("PUT", f"{dep['links']['bucket']}/{BUNDLE.name}", token,
         BUNDLE.read_bytes(), "application/octet-stream")
    print(f"  uploaded {BUNDLE.name}")

    if args.publish:
        _, pub = call("POST",
                      f"{API}/deposit/depositions/{dep_id}/actions/publish", token)
        print(f"\n  PUBLISHED  doi {pub.get('doi')}")
        print(f"  concept    {pub.get('conceptdoi')}")
        print(f"  {pub['links'].get('record_html', '')}")
    else:
        print(f"\n  draft ready, not published:")
        print(f"    https://zenodo.org/uploads/{dep_id}")
        print("  re-run with --publish to mint the DOI")


if __name__ == "__main__":
    main()
