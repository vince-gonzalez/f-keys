#!/usr/bin/env python3
"""
============================================================
buildapi - openapi.json, generated from the files that exist
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
F-Keys has no hosted API: nothing here takes a parameter, no
request is authenticated, and there is no server of ours to
call. Publishing a specification for endpoints that do not
exist would be a lie an agent could not detect until it tried
one, so this does not do that.

What does exist is a read-only data surface that is already
public and already versioned: thirteen gonzalgo measurement
tables, a JSON Schema and fourteen profiles conforming to it,
and the daily status snapshot. Each carries its own name,
description, version and sha256. An agent that wants those
numbers currently has to find them by reading HTML.

So the specification is GENERATED from the files themselves.
Every path in it is a file on disk, every description is the
one the file gives itself, and a dataset that is deleted
disappears from the spec on the next build rather than
becoming a 404 an agent trusts.

WORKFLOW STACK
  1. datasets()  - walk the real JSON, read each envelope
  2. paths()     - one GET per file, described by that file
  3. spec()      - OpenAPI 3.1, no auth, no writes, no fiction
  4. --check     - the committed spec matches the files

Run:  python tools/buildapi.py
      python tools/buildapi.py --check
============================================================
"""

import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "openapi.json")
SITE = "https://f-keys.com"

# Where the public data actually lives. tools/*.json is build
# configuration and .private-snapshot is owner-only, so neither is a
# published endpoint and neither is described here.
SOURCES = [
    ("gonzalgo", "Measurement tables",
     "Published measurements of what formal mathematical libraries rest "
     "on. Each table carries its own version, sha256 and series DOI."),
    ("status", "Status",
     "The daily snapshot behind the status page: uptime, package "
     "installs, paper views and aggregate site traffic."),
]

# The Kernel Trust Profiles are the product rather than a detail of
# it, so profiles/ is walked like everything else.
SKIP_DIRS = {"__pycache__", "_build", "node_modules"}


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def url_for(path):
    return "/" + os.path.relpath(path, ROOT).replace("\\", "/")


def datasets():
    """Every published JSON file, described by what it says it is."""
    found = []
    for top, _tag, _blurb in SOURCES:
        base = os.path.join(ROOT, top)
        if not os.path.isdir(base):
            continue
        for cwd, dirs, names in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for n in sorted(names):
                if not n.endswith(".json"):
                    continue
                path = os.path.join(cwd, n)
                try:
                    doc = read(path)
                except ValueError:
                    continue
                if not isinstance(doc, dict):
                    continue
                found.append((top, path, doc))
    return found


def describe(doc, path):
    """The file's own words, never invented ones."""
    if "$schema" in doc and "title" in doc:
        return doc["title"], doc.get("description", "")
    if "name" in doc and "rows" in doc:
        rows = len(doc.get("rows") or [])
        extra = " {} rows, version {}.".format(rows, doc.get("version", "?"))
        return doc["name"], (doc.get("description", "") or "").strip() + extra
    if "ktp_version" in doc:
        subject = doc.get("subject") or {}
        name = subject.get("name") if isinstance(subject, dict) else None
        return ("Kernel Trust Profile: " + (name or os.path.basename(path)),
                "A Kernel Trust Profile conforming to kernel-trust-0.1, "
                "reporting what one library's proofs depend on.")
    if "summary" in doc and "uptime" in doc:
        return ("Status snapshot",
                "Uptime, package installs, publication views and aggregate "
                "traffic. Repository traffic is owner-only and is not here.")
    return os.path.basename(path), ""


ERROR_RESPONSE = {
    "description": "The path does not exist. Returned as JSON when the "
                   "request asks for it, so an agent does not have to "
                   "parse an HTML error page.",
    "content": {"application/json": {
        "schema": {"$ref": "#/components/schemas/Error"},
        "example": {
            "error": {
                "code": "not_found",
                "message": "No resource exists at /gonzalgo/nope.json",
                "status": 404,
                "hints": [
                    "Every published path is listed in " + SITE + "/openapi.json",
                    "The full site map is at " + SITE + "/sitemap.xml",
                    "A plain-text catalogue is at " + SITE + "/llms.txt",
                ],
            }
        }}},
}


