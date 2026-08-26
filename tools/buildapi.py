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
#
# status/data is the exception. A scheduled Action writes one dated
# snapshot there every morning, so documenting them one path at a time
# would add an operation a day, grow the spec without bound, and make it
# stale by 01:36 UTC daily - a build breaking every night on nothing.
# The endpoint is status/latest.json; the archive is a naming convention,
# described once in that operation rather than enumerated.
SKIP_DIRS = {"__pycache__", "_build", "node_modules", "data"}

ARCHIVE_NOTE = (" Prior days are archived at /status/data/YYYY-MM-DD.json "
                "using the same shape; this file is a copy of the most "
                "recent one.")


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
            # os.walk hands back directories in filesystem order, which is
            # not the same order on Windows and on the Linux runner. Sorting
            # here makes the generated spec byte-identical on both, so
            # --check is comparing content rather than platform.
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
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
    # Same recognition as dataset_schema(): a reconstructed day has a
    # summary and no uptime, because nothing was checking on that date.
    if "summary" in doc and ("uptime" in doc or doc.get("backfilled")):
        return ("Status snapshot",
                "Uptime, package installs, publication views and aggregate "
                "traffic. Repository traffic is owner-only and is not here."
                + ARCHIVE_NOTE)
    return os.path.basename(path), ""


MAX_DEPTH = 4
SAMPLE = 40


def json_type(value):
    if value is None:
        return None                      # carries no type information
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def infer(value, depth=0, labels=None):
    """A typed schema read off the data itself.

    An agent doing function calling needs to know a table has a `library`
    column of strings before it fetches half a megabyte to find out. The
    types are not asserted from a spec written alongside the data, they
    are read out of the data, so they cannot describe a column that is
    not there.
    """
    kind = json_type(value)

    if kind == "object" and depth < MAX_DEPTH:
        props, required = {}, []
        for key, item in value.items():
            if json_type(item) is None:
                continue
            props[key] = infer(item, depth + 1, labels)
            if labels and key in labels:
                props[key]["title"] = labels[key]
            required.append(key)
        out = {"type": "object", "properties": props}
        if required:
            out["required"] = sorted(required)
        return out

    if kind == "array" and depth < MAX_DEPTH:
        items = [v for v in value[:SAMPLE] if json_type(v) is not None]
        if not items:
            return {"type": "array"}
        if all(isinstance(v, dict) for v in items):
            # union the keys across the sample, so a column that is only
            # populated on some rows is described but not made required
            props, counts = {}, {}
            for row in items:
                for key, item in row.items():
                    if json_type(item) is None:
                        continue
                    if key not in props:
                        props[key] = infer(item, depth + 2, labels)
                        if labels and key in labels:
                            props[key]["title"] = labels[key]
                    counts[key] = counts.get(key, 0) + 1
            required = sorted(k for k, c in counts.items() if c == len(items))
            schema = {"type": "object", "properties": props}
            if required:
                schema["required"] = required
            return {"type": "array", "items": schema}
        return {"type": "array", "items": infer(items[0], depth + 1, labels)}

    if kind in (None, "object", "array"):
        return {"type": kind or "object"}
    return {"type": kind}


def schema_name(path):
    """A stable, unique name per document, for $ref and for the tools
    that turn an operation into a function signature."""
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    rel = rel[:-len(".json")] if rel.endswith(".json") else rel
    parts = [p for p in rel.replace(".", "_").split("/") if p]
    # drop the directory when it just repeats the file name
    if len(parts) >= 2 and parts[-1] == parts[-2]:
        parts = parts[:-1]
    return "".join(w.capitalize() for p in parts
                   for w in p.replace("-", "_").split("_"))


