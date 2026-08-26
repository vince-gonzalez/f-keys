```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                            ║
║                    ██████╗  █████╗ ████████╗███████╗██╗  ██╗██╗████████╗                   ║
║                   ██╔════╝ ██╔══██╗╚══██╔══╝██╔════╝██║ ██╔╝██║╚══██╔══╝                   ║
║                   ██║  ███╗███████║   ██║   █████╗  █████╔╝ ██║   ██║                      ║
║                   ██║   ██║██╔══██║   ██║   ██╔══╝  ██╔═██╗ ██║   ██║                      ║
║                   ╚██████╔╝██║  ██║   ██║   ███████╗██║  ██╗██║   ██║                      ║
║                    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝                      ║
║                                                                                            ║
║                           three gates a linter will not give you                           ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```
Three gates for defects a linter does not have an opinion about, because
none of them is a syntax error. Each one exists because a real person read
something and could not.

| Gate | Fails the build when |
|---|---|
| `typefloor` | Type is declared below a readable floor (13px by default) |
| `contrast-gate` | A declared colour cannot reach 4.5:1 on any surface the file also declares |
| `deadname-gate` | A retired name reaches anything a human reads |

## Install

```
pip install gatekit
```

## Use

```
typefloor ./src                  # every CSS and inline declaration
contrast-gate ./src              # WCAG 4.5:1 against declared surfaces
deadname-gate ./src              # a name that should be gone
```

Each exits non-zero on a finding and prints the file and line. `--list`
shows every offender rather than the summary.

## Why these three

**typefloor.** Six-point type is not a style choice. This was written after
the same reader reported the same thing more than once, and the first time it
was pointed at a folder it found every violation immediately — what was
missing was never the tool, it was anything that pulled it.

**contrast-gate.** It reads CSS custom properties — `--ink: #hex` against
`--bg: #hex` — and reports the best surface each ink can reach. Dark grey on
navy measured 2.64:1 where body text needs 4.5, and a person found that, not
a build.

It does **not** read literal `color:` declarations. A stylesheet using
neither has nothing to compare, and it says so and exits 0 — which in CI
reads as a pass on a site nobody checked. Pass `--require-pairs` to fail
instead when nothing was found. The Action sets it.

**deadname-gate.** Fails a build when a name that should be gone reaches a
title, a footer, a byline, alt text or a comment — while leaving machine
identifiers alone, because renaming a repository path or a published
artifact breaks working links or contradicts a deposited record. Both halves
matter: a gate that cannot tell those apart gets switched off.

Written for a company rename. It is the same shape as the problem of a person
changing their name and finding it in three hundred places, which is the
harder version and the one worth getting right.

## Configuration

Each gate reads a JSON file of exceptions, so a deliberate choice is
recorded with a reason rather than silently re-flagged.

```
typefloor ./src --config typefloor.json
contrast-gate ./src --config contrast.json
deadname-gate ./src --config deadname_gate.json
```

`TYPEFLOOR_CONFIG`, `CONTRAST_CONFIG` and `DEADNAME_CONFIG` do the same.

## In CI

```yaml
- run: pip install gatekit
- run: typefloor ./src
- run: contrast-gate ./src --require-pairs
- run: deadname-gate ./src
```

There are Actions too, in `.github/actions/` of the source repository.

## A note on the argument

An earlier version ignored a bare path and scanned its own directory
instead, then printed `OK`. A gate that reports a pass on a tree it never
opened is worse than no gate, so a positional path is now the root. If you
pinned an earlier build, check what it is actually reading.

## Licence

MIT.