def paths(found):
    out = {}
    for top, path, doc in found:
        title, blurb = describe(doc, path)
        tag = next(t for s, t, _b in SOURCES if s == top)
        out[url_for(path)] = {"get": {
            "summary": title,
            "description": blurb.strip(),
            "operationId": os.path.relpath(path, ROOT)
                             .replace("\\", "_").replace("/", "_")
                             .replace(".json", "").replace("-", "_"),
            "tags": [tag],
            "responses": {
                "200": {
                    "description": title,
                    "content": {"application/json": {"schema": {
                        "$ref": "#/components/schemas/Dataset"
                        if "rows" in doc else "#/components/schemas/Document"}}},
                },
                "404": ERROR_RESPONSE,
            },
        }}
    return out


DESCRIPTION = """\
F-Keys does not run a hosted API. Nothing here takes a parameter, no request
is authenticated, there are no write operations, and there is no rate limit
because there is no server of ours in the path - every file below is static
and served from a CDN.

What this document describes is the read-only data surface that already
exists: the published gonzalgo measurement tables, the Kernel Trust Profile
schema and the profiles conforming to it, and the daily status snapshot. It
is here so an agent can find those files and know their shape without
scraping HTML.

Every path in this specification is generated from a file that exists in the
repository. If a dataset is removed, it leaves this document on the next
build rather than remaining as a promise.

Each measurement table is a single JSON object carrying its own name,
description, version, sha256, licence and series DOI alongside its rows, so a
consumer can cite it and verify it did not change underneath them.

Pages on this site also serve `text/markdown` when the request asks for it
via `Accept`, per acceptmarkdown.com.
"""


def spec():
    found = datasets()
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "F-Keys published data",
            "version": "1.0.0",
            "summary": "Read-only static datasets. Not a hosted API.",
            "description": DESCRIPTION,
            "contact": {"name": "F-Keys", "email": "hello@f-keys.com",
                        "url": SITE + "/contact.html"},
            "license": {"name": "CC BY 4.0",
                        "identifier": "CC-BY-4.0"},
        },
        "servers": [{"url": SITE, "description": "Static files over HTTPS"}],
        "externalDocs": {"url": SITE + "/developers.html",
                         "description": "Developer resources"},
        "tags": [{"name": t, "description": b} for _s, t, b in SOURCES],
        "paths": paths(found),
        "components": {"schemas": {
            "Dataset": {
                "type": "object",
                "description": "A published measurement table.",
                "required": ["name", "version", "sha256", "rows"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "version": {"type": "string",
                                "description": "The measurement date."},
                    "sha256": {"type": "string",
                               "description": "Checksum of the rows, so a "
                                              "consumer can tell whether the "
                                              "table changed."},
                    "url": {"type": "string", "format": "uri"},
                    "seriesDoi": {"type": "string", "format": "uri"},
                    "license": {"type": "string", "format": "uri"},
                    "producedBy": {"type": "object"},
                    "measured": {"type": "object"},
                    "fields": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                },
            },
            "Document": {"type": "object",
                         "description": "A JSON document whose shape is "
                                        "given by its own $schema or "
                                        "ktp_version field."},
            "Error": {
                "type": "object",
                "required": ["error"],
                "properties": {"error": {
                    "type": "object",
                    "required": ["code", "message", "status"],
                    "properties": {
                        "code": {"type": "string",
                                 "description": "Stable machine-readable "
                                                "identifier."},
                        "message": {"type": "string"},
                        "status": {"type": "integer"},
                        "hints": {"type": "array",
                                  "items": {"type": "string"},
                                  "description": "Where to look instead."},
                    }}},
            },
        }},
    }


def render():
    return json.dumps(spec(), indent=2, ensure_ascii=False) + "\n"


def main():
    text = render()
    if "--check" in sys.argv:
        old = io.open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
        if old != text:
            print("buildapi: openapi.json is stale - run "
                  "python tools/buildapi.py")
            return 1
        print("buildapi: ok")
        return 0

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    n = len(spec()["paths"])
    print("buildapi: openapi.json, {} documented paths".format(n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