# A JSON Schema document describes other documents, so its own contents
# are keywords rather than data. Inferring it produced a property
# literally named `$ref` whose value was an object, which is the one
# shape a resolver walking this file must never meet. It gets described
# by hand as what it is.
META_SCHEMA = {
    "type": "object",
    "title": "JSON Schema document",
    "description": "A JSON Schema (draft 2020-12). Its keys are schema "
                   "keywords, not data fields - fetch it and hand it to a "
                   "validator rather than reading it as a record.",
    "required": ["$schema", "title"],
    "properties": {
        "$schema": {"type": "string", "format": "uri",
                    "description": "The draft this document conforms to."},
        "$id": {"type": "string", "format": "uri"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "type": {"type": "string"},
        "required": {"type": "array", "items": {"type": "string"}},
        "properties": {"type": "object",
                       "description": "The fields a conforming document "
                                      "carries. Keywords, not values."},
        "$defs": {"type": "object"},
        "additionalProperties": {"type": "boolean"},
    },
}


# The status snapshot is a REPORT, not a dataset, and inferring its shape
# broke the build every time a source had a different day. Cloudflare's
# 24-hour bot sample returns whichever categories it saw, so "Security"
# became a schema property one day and "Accessibility" the next. A failed
# pypistats call replaced `daily`/`weekly`/`monthly` with `error`. GitHub
# traffic succeeding removed `traffic_error`. None of that is a change to
# the format; it is the weather.
#
# So this one is described rather than measured. Optional things are
# optional, and the maps whose KEYS are data are declared as maps.
STATUS_SCHEMA = {
    "type": "object",
    "title": "Status snapshot",
    "required": ["date", "generated_at", "summary"],
    "properties": {
        "date": {"type": "string", "format": "date"},
        "generated_at": {"type": "string"},
        "mode": {"type": "string", "enum": ["daily", "weekly"]},
        "redacted": {"type": "string",
                     "description": "What this published copy leaves out."},
        "summary": {
            "type": "object",
            "description": "The headline figures. A key is absent when the "
                           "source behind it did not report.",
            "additionalProperties": {"type": ["integer", "null"]},
        },
        "uptime": {"type": "array", "items": {
            "type": "object",
            "required": ["name", "up"],
            "properties": {"name": {"type": "string"},
                           "url": {"type": "string", "format": "uri"},
                           "up": {"type": "boolean"},
                           "ms": {"type": "integer"},
                           "error": {"type": ["string", "null"]}}}},
        "npm": {"type": "array", "items": {"$comment": "package row",
                                           "type": "object"}},
        "pypi": {"type": "array", "items": {"$comment": "package row",
                                            "type": "object"}},
        "github": {"type": "array", "items": {"type": "object"}},
        "zenodo": {"type": "object", "properties": {
            "error": {"type": ["string", "null"]},
            "records": {"type": "array", "items": {"type": "object"}}}},
        "cloudflare": {"type": "object", "properties": {
            "days": {"type": "integer"},
            "error": {"type": ["string", "null"]},
            "sites_omitted": {"type": "integer"},
            "sites": {"type": "array", "items": {"type": "object"}},
            "totals": {"type": "object"},
            "window": {"type": "object"},
            # the keys here are Cloudflare's bot categories, which are
            # data and differ day to day - a map, never named properties
            "bots_24h": {"type": "object",
                         "additionalProperties": {"type": "integer"},
                         "description": "Requests per bot category in the "
                                        "last 24 hours. Keys are "
                                        "Cloudflare's categories and vary."},
            "bots_error": {"type": ["string", "null"]}}},
        "history": {"type": "array", "items": {"type": "object"}},
    },
}


def dataset_schema(doc, title, blurb):
    # A backfilled day carries a summary and no uptime - nothing was
    # checking on that date. It is still a status snapshot, and if it
    # is not recognised as one the generator falls back to inferring
    # it, which is the churn this schema exists to stop.
    if "summary" in doc and ("uptime" in doc or doc.get("backfilled")):
        out = dict(STATUS_SCHEMA)
        out["title"] = title
        if blurb:
            out["description"] = blurb.strip()
        return out
    if "$schema" in doc:
        out = dict(META_SCHEMA)
        out["title"] = title
        if blurb:
            out["description"] = blurb.strip() + " " + META_SCHEMA["description"]
        return out

    """The envelope and its rows, typed, with the table's own column
    labels carried through as titles."""
    labels = {}
    for col in (doc.get("displayed") or []):
        if isinstance(col, dict) and col.get("key") and col.get("label"):
            labels[col["key"]] = col["label"]
    schema = infer(doc, labels=labels)
    schema["title"] = title
    if blurb:
        schema["description"] = blurb.strip()
    return schema


ERROR_SCHEMA = {
    "type": "object",
    "title": "Error",
    "required": ["error"],
    "properties": {"error": {
        "type": "object",
        "required": ["code", "message", "status"],
        "properties": {
            "code": {"type": "string",
                     "description": "Stable machine-readable identifier."},
            "message": {"type": "string"},
            "status": {"type": "integer"},
            "path": {"type": "string"},
            "hints": {"type": "array", "items": {"type": "string"},
                      "description": "Where to look instead."},
        }}},
}


def error_response():
    """A fresh copy per operation: inline schemas must not be
    shared objects, or json.dumps writes one and the readers that
    do resolve see aliasing that is not in the document."""
    import copy
    return copy.deepcopy(_ERROR_RESPONSE)


_ERROR_RESPONSE = {
    "description": "The path does not exist. Returned as JSON when the "
                   "request asks for it, so an agent does not have to "
                   "parse an HTML error page.",
    "content": {"application/json": {
        "schema": ERROR_SCHEMA,
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
    """Each operation, carrying its schema inline.

    These were $refs into components/schemas, which is the tidier
    OpenAPI and the wrong choice here. The tools that turn an operation
    into a function signature - and the readiness checkers that imitate
    them - overwhelmingly do not dereference, so a $ref reads as an
    argument with no type. Every operation is self-contained instead:
    one fetch of one object tells a caller the whole shape.
    """
    out, schemas = {}, {}
    # the paths go out in one fixed order, so the document does not depend
    # on how the tree happened to be walked
    for top, path, doc in sorted(found, key=lambda f: url_for(f[1])):
        title, blurb = describe(doc, path)
        tag = next(t for s, t, _b in SOURCES if s == top)
        name = schema_name(path)
        schemas[name] = dataset_schema(doc, title, blurb)
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
                    "content": {"application/json": {
                        "schema": schemas[name]}},
                },
                "404": error_response(),
            },
        }}
    return out, schemas


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


