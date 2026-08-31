# certivl

> An enclosure that turns a computed inequality into a proof.

Canonical: https://f-keys.com/certivl/

Exact rational and certified interval arithmetic. A float comparison tells you what the hardware thought; an enclosure tells you what is true, because the answer is bracketed and the bracket is carried through every operation.

**0.2.0** · pip install certivl · MIT · exact rational and interval

## What it does

Exact rational and certified interval arithmetic. A float comparison tells
you what the hardware thought; an enclosure tells you what is true, because the
answer is bracketed and the bracket is carried through every operation.

**pip install certivl**
Why an interval rather than a number
A computed inequality is only evidence until the rounding is accounted for.
An enclosure that stays strictly on one side of zero settles the question; one
that straddles zero says the computation did not decide it. The second answer
is the useful one, and floating point never gives it to you — it gives
you a number and no idea how much of it is real.

## Where it is used

Behind the certified bounds in the discrete-geometry papers: covering,
packing and opacity results where a machine-checked upper bound has to survive
someone re-running it on different hardware.

## How it works

## What it gives you

## Specifications

| Field | Value |
| --- | --- |
| Install | pip install certivl |
| Version | 0.2.0 |
| Licence | MIT |
| Arithmetic | Exact rational, certified interval |
| Source | vince-gonzalez/certivl |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
