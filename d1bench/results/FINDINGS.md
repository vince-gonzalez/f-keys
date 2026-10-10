# Writing rows to Cloudflare D1: which strategy wins, and which limit stops you first

Measured 2026-10-10 against a live D1 database (`f-keys-d1bench`, region
ENAM) from inside a deployed Worker. Harness `f-keys/d1bench`, Worker version
`d5bb2ca7`. Every number below is the median of repeated passes against the
live service; nothing here is computed from the documentation.

---

## The question

Cloudflare documents its D1 limits individually. It does not document how they
interact, and they interact in a way that changes which strategy is correct.
Three ways to write N rows, each stopped by a different limit:

| strategy | one statement holds | capped by |
|---|---|---|
| `params` | many rows, values **bound** | 100 bound parameters per query |
| `literal` | many rows, values **inlined** | 100,000-byte statement length |
| `onebyone` | one row | queries per invocation, 30 s per call |

The limits are published. Which one binds first, for a given shape of data,
is not — and that is the only part a developer actually has to decide.

---

## Finding 1 — `batch()` is not bound by "queries per Worker invocation"

The documented cap is **1000 queries per Worker invocation** (50 on free), and
the advice that follows it is to chunk a bulk insert so the statement count
stays under it. Whether that cap is charged per statement inside a `batch()`
is left open by the documentation — see the quotations below — and the open
question is why the cautious reading spread.

A single `batch()` call accepted far more:

| statements in one `batch()` | D1 time | per statement |
|---|---|---|
| 1,000 | 280 ms | 0.280 ms |
| 2,000 | 439 ms | 0.220 ms |
| 4,000 | 844 ms | 0.211 ms |
| 8,000 | 1,701 ms | 0.213 ms |
| 16,000 | 3,831 ms | 0.239 ms |
| 32,000 | 6,563 ms | 0.205 ms |
| 64,000 | 14,893 ms | 0.233 ms |
| 128,000 | 30,208 ms | 0.236 ms |

No refusal at any rung. **128,000 statements is 128x the documented cap**, and
per-statement cost is flat from 0.205 to 0.280 ms across that entire 128-fold
range — the relationship is linear with a small intercept.

**The check that makes this a finding and not a fast no-op.** Row counts were
reconciled against every statement sent: 260,487 expected across three probe
runs, 260,487 present in the table. Exact. Every statement executed.

So one `batch()` call behaves as **one query** against the per-invocation cap.
Chunking statements to stay under 1000 is solving a problem that is not there.

### What the documentation actually says, quoted

The relevant row is not phrased the way it is usually quoted. Verbatim:

> **Queries per Worker invocation (read subrequest limits)**: 1000 (Workers
> Paid) / 50 (Free)

The parenthetical is the hint, and it is routinely dropped when the number is
repeated. The page then says:

> Limits for individual queries (listed above) apply to each individual
> statement contained within a batch statement.

with statement length given as the example. **What the page does not say is
how a `batch()` counts against the query-count row** — one query, or one per
statement. That is the ambiguity, and the sentence above invites the stricter
reading. The measurement resolves it: a batch is one.

### A correction to an earlier draft of this document

An earlier draft noted that the 128,000-statement call ran 30,208 ms, past
the documented 30-second **Maximum SQL query duration**, and treated that as
a second unenforced limit. That was wrong, and wrong by the same misreading
this finding is about.

The duration limit applies **per statement**, exactly as the quoted sentence
says. Each statement here took about 0.236 ms, so no statement came close to
30 seconds and nothing was violated. A batch whose *total* wall time exceeds
30 seconds does not breach a per-statement cap.

So there is **no finding about the 30-second limit**, in either direction. It
was never approached. Where a genuinely long single statement gets refused is
a different experiment and was not run.

---

## Finding 2 — the parameter ceiling is exactly `floor(100 / C)`, and it reaches 1

Climbed until D1 refused, at each column count:

| columns bound (C) | max rows per statement | parameters used | `floor(100/C)` | error at failure |
|---|---|---|---|---|
| 2 | 50 | 100 | 50 | `too many SQL variables` |
| 4 | 25 | 100 | 25 | `too many SQL variables` |
| 8 | 12 | 96 | 12 | `too many SQL variables` |
| 16 | 6 | 96 | 6 | `too many SQL variables` |
| 32 | 3 | 96 | 3 | `too many SQL variables` |
| 64 | **1** | 64 | 1 | `too many SQL variables` |

The arithmetic is exact at every point. The consequence is the part worth
saying out loud: **at C >= 51, `floor(100/C)` is 1**, so "chunked bound
parameters" has silently become one-statement-per-row. It is no longer a
batching strategy at all, while still being described as one in the code that
uses it.

---

## Finding 3 — literal SQL pulls away as columns rise

1,000 rows, 16-byte values, median of 5 passes, tables truncated before every
measured run.

| C | `params` | `literal` | `onebyone` | params rows/stmt | literal rows/stmt | verdict |
|---|---|---|---|---|---|---|
| 2 | 51 ms | 44 ms | 281 ms | 50 | 1000 | literal by 7 ms |
| 4 | 54 ms | 49 ms | 253 ms | 25 | 1000 | within noise (sd 20) |
| 8 | 88 ms | 59 ms | 284 ms | 12 | 500 | literal by 29 ms (33%) |
| 16 | 132 ms | 93 ms | 302 ms | 6 | 250 | literal by 39 ms (30%) |
| 32 | 195 ms | 123 ms | 309 ms | 3 | 143 | literal by 72 ms (37%) |
| 64 | 503 ms | 187 ms | 388 ms | 1 | 77 | **literal by 316 ms (63%)** |