# -- what an integrator is entitled to rely on ----------------
# An agent will not build against a surface that can change without
# warning, and the honest answer here is unusual enough to be worth
# stating in the document rather than leaving to inference: the URLs
# are permanent, and it is the DATA that carries the version.
VERSIONING = {
    "strategy": "url-path",
    "current": "v1",
    "summary": "Every document is served both at its bare path and under "
               "/v1, byte for byte. Integrate against /v1 for a stable "
               "shape, or against the bare path and pin on the sha256 each "
               "document carries.",
    "detail": "A measurement table is republished at the same URL when it is "
              "re-measured, and its `version` (the measurement date) and "
              "`sha256` both change - the numbers move, the shape does not. "
              "If a shape ever has to change, it appears under /v2 and /v1 "
              "keeps serving the old shape for the notice period. Responses "
              "under a version prefix carry `X-API-Version`. An unknown "
              "version answers 404 with the code `unknown_version` rather "
              "than looking like a mistyped path.",
    "breakingChangePolicy": "Fields are added, not removed or retyped. A "
                            "field that must go is announced in the working "
                            "log at " + SITE + "/log/ and kept for at least "
                            "180 days after that entry.",
    "deprecation": {
        "signal": "A path scheduled for removal is served with the "
                  "`Deprecation` and `Sunset` headers of RFC 8594 and RFC "
                  "9745, and is listed under x-versioning.deprecated here.",
        "noticePeriod": "P180D",
    },
    "deprecated": [],
    "changeLog": SITE + "/log/",
}

# There is no rate limit to report, and inventing a RateLimit header for
# a limit that does not exist would tell an agent to throttle against a
# number nobody enforces. Saying so is more useful than a fiction.
RATE_LIMIT = {
    "enforced": False,
    "summary": "No rate limit. These are static files on a CDN; there is no "
               "quota, no API key and no 429.",
    "detail": "No RateLimit or Retry-After headers are returned, because "
              "there is nothing behind them to enforce. Fetch as needed, "
              "and prefer the ETag and Last-Modified the CDN already sends "
              "so a repeat fetch costs a 304. If a request is ever refused "
              "it is the CDN's own abuse protection, not a published quota.",
    "conditionalRequests": ["ETag", "If-None-Match", "Last-Modified",
                            "If-Modified-Since"],
}


def spec():
    found = datasets()
    documented, _schemas = paths(found)

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "F-Keys published data",
            "version": "1.0.0",
            "summary": "Read-only static datasets. Not a hosted API.",
            "description": DESCRIPTION,
            "contact": {"name": "F-Keys", "email": "hello@f-keys.com",
                        "url": SITE + "/contact.html"},
            "license": {"name": "CC BY 4.0", "identifier": "CC-BY-4.0"},
        },
        "servers": [
            {"url": SITE + "/v1",
             "description": "Version 1. The same documents as the bare paths, "
                            "under a prefix that carries a promise: what is "
                            "served here keeps the shape it has today, and a "
                            "breaking change appears as /v2 while /v1 is "
                            "served with Deprecation and Sunset headers for "
                            "180 days. Responses carry X-API-Version: v1."},
            {"url": SITE,
             "description": "The same files without the version prefix. "
                            "Identical bytes; pin on each document's own "
                            "sha256 or seriesDoi instead of on a path."},
        ],
        "externalDocs": {"url": SITE + "/developers.html",
                         "description": "Developer resources"},
        "tags": [{"name": t, "description": b} for _s, t, b in SOURCES],
        "paths": documented,
        # deliberately empty: every schema is inline on its
        # operation, so nothing here needs resolving
        "components": {"schemas": {}},
        "x-versioning": VERSIONING,
        "x-rate-limit": RATE_LIMIT,
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
