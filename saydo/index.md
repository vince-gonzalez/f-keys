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

## A receipt, actually

This is the receipt for saydo verify certivl, from the repository. Thirteen rows: the declaration it was checked against, the captured tool definitions, what the monitor could and could not see, one row per invariant, and a close. Each row carries the hash of the row before it.

| # | row |  | prev_hash | row_hash |
| --- | --- | --- | --- | --- |
| 1 | open | pkg:pypi/certivl@0.2.0 | 31b446b87a387b3d… | 2911aee89d746f02… |
| 2 | capture |  | 2911aee89d746f02… | 8bbcbdebf275fae5… |
| 3 | monitor |  | 8bbcbdebf275fae5… | 8db9473951715e22… |
| 4 | verdict | refusal.scope | 8db9473951715e22… | a192845eb5d858e8… |
| 5 | verdict | network.none | a192845eb5d858e8… | 94ff9d07b07e1140… |
| 6 | verdict | writes.none | 94ff9d07b07e1140… | 2792b46310d90e1e… |
| 7 | verdict | reads.none | 2792b46310d90e1e… | 6953d604c4a27794… |
| 8 | verdict | subprocess.none | 6953d604c4a27794… | fe0193b67cfeab17… |
| 9 | verdict | answers.deterministic | fe0193b67cfeab17… | e83fd3722b937d43… |
| 10 | verdict | errors.are-values | e83fd3722b937d43… | 8d7fb1429449889e… |
| 11 | verdict | undecided.on-overlap | 8d7fb1429449889e… | 27850d284c2f007b… |
| 12 | verdict | decimal.read-exactly | 27850d284c2f007b… | 6f174eaa56827918… |
| 13 | close | tally {'pass': 9} | 6f174eaa56827918… | 754a675f79ea0f92… |

Every prev_hash above equals the row_hash on the line before it — checked, not asserted. Change any row and every hash below it stops matching, which is the whole mechanism. Paste it into verifier/index.html and it checks offline, with no account and no request to anybody.

## What the monitor admits it cannot see

Row 3 is not a result. It is the harness recording its own blind spots — that it observes filesystem opens and socket connects at the host process, and does **not** observe activity below the Python runtime, such as a native extension. An invariant it did not exercise is reported not-covered rather than passed.

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
