# F-Keys developer resources

> F-Keys developer resources: the OpenAPI description of 31 published documents, the PyPI and npm packages, the gonzalgo GitHub Action, llms.txt, and Markdown and JSON content negotiation. No API keys, because there is no hosted API.

Canonical: https://f-keys.com/developers.html

Four command-line tools, sixteen PyPI packages, nineteen on npm, and a shelf of published
JSON. Everything here is a thing you install or a file you fetch, and there is
nothing to sign up for.

## Start here

| Field | Value |
| --- | --- |
| OpenAPI | [/openapi.json](https://f-keys.com/openapi.json) — every published document, each with a typed schema naming its columns |
| For agents | [/llms.txt](https://f-keys.com/llms.txt) — the whole catalogue as plain text, including when to reach for each thing |
| Site map | [/sitemap.xml](https://f-keys.com/sitemap.xml) |
| Product docs | [/Docs.html](https://f-keys.com/Docs.html) — setup, configuration and troubleshooting |
| Source | [github.com/vince-gonzalez](https://github.com/vince-gonzalez) |
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

Every document is served twice, byte for byte: at its bare path, and
under /v1. Integrate against whichever suits you.

# the same bytes, and the second carries a version stamp
curl https://f-keys.com/gonzalgo/kernel-index/kernel-index.json
curl -i https://f-keys.com/v1/gonzalgo/kernel-index/kernel-index.json | grep -i x-api-version

Under /v1What is served there keeps the shape it has today.
A breaking change appears as /v2 while /v1 keeps
serving the old shape. Responses carry X-API-Version: v1, and a
version that does not exist answers 404 with the code
unknown_version rather than looking like a typo.
Pin to contentEvery document carries a version
(the measurement date) and a sha256. Re-measuring republishes the
same URL with both changed, so comparing either tells you whether anything moved
under you.
Pin to a releaseEach table carries a seriesDoi
resolving to an immutable Zenodo deposit. Cite that, not this page.
Breaking changesFields are added, never removed or retyped. A
field that has to go is announced in the [working log](https://f-keys.com/log/) and
kept for at least **180 days** after that entry.
Deprecation signalA path scheduled for removal is served with
the Deprecation and Sunset headers of RFC 8594 and RFC
9745, and listed under x-versioning.deprecated in
[openapi.json](https://f-keys.com/openapi.json). That list is currently empty.


The command line
Four of them, below. Each is a real CLI rather than a library with a script
attached, and does its whole job from a terminal, which is the point: an agent
can drive them without an integration.

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

Sixteen on PyPI. Every one installs from the public index, with no account
and no registration step.

| Field | Value |
| --- | --- |
| gonzalgo | pip install gonzalgo — axiom provenance for Lean 4 and Metamath. Apache-2.0. |
| mmforge | pip install mmforge — find avoidable axiom dependencies in Metamath, and build the proofs that remove them. |
| loadbearing | pip install loadbearing — what a claim asserts, separated from what its derivation consumed. |
| axsent | pip install axsent — what a formal library assumes, read from Rocq, Agda and Isabelle source, with nothing built. |
| certivl | pip install certivl — certified interval arithmetic: an enclosure that turns a computed inequality into a proof. |
| authorecon | pip install authorecon — reconcile published work against every place it lives, for any ORCID, from public sources. |
| saydo | pip install saydo — run a tool against the behavioural contract its author signed, and emit a receipt anyone can verify. |
| ishihara | pip install ishihara — pseudoisochromatic colour-vision plates, reproducible from a seed. |
| opticquiz-cvd | pip install opticquiz-cvd — the colour-accessibility engine, the same maths as the npm package. |
| legible | pip install legible — three build gates: unreadable type, unreadable colour, a retired name. |
| openapi-drift | pip install openapi-drift — has your API drifted from its spec, and can a machine still read it? |
| changewatch | pip install changewatch — a doorbell for your published work. Silent until somebody else acts. |
| keyj | pip install keyj — tablature to notes, render, and play. |
| remapwrap | pip install remapwrap — build a RemapWrap control surface from a folder of samples or a list of shortcuts. |
| plumhud | pip install plumhud — miner fleet monitor. |
| moonbeam-miner | pip install moonbeam-miner — NerdMiner discovery and vitals. |

Nineteen on npm. Most of them are the OpticQuiz colour engine published one
name per deficiency, so somebody searching for protanopia finds
it; these are the entry points.

| Field | Value |
| --- | --- |
| opticquiz-cvd | npm i opticquiz-cvd — colour-vision simulation and daltonisation. |
| opticquiz-cvd-mcp | npm i opticquiz-cvd-mcp — the same engine as callable tools for an LLM. |
| opticquiz-eye | npm i opticquiz-eye — a one-line widget that lets a visitor re-colour your site. |
| keyjockey | npm i keyjockey — tablature to notes: eight tunings, capo offsets, MIDI and frequency. npm only. |
| @f-keys/tip-widget | npm i @f-keys/tip-widget — the TipStreams widget. |

## Upstream, merged

The measurements feed back into the library they measure. Eight pull requests
to [metamath/set.mm](https://github.com/metamath/set.mm)
— the Metamath Proof Explorer's canonical database, reviewed and merged by
its own maintainers — each remove an avoidable axiom-of-choice dependency
that the tooling on this page located:

| Field | Value |
| --- | --- |
| [#5442](https://github.com/metamath/set.mm/pull/5442) | Remove the ax-ac dependency from difelsiga — merged 2026-08-19 |
| [#5448](https://github.com/metamath/set.mm/pull/5448) | Drop the ax-ac dependency from omeiunle — merged 2026-08-21 |
| [#5447](https://github.com/metamath/set.mm/pull/5447) | Avoid ax-ac in sigaclci directly — merged 2026-08-21 |
| [#5445](https://github.com/metamath/set.mm/pull/5445) | Shorten madefi and drop its ax-ac dependency — merged 2026-08-21 |
| [#5443](https://github.com/metamath/set.mm/pull/5443) | Add fnrndomnum, and prove fnrndomg from it — merged 2026-08-24 |
| [#5458](https://github.com/metamath/set.mm/pull/5458) | Drop the ax-ac dependency from fnct, dmct and ffsrn — merged 2026-08-26 |
| [#5446](https://github.com/metamath/set.mm/pull/5446) | Drop the ax-ac dependency from disjinfi — merged 2026-08-30 |
| [#5466](https://github.com/metamath/set.mm/pull/5466) | Add imadomnum, and drop the ax-ac dependency from fimact — merged 2026-09-01 |

Two more set.mm pull requests are open in review, along with
[#203](https://github.com/metamath/metamath-exe/pull/203)
against metamath/metamath-exe — the C source of the Metamath program
itself, rather than the database — and two
[winget-pkgs](https://github.com/microsoft/winget-pkgs/pulls?q=is%3Apr+author%3Avince-gonzalez)
package submissions. Open means open — nothing here is claimed merged
until its maintainers say so.

## The published data

Every published document is described in
[openapi.json](https://f-keys.com/openapi.json) with a typed schema that names its
columns — so a function-calling agent knows a table has a
library string and a theorems integer before it
fetches half a megabyte to find out.

| Field | Value |
| --- | --- |
| Measurement tables | Fifteen tables behind the papers — the [Kernel Index](https://f-keys.com/gonzalgo/kernel-index/), the [Dominator Table](https://f-keys.com/gonzalgo/dominator-table/) and the rest. One object each, carrying its version, sha256, license and seriesDoi beside its rows. CC BY 4.0. |
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
