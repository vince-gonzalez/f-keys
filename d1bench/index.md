# d1bench

> Which D1 write strategy wins, and which limit stops you first.

Canonical: https://f-keys.com/d1bench/

Cloudflare documents D1's limits one at a time. It does not document how they interact, and they interact in a way that changes which bulk-insert strategy is correct. This harness deploys inside a Worker, because two of the limits under test only exist inside a Worker invocation, and sweeps three strategies against a live database.

**Measured 2026-10-10** · live D1, region ENAM · five findings · v0.1.0 · raw data published · MIT

## The question

Three ways to write N rows to D1, and each one is stopped by a different
documented limit. Which limit binds first, for a given shape of data, is the
only part a developer actually has to decide — and it is the part that is
not written down.

| strategy | one statement holds | capped by |
| --- | --- | --- |
| params | many rows, values **bound** | 100 bound parameters per query |
| literal | many rows, values **inlined** | 100,000-byte statement length |
| onebyone | one row | queries per invocation |

## A single batch() call took 150,000 statements

The documented cap is 1000 queries per Worker invocation, and the advice
that follows it is to chunk a bulk insert so the statement count stays under
it. No rung refused:

| statements in one batch() | D1 time | per statement |
| --- | --- | --- |
| 1,000 | 280 ms | 0.280 ms |
| 8,000 | 1,701 ms | 0.213 ms |
| 32,000 | 6,563 ms | 0.205 ms |
| 128,000 | 30,208 ms | 0.236 ms |
| 150,000 | 25,802 ms | 0.172 ms |
| 175,000 | **refused** |  |

One batch() behaves as one query against the count limit, so
chunking statements to stay under 1000 solves a problem that is not there. The
limit that does bind is **duration**: thirty seconds, applied to the entire
batch call, exactly as the documentation’s own footnote 4 states.

Which makes the ceiling a **time budget rather than a statement
count** — thirty seconds divided by your per-statement cost. It moves
with row width, so a number copied out of this table into code handling wider
rows will be wrong.

## The ceiling is exact, and it reaches one

Climbed until D1 refused, at every column count. The arithmetic holds
exactly: 50 rows at two columns, 12 at eight, 3 at thirty-two, and
**1 at sixty-four**. Past fifty columns, “chunked bound
parameters” is one statement per row wearing a different name.

## Which is why literal SQL pulls away

1,000 rows of 16-byte values, median of five passes, tables truncated before
every measured run:

| columns | params | literal | params rows/stmt | literal rows/stmt |
| --- | --- | --- | --- | --- |
| 4 | 54 ms | 49 ms | 25 | 1000 |
| 8 | 88 ms | 59 ms | 12 | 500 |
| 32 | 195 ms | 123 ms | 3 | 143 |
| 64 | 503 ms | **187 ms** | 1 | 77 |

At four columns the gap is inside the noise and no winner is named. At
sixty-four it is **2.7×**.

## Then the row-size axis reverses it, and ends in a wall

Literal SQL's chunk collapses as rows fatten — 500, 200, 53, 13, 3
— and once one literal tuple passes the statement limit, there is no
chunk size that works. At roughly 131 KB rows it is **refused
outright** while bound parameters carry on unaffected, because bound values
travel beside the SQL rather than inside it.

## The result

The two strategies are capped by **orthogonal** limits. Bound parameters
bind on column count and are blind to row size; literal binds on row size and
is blind to column count. Everything above follows from that.

## It reports what it did not establish

One region, one database, one account, one day, and no indexes anywhere.
Escaping cost was not swept, and that is the one untested axis that could
narrow literal SQL's advantage. The findings document also carries a
correction to an earlier draft of this work, which claimed the 30-second
duration cap went unenforced by confusing a per-statement limit with a
per-call total.

## How it works

## What it found

## Specifications

| Field | Value |
| --- | --- |
| Measured | 2026-10-10, region ENAM |
| Version | v0.1.0 |
| Strategies | bound parameters, literal SQL, one statement per row |
| Axes | columns 2 to 64, values 16 B to 64 KB |
| License | MIT |
| Source | vince-gonzalez/d1bench |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
