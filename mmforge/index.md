# mmforge

> Find the axiom a theorem did not need.

Canonical: https://f-keys.com/mmforge/

Find the axiom a theorem did not need.

| Field | Value |
| --- | --- |
| Install | pip install mmforge |
| Version | 0.2.0 |
| Licence | MIT |
| Reads | Metamath databases |
| Upstream | 6 pull requests merged into set.mm |
| Source | vince-gonzalez/mmforge |

## What it does

Two halves of one loop. The analysis finds a theorem that pays for an
axiom it does not need; the construction writes the replacement proof and
checks it.

**pip install mmforge**
mmforge reach set.mm --axiom ax-ac
mmforge impact set.mm --axiom ax-ac --top 40
mmforge domination set.mm
mmforge conformance set.mm
The finding it came from
set.mm is 47,621 theorems deep. 583 of them reach the axiom of choice and
**three** actually invoke it — everything else inherits. 418 of the 583
inherit through exactly one step, which means each has a single place where the
dependence could be removed.

The lower half of that table is measure theory, which has no business being
there. difelsiga says a sigma-algebra is closed under set
difference; below it sit 64 results including **Bayes' theorem**.

## Repairs do not add up

Fixing one statement frees a count that is not the count you get when you
fix it alongside the others. fimact alone frees one theorem; in the
stack it frees fourteen. Every per-repair figure this reports is a lower bound,
and it says so rather than adding them for you.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
