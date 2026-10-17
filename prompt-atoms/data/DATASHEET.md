# Datasheet — Prompt Atoms & Conflicts
### Following Gebru et al., "Datasheets for Datasets" (2021). V. Gonzalez (ORCID 0009-0005-3640-014X), 2026-10-16.

A dataset of recurring instruction "atoms" mined from public prompt libraries,
each typed to a slot and tagged with frequency and task-family breadth, plus a
measured graph of pairwise conflicts between them.

## Motivation
- **Why created.** Public prompt libraries reuse the same instructions ("Only
  output Markdown", "Do not give warnings") across unrelated tasks, and some of
  those instructions contradict each other. No published dataset captures the
  recurring instruction vocabulary *and* its conflict structure. This fills that.
- **Intended uses.** Studying instruction reuse and conflict; building or
  benchmarking prompt linters/compilers; a reference for prompt authoring.
- **Who.** F-Keys Creative LLC. No external funding.

## Composition
- **Instances.** Two tables.
  - `prompt-atoms` — **257 instruction atoms.** Fields: `id`, `text` (canonical
    phrasing), `slot` (role/method/checks/output/first), `kind`
    (persona/process/behavior/format), `negative` (a prohibition), `frequency_prompts`
    (how many source prompts use it), `n_variants` (distinct phrasings observed),
    `n_task_families` (distinct task types it spans), `example_variant`.
  - `prompt-conflicts` — **32 conflict pairs.** Fields: `atom_a_id/text`,
    `atom_b_id/text`, `reason` (why they cannot both hold).
- **Slot distribution.** method 83, checks 78, output 64, role 25, first 7.
- **Not personal data.** Instructions only; no users, PII, or private content.
- **Sampling.** Derived from two public corpora (below), not a sample of a larger
  hidden set. Frequencies are relative to those corpora and will differ on others.

## Collection process
- **Sources.** Fabric (265 task patterns; MIT) and prompts.chat (2,425 community
  prompts; CC0) — 195 task templates in total after merging.
- **Method.** Line/sentence-level extraction → canonicalisation into atoms →
  slot typing → frequency and task-family counts. Conflicts named and judged by a
  model, then rule-reviewed (personas never conflict; near-identical wordings merged).
- **Timeframe.** Snapshot built October 2026.

## Preprocessing / cleaning
- Near-duplicate phrasings merged into one atom with recorded variants.
- Prompts written to make a model drop its rules (jailbreaks, e.g. DAN) were
  excluded at source.
- **Known limitation:** atom extraction is model-assisted and imperfect; a human
  audit rate is not yet reported. Frequencies are corpus-shaped, not universal.
- **Build-stage note:** the live coldHat worker serves a 329-atom build; this
  dataset uses the provenance-complete 257-atom consolidation (`library.json`).
  Use one number consistently in any write-up.

## Uses
- **Suitable.** Prompt-engineering research, linter/compiler development, teaching.
- **Not suitable.** Claims about model behaviour (this is about prompts, not
  models) or about prompt effectiveness (frequency ≠ efficacy — see the literature).

## Distribution
- **License: CC BY 4.0** (https://creativecommons.org/licenses/by/4.0/). Free to
  use with attribution to Vincent Gonzalez / F-Keys Creative LLC. Source corpora
  (MIT + CC0) permit it.
- **Channels:** Zenodo (DOI, for citeability — see ZENODO.md), the F-Keys site,
  and optionally a data marketplace (Apify/Kaggle/HuggingFace).

## Maintenance
- Regenerate with `python dataset/build.py` from the atom library. Version by date.
- Contact: via f-keys.com.

## Provenance of claims
Built from `atoms/data/library.json` + `worker/src/atoms-data.json`. The conflict
graph and slot typing are this project's work; the raw instructions are the source
authors', under their licenses (credited above).
