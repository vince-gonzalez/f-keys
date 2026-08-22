# F-Keys developer resources

> F-Keys developer resources: the OpenAPI description of 35 published datasets, the PyPI and npm packages, the gonzalgo GitHub Action, llms.txt, and Markdown and JSON content negotiation. No API keys, because there is no hosted API.

Canonical: https://f-keys.com/developers.html

Four command-line tools, six packages, and thirty-five JSON
documents. Everything here is a thing you install or a file you fetch, and
there is nothing to sign up for.

## Start here

| Field | Value |
| --- | --- |
| OpenAPI | [/openapi.json](https://f-keys.com/openapi.json) — all 35 documents, each with a typed schema naming its columns |
| For agents | [/llms.txt](https://f-keys.com/llms.txt) — the whole catalogue as plain text, including when to reach for each thing |
| Site map | [/sitemap.xml](https://f-keys.com/sitemap.xml) |
| Product docs | [/Docs.html](https://f-keys.com/Docs.html) — setup, configuration and troubleshooting |
| Source | [github.com/zengineco](https://github.com/zengineco) |
| Questions | [hello@f-keys.com](mailto:hello@f-keys.com) |

## Authentication

**There is none, and none is required.** No API key, no token, no OAuth
flow, no signup. Every request below works from a cold start with no
credentials and no headers:

curl https://f-keys.com/gonzalgo/kernel-index/kernel-index.json
This is not a free tier with a paid one behind it. Every F-Keys product runs
in your browser or installs on your machine, so nothing calls a server of ours
— this site is a folder of static files behind a CDN. There is nothing to
authenticate against because there is nothing running.

What that buys you: the packages work offline, they keep working if this site
goes away, and nothing you compute is reported back here. What it costs you:
there is no endpoint to POST to. If you need one, the source is public.

## Rate limits

**None.** No quota, no 429, and deliberately no
RateLimit headers — publishing a limit nobody enforces would
tell you to throttle against a number that does not exist.

The CDN already sends ETag and Last-Modified, so
use them and a repeat fetch costs you a 304 and no body:

curl -H "If-None-Match: "<etag>"" \
 https://f-keys.com/status/latest.json

Versioning and deprecation
**The URLs are permanent; the data carries the version.** There is no
/v1/ prefix because there is no server to route one.

| Field | Value |
| --- | --- |
| Pin to content | Every document carries a version (the measurement date) and a sha256. Re-measuring republishes the same URL with both changed, so comparing either tells you whether anything moved under you. |
| Pin to a release | Each table carries a seriesDoi resolving to an immutable Zenodo deposit. Cite that, not this page. |
| Breaking changes | Fields are added, never removed or retyped. A field that has to go is announced in the [working log](https://f-keys.com/log/) and kept for at least **180 days** after that entry. |
| Deprecation signal | A path scheduled for removal is served with the Deprecation and Sunset headers of RFC 8594 and RFC 9745, and listed under x-versioning.deprecated in [openapi.json](https://f-keys.com/openapi.json). That list is currently empty. |

## The command line

Four of these are real CLIs, not libraries with a script attached. Each does
its whole job from a terminal, which is the point: an agent can drive them
without an integration.

**pip install gonzalgo**
gonzalgo trust *path* every theorem reaching a sorry
gonzalgo why *decl* *axiom* shortest labelled path to an axiom
gonzalgo trust *path* --fail-on-trust exit non-zero in CI
**pip install keyj**
keyj tab solo.txt -o song.txt tablature in, note names out
keyj render song.txt out.wav the sequence, at a tempo
keyj show song.txt what is in a sequence
**pip install moonbeam-miner**
moonbeam scan find the NerdMiners on this network
moonbeam watch their vitals, live
**pip install plumhud**
plumhud the overlay HUD
plumhud --history what the fleet has been doing
In a pipeline, the
[gonzalgo-trust-audit](https://github.com/marketplace/actions/gonzalgo-trust-audit)
Action is three lines of workflow and fails the build when a proof rests on
something unfinished.

## Packages

| Field | Value |
| --- | --- |
| gonzalgo | pip install gonzalgo — axiom provenance for Lean 4 and Metamath. Apache-2.0. |
| keyj | pip install keyj — tablature to notes, render, and play. |
| plumhud | pip install plumhud — miner fleet monitor. |
| moonbeam-miner | pip install moonbeam-miner — NerdMiner discovery and vitals. |
| opticquiz-cvd | npm i opticquiz-cvd — colour-vision simulation and daltonisation. |
| @f-keys/tip-widget | npm i @f-keys/tip-widget — the TipStreams widget. |

## The published data

Thirty-five JSON documents, every one described in
[openapi.json](https://f-keys.com/openapi.json) with a typed schema that names its
columns — so a function-calling agent knows a table has a
library string and a theorems integer before it
fetches half a megabyte to find out.

| Field | Value |
| --- | --- |
| Measurement tables | Thirteen tables behind the papers — the [Kernel Index](https://f-keys.com/gonzalgo/kernel-index/), the [Dominator Table](https://f-keys.com/gonzalgo/dominator-table/) and the rest. One object each, carrying its version, sha256, license and seriesDoi beside its rows. CC BY 4.0. |
| Kernel Trust Profile | The [0.1 schema](https://f-keys.com/gonzalgo/kernel-trust/kernel-trust-0.1.schema.json) and fourteen profiles conforming to it, one per library measured. |
| Status | [/status/latest.json](https://f-keys.com/status/latest.json) — the daily snapshot behind the [status page](https://f-keys.com/status/). Repository traffic is owner-only and is not in it. |

# the whole surface, as an agent would discover it
curl https://f-keys.com/openapi.json | jq '.paths | keys'

# one table, and the columns it declares
curl -s https://f-keys.com/gonzalgo/kernel-index/kernel-index.json | jq '.rows[0]'

# check whether it moved since you last looked
curl -s https://f-keys.com/gonzalgo/kernel-index/kernel-index.json | jq -r '.version, .sha256'

The site itself is machine-readable
Every page here serves **Markdown** to anything that asks. Send
Accept: text/markdown and you get the content without the window
around it, per [acceptmarkdown.com](https://acceptmarkdown.com),
with Vary: Accept set so a cache cannot hand you the wrong one.

curl -H "Accept: text/markdown" https://f-keys.com/keyj/
A path that does not exist returns a real **404** in the format you asked
for. Anything under a data path — a .json URL,
/api, /v1 — errors as JSON even when the client
sends no Accept at all, because most of them do not:

curl https://f-keys.com/gonzalgo/no-such-table.json

{
 "error": {
 "code": "not_found",
 "message": "No resource exists at /gonzalgo/no-such-table.json",
 "status": 404,
 "path": "/gonzalgo/no-such-table.json",
 "hints": [ "..." ]
 }
}
The code is stable and machine-readable, the
hints name the three places a lost agent can recover from, and the
envelope is the one under components.schemas.Error in the
specification.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
