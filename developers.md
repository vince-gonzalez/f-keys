# Developer resources

> F-Keys developer resources: the OpenAPI description of 35 published datasets, the PyPI and npm packages, the gonzalgo GitHub Action, llms.txt, and Markdown and JSON content negotiation. No API keys, because there is no hosted API.

Canonical: https://f-keys.com/developers.html

Everything here is a package you install or a file you fetch.
There is nothing to sign up for.

## Start here

| Field | Value |
| --- | --- |
| OpenAPI | [/openapi.json](https://f-keys.com/openapi.json) — every published dataset, its shape and its licence |
| For agents | [/llms.txt](https://f-keys.com/llms.txt) — the whole catalogue as plain text, including when to reach for each thing |
| Site map | [/sitemap.xml](https://f-keys.com/sitemap.xml) |
| Documentation | [/Docs.html](https://f-keys.com/Docs.html) — setup, configuration and troubleshooting |
| Source | [github.com/zengineco](https://github.com/zengineco) |
| Questions | [hello@f-keys.com](mailto:hello@f-keys.com) |

## There are no API keys, and that is not an omission

Every F-Keys product either runs in your browser or installs on your
machine. None of them calls a server of ours, because there is no server of
ours — this site is a folder of static files behind a CDN. So there is
nothing to authenticate, no rate limit to raise, no sandbox to provision and
no quota to buy.

What that buys you: the packages work offline, they keep working if this
site goes away, and nothing you compute with them is reported back here. What
it costs you: there is no endpoint to POST to. If you need one, the source is
public and the licence is permissive for most of it.

## Install

| Field | Value |
| --- | --- |
| gonzalgo | pip install gonzalgo — axiom provenance for Lean 4 and Metamath |
| keyj | pip install keyj — tablature to notes, render, and play |
| plumhud | pip install plumhud — miner fleet monitor |
| moonbeam-miner | pip install moonbeam-miner — NerdMiner discovery and vitals |
| opticquiz-cvd | npm i opticquiz-cvd — colour-vision simulation and daltonisation |
| @f-keys/tip-widget | npm i @f-keys/tip-widget — the TipStreams widget |

## In your pipeline

The [gonzalgo-trust-audit](https://github.com/marketplace/actions/gonzalgo-trust-audit)
Action fails a build when a proof rests on something unfinished. Three lines of
workflow, or --fail-on-trust if you would rather call the CLI
yourself.

## The published data

Thirty-five JSON documents are served from this domain and described in
[openapi.json](https://f-keys.com/openapi.json). They are static files: fetch them,
cache them, mirror them.

| Field | Value |
| --- | --- |
| Measurement tables | Thirteen tables behind the papers — the [Kernel Index](https://f-keys.com/gonzalgo/kernel-index/), the [Dominator Table](https://f-keys.com/gonzalgo/dominator-table/) and the rest. Each is one object carrying its own version, sha256, licence and series DOI beside its rows, so you can cite it and tell whether it changed under you. |
| Kernel Trust Profile | The [0.1 schema](https://f-keys.com/gonzalgo/kernel-trust/kernel-trust-0.1.schema.json) and fourteen profiles conforming to it, one per library measured. |
| Status | [/status/latest.json](https://f-keys.com/status/latest.json) — the daily snapshot behind the [status page](https://f-keys.com/status/). Repository traffic is owner-only and is not in it. |

The measurement data is CC BY 4.0. Cite the series DOI in the file rather
than this page, so the citation points at a version.

## The site itself is machine-readable

Every page here serves **Markdown** to anything that asks for it. Send
Accept: text/markdown and you get the content without the window
around it, per [acceptmarkdown.com](https://acceptmarkdown.com),
with Vary: Accept set so a cache cannot hand you the wrong one.

curl -H "Accept: text/markdown" https://f-keys.com/keyj/
A path that does not exist returns a real **404**, and returns it in the
format you asked for. Send Accept: application/json and the error
is JSON with a stable code, a message and hints, rather than an
HTML page you would have to parse to discover you had failed.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
