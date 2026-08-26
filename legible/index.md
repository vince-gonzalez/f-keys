# legible

> Three gates a linter will not give you.

Canonical: https://f-keys.com/legible/

Three gates a linter will not give you.

| Field | Value |
| --- | --- |
| Install | pip install legible |
| Licence | MIT |
| Commands | typefloor, contrast-gate, deadname-gate |
| Actions | typefloor, contrast-gate, deadname-gate, cvd-palette |
| Source | vince-gonzalez/f-keys |

## What it does

Three build gates for defects a linter has no opinion about, because none of
them is a syntax error. Each one exists because a person read something and
could not.

**pip install legible**
typefloor ./src type below a readable floor
contrast-gate ./src colour that cannot be read on its surface
deadname-gate ./src a name that should be gone
The rename gate is the unusual one
It fails a build when a retired name reaches a title, a footer, a byline,
alt text or a comment — while leaving machine identifiers alone, because
renaming a repository path or a published artifact breaks working links or
contradicts a deposited record. Both halves matter. A gate that cannot tell
those apart gets switched off within a week.

Written for a company rename. It is the same shape as the problem of a
person changing their name and finding it in three hundred places, which is the
harder version and the one worth getting right.

## It will not tell you it passed when it did not

All three once reported OK on a directory they had never
opened, because a bare path argument was ignored and each scanned itself
instead. deadname-gate exits **2** rather than **0** when
nothing is configured, and contrast-gate --require-pairs fails
rather than passing a stylesheet that declares no colours at all.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
