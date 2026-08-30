# SayDo

> Prove a tool behaves as it says.

Canonical: https://f-keys.com/saydo/

Prove a tool behaves as it says.

| Field | Value |
| --- | --- |
| Status | Working proof of concept — name provisional |
| Declarations | 5 F-Keys servers, 4 third-party — all draft |
| Receipts | Unsigned |
| Invariant types | 10 in the current draft |
| Licence | Apache-2.0 on the open layers |
| Source | vince-gonzalez/saydo |

## The gap

Signing and provenance prove a tool’s code is what the publisher
released. They do not prove the tool behaves as its description promises.
Tool poisoning, capability rug-pulls and silent behavioral drift are one
problem wearing three names: the distance between what a tool declares and
what it does.

The provenance standards say so themselves. **TBOM** states it cannot
verify that tool behavior matches descriptions. **CTMS** states it verifies
that a tool’s claims have not changed, not that they are true. That
out-of-scope line is what this is for.

SayDo does not replace either. It extends them: a declaration binds to the
same tool-definition digests a Tool Bill of Materials already records, and
attaches to one without changing its schema.

## Four layers

| Field | Value |
| --- | --- |
| Declaration | A signed, machine-readable contract per tool: the behavior it is permitted to show — no network, writes only here, deterministic, returns errors as values. Ten invariant types in the current draft. |
| Conformance | A harness exercises the tool under observation — valid calls, adversarial input, egress and filesystem monitoring — and reports pass, fail or **not-covered** per invariant. It cannot prove an invariant it did not exercise, and it says so rather than passing it. |
| Receipt | Every run emits a hash-chained record, one row per verdict, chained by row_hash = sha256(prev + row). Edit one row and the chain breaks at it. An auditor re-verifies it in a browser — no account, no request to us. |
| Trust mark | A “Warranted” badge served from the registry, linking to the full findings rather than a bare grade, with expiry and revocation. **Not built yet.** |

## Run it

Install one of the covered servers, then put it under SayDo. The command
captures the tool definitions, exercises the server, and writes a receipt.

**saydo verify certivl**
 certivl CONFORMANT
 tally {'pass': 9}
 receipt receipts/certivl.receipt.jsonl
 head 353e94cd497115aa49e10ab76874ab7bd9645fed…
A harness that only ever passes is worth nothing, so it ships with a server
built to fail. saydo selfcheck runs that one and requires the
harness to catch every violation — the same discipline the rest of this
catalogue is built on, pointed at itself.

## What it is not, yet

This is a working proof of concept and the name is provisional. Every
declaration currently carries status: "draft". Every receipt is
unsigned. Nothing here is a claim of conformance about anybody’s
software, including ours, and the trust mark does not exist.

Those sentences are on this page in the same size type as the rest, because
a tool whose entire purpose is the distance between what software claims and
what it does would be a poor place to start overstating.

## Prior art it builds on

TBOM v1.0.2, Jason M. Lovell, 2026 —
[10.5281/zenodo.18459260](https://doi.org/10.5281/zenodo.18459260).
CTMS 1.0, George Kanellopoulos, 2026 —
[gkanellopoulos/ctms](https://github.com/gkanellopoulos/ctms).
Both are provenance; both state that verifying behavior against the metadata
is out of their scope.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