At C=64 literal SQL is **2.7x faster**, and the mechanism is in the two
rows/stmt columns rather than in anything subtle: the parameter ceiling has
driven `params` to 1 row per statement while `literal` still carries 77.

**`params` at C=64 and `onebyone` are the same thing** — 1,000 single-row
statements — and their medians (503 ms and 388 ms) differ by less than the
spread of `params` (sd 93, min 327). No claim is made that one beats the
other; they converge, which is the point.

**The bias this had to survive.** In Workers, `Date.now()` advances only on
I/O, so it cannot see CPU — and `literal` is the strategy doing extra CPU,
building and escaping SQL strings. Timed only from inside the Worker, literal
SQL would look better than it is. So every run was also timed from outside, as
whole-request wall clock:

| C | params d1 / total | literal d1 / total | outside overhead |
|---|---|---|---|
| 2 | 51 / 135 ms | 44 / 129 ms | 84 vs 85 ms |
| 8 | 88 / 181 ms | 59 / 151 ms | 93 vs 92 ms |
| 64 | 503 / 599 ms | 187 / 285 ms | 96 vs 98 ms |

The outside overhead is 84–98 ms and **essentially identical between
strategies at every column count**, so the CPU that the inner clock cannot see
is not what produced the gap. The finding holds in both clocks. This was the
measurement most likely to overturn the result, which is why it was run.

---

## Finding 4 — on the row-size axis it runs the other way, and ends in a wall

C=8, median of 3 passes. N is scaled down as rows get fatter to hold each run
near 4 MB, so times compare **between strategies within a row size**, never
across row sizes.

| bytes/value | row ~ | params | literal | literal rows/stmt | verdict |
|---|---|---|---|---|---|
| 16 | 128 B | 96 ms | 69 ms | 500 | literal by 28% |
| 64 | 512 B | 90 ms | 99 ms | 200 | within noise |
| 256 | 2 KB | 254 ms | 182 ms | 53 | literal by 28% |
| 1,024 | 8 KB | 231 ms | 289 ms | 13 | within noise |
| 4,096 | 32 KB | 203 ms | 217 ms | 3 | within noise |
| 16,384 | 131 KB | 150 ms | **refused** | — | `statement too long` |
| 65,536 | 524 KB | 202 ms | **refused** | — | `statement too long` |

Literal SQL's chunk collapses as rows grow — 500, 200, 53, 13, 3 — and then
stops being an option at all: once a single row's literal tuple exceeds the
100,000-byte statement limit, there is no chunk size that works. It is not
slower there. It is **unavailable**.

`params` rows-per-statement stays pinned at 12 across every row size, because
bound values travel beside the SQL rather than inside it.

---

## Finding 5 — the two strategies are capped by orthogonal limits

That is the whole result in one line, and everything above is a consequence:

|  | bound by column count | bound by row size |
|---|---|---|
| `params` | **yes** — `floor(100/C)`, reaches 1 at C=51 | no — invariant |
| `literal` | no — invariant | **yes** — collapses, then unavailable |

### The decision rule this supports

- **Wide rows, small values** (high C, short strings): literal SQL, by a
  margin that grows to 2.7x at C=64.
- **Fat values** (any value pushing a row past ~100 KB of literal text):
  bound parameters, because literal SQL cannot express the statement.
- **The broad middle** (C <= 8, rows 512 B to 32 KB): the difference sits
  inside run-to-run spread. Use bound parameters — same speed, and no
  escaping to get wrong.
- **Never chunk to stay under 1000 statements.** That cap is not charged per
  statement inside `batch()`.

---

## Method, so it can be checked

- Harness: `f-keys/d1bench`, Worker version `d5bb2ca7`, one D1 database
  created for this and nothing else.
- Timing: `d1_ms` wraps only the awaited `batch()` call, inside the Worker.
  `total_ms` is whole-request wall clock from the driver. Both reported.
- Repeats are the **outer** loop, so every pass covers all (columns,
  strategy) pairs before the next begins. Run serially by strategy, any
  drift over the sweep would land entirely on whichever ran last and be
  reported as a difference between strategies.
- Tables truncated before every measured run, so table size is not a hidden
  variable.
- A difference smaller than the larger of the two conditions' standard
  deviations is reported as "within noise" and no winner is named.
- Probes climb until D1 refuses and record the refusal text. A documented
  limit that has never been hit on purpose is a number someone typed.

## What these numbers do not support

- **One region, one database, one account, one day.** ENAM only. Region
  placement and neighbor load are not characterized, and D1 is a hosted
  service whose absolute timings are not a property of the strategy.
- **No indexes on any table.** Index maintenance is real write cost,
  excluded deliberately to isolate the variable. A table with three indexes
  will not match these absolute numbers.
- **Nothing here tests the 30-second duration cap.** It applies per
  statement, and every statement measured took well under a millisecond, so
  the cap was never approached. An earlier draft of this document claimed the
  cap went unenforced because a whole batch ran 30,208 ms; that conflated a
  per-statement limit with a per-call total and has been removed.
- **Values contained no characters needing escaping.** Escaping cost scales
  with quote density, which is a separate sweep and was not run. This matters
  only for `literal`, and it is the one axis where the untested direction
  could narrow literal SQL's advantage.
- **`rows_per_stmt` for `params` is set from the documented ceiling**
  (`floor(100/C)`), which Finding 2 confirms is exact. It is not tuned below
  the ceiling, so these are best-case `params` numbers.
- Absolute milliseconds are of this account on this day. The **ratios and
  the orthogonality** are the claims; the raw timings are evidence for them,
  not the result.
