# axsent

> What a formal library assumes, measured from source.

Canonical: https://f-keys.com/axsent/

What a formal library assumes, measured from source.

| Field | Value |
| --- | --- |
| Install | pip install axsent |
| Reads | Rocq, Agda, Isabelle |
| Builds | Nothing |
| Source | vince-gonzalez/axsent |

## What it does

Measures what a formal library actually assumes — its axioms, and the
interface assumptions that get counted alongside them — across Rocq,
Agda and Isabelle, read from source with nothing compiled.

**pip install axsent**
axsent <path-to-library>
Why nothing is built
A census that requires building the library can only measure libraries that
still build. That silently excludes the old, the abandoned and the ones
pinned to a compiler nobody has — which is a biased sample of exactly the
wrong kind, because those are the ones whose assumptions nobody has looked at
lately.

## The finding behind it

Every census of this kind conflates two different things: assumptions that
are *mathematical*, and assumptions that are about the
*interface* to the outside world. They are counted together and
reported as one number. Separating them is most of what this tool is for, and
the measurements are written up in the papers.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
