# Kernel Trust Profile

**Version 0.1 (draft) — 2026-08-05**

A machine-readable declaration of what a body of machine-checked mathematics
rests on.

---

## 0. The gap this fills

A proof assistant reports that a proof checks. It does not report that the
theorem is standing on an unfinished proof several files upstream, or that the
result was obtained by trusting a compiler rather than a kernel. Both look
exactly like success, and neither is visible to anyone downstream.

There is a standard way to say how to cite a project (`CITATION.cff`), and a
standard way to say what licence it carries (SPDX). There is no standard way to
say what it *rests on*. Every project states it in prose, or not at all.

A Kernel Trust Profile is that statement, in a fixed shape, computed from the
artifact rather than asserted by its author.

## 1. Scope

A profile describes one library, at one revision, as measured by one tool at one
time. It carries no claim about correctness, quality, or importance, and it is
not a certificate. It reports provenance: which trust assumptions the library's
theorems actually reach.

Consistency is not in scope and cannot be. A profile scopes the risk; it does
not eliminate it.

## 2. Design rules

These are the rules that keep a profile from becoming a badge.

**R1. Mechanically recomputable.** Every number MUST be derivable by a third
party from the named revision using the named tool. No field may hold a value
that only the author could know.

**R2. Absence is not zero.** A profile MUST distinguish "measured, and the count
is zero" from "not measured". `null` means not measured. Omitting a field means
not measured. Writing `0` is a positive claim and MUST be backed by a
measurement.

**R3. Statement and proof stay separate.** Where a dependency is reported, a
profile MUST record whether it enters through a theorem's *statement* or only
through its *proof*. Collapsing the two discards the distinction that makes the
measurement actionable: a statement dependency changes what was proved, a proof
dependency changes only how.

**R4. Reach, not amplification.** Reach — the fraction of a library depending on
an assumption — is invariant under inlining and factoring. Amplification is not:
factoring a shared step into a lemma changes it without changing anything the
library proves. A profile MAY report amplification, MUST report reach, and MUST
NOT rank libraries by amplification.

**R5. No composite scores.** A profile MUST NOT contain a single number summarising
trustworthiness. A theorem either reaches an unfinished proof or it does not;
averaging that against anything else invents precision that the underlying
measurement does not have.

**R6. Tool-agnostic.** A profile MUST be emittable by any tool that can compute
the declaration graph. Nothing in this specification requires a particular
implementation. A format only one program can produce is a file format, not a
standard.

## 3. Format

A profile is a JSON document, conventionally at the repository root as
`kernel-trust.json`, UTF-8, conforming to the schema in `schema/kernel-trust-0.1.schema.json`.

```json
{
  "ktp_version": "0.1",
  "generated_at": "2026-08-05",
  "generated_by": { "tool": "gonzalgo", "version": "0.5.2" },
  "subject": {
    "name": "Mathlib",
    "system": "Lean 4",
    "system_version": "4.32.1",
    "revision": "a1b2c3d",
    "foundation": "dependent type theory"
  },
  "counts": {
    "declarations": 790171,
    "theorems": 437429
  },
  "unfinished": {
    "theorems_reaching": 0,
    "axioms": ["sorryAx"]
  },
  "compiler_trusted": {
    "theorems_reaching": 0,
    "axioms": ["Lean.ofReduceBool", "Lean.ofReduceNat"]
  },
  "assumptions": [
    {
      "name": "Classical.choice",
      "kind": "optional",
      "entry_points": 144,
      "reach": { "theorems": 324808, "fraction": 0.6100 },
      "via": "proof"
    },
    {
      "name": "propext",
      "kind": "foundational",
      "entry_points": null,
      "reach": { "theorems": 437429, "fraction": 1.0 },
      "via": "both"
    }
  ]
}
```

### Fields

`ktp_version` (required) — the version of this specification.

`generated_at` (required) — ISO 8601 date the measurement was taken.

`generated_by` (required) — `tool` and `version`. Identifies what to re-run.

`subject` (required) — what was measured. `revision` SHOULD be a commit hash or
released version, so R1 is satisfiable.

`counts` (required) — `theorems` is the denominator for every `fraction`.

`unfinished` (required) — theorems reaching an unfinished proof from anywhere
upstream, and the axiom names that signal it. `theorems_reaching: 0` is the
claim most worth making and, under R2, the one that must be measured to be
stated.

`compiler_trusted` (required) — theorems reaching a result obtained by trusting
the compiler and runtime rather than the kernel.

`assumptions` (required, may be empty) — one entry per axiom or assumption
reached by any theorem.

- `kind` — `foundational` (the system's own basis, unremarkable), `optional`
  (removable in principle, e.g. choice), or `escape-hatch` (unfinished or
  compiler-trusting).
- `entry_points` — declarations whose own proof cites it, as opposed to
  inheriting it. `null` where not computed.
- `reach` — theorems depending on it at all, and that count over `counts.theorems`.
- `via` — `statement`, `proof`, or `both`, per R3.

## 4. What a profile does not mean

A library reaching 61% of its theorems with the axiom of choice has made a
design decision, not an error. Metamath's `set.mm` tiers countable and dependent
choice separately on purpose and reaches 1.2%; Lean core does not, and its
maintainers have stated that avoiding choice is a deliberate non-goal. Both are
coherent. A profile makes the difference legible; it does not adjudicate it.

Under R5 there is no score, so there is no ranking, so a profile cannot be used
as a league table without leaving the specification.

## 5. Versioning

Additive changes increment the minor version. Any change to the meaning of an
existing field increments the major version. A consumer encountering an unknown
`ktp_version` major MUST NOT interpret the document.

## 6. Prior art

`CITATION.cff` standardises citation metadata; SPDX standardises licence
identifiers; `codemeta.json` standardises software description. Each took a
thing every project stated in prose and gave it a shape. This does the same for
the trust assumptions under a machine-checked result.

The measurements are defined in *Where Formal Libraries Spend Their Axioms*,
https://doi.org/10.5281/zenodo.21769846, which also gives the refactoring
argument behind R4 and the statement/proof separation behind R3.

## 7. Licence

This specification is CC-BY-4.0. Implementations are unencumbered.
