# Finding 1 — `db.batch()` is not bound by "queries per Worker invocation"

Measured 2026-10-10 against a live D1 instance (`f-keys-d1bench`, region ENAM)
from inside a deployed Worker. Harness: `f-keys/d1bench`, version `d5bb2ca7`.

## The claim everyone repeats

Cloudflare's D1 limits page lists **queries per Worker invocation: 1000**
(paid) / 50 (free). The advice that follows it, in blog posts and in bug
reports, is that a bulk insert must be chunked so the number of statements
stays under that cap.

## What a single `batch()` call actually accepted

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

No refusal at any rung. **128,000 statements is 128x the documented
per-invocation cap.** Per-statement cost is flat at 0.205–0.280 ms across a
128-fold range, so nothing degrades as the call grows — it is linear, and the
intercept is small.

## The check that makes it a finding rather than a fast no-op

A benchmark that reports a time for writes which never happened is worthless,
so the row count was reconciled against every statement sent:

```
run 1 (default ladder)     5,487
run 2                     31,000
run 3                    224,000
                        --------
expected                 260,487
actually in bench_c4     260,487      exact
```

Every statement in every batch executed. The times above are real work.

## What it means

The 1000-query cap is **not charged per statement inside `batch()`**. One
`batch()` call behaves as one query against that limit. So the usual
reasoning — "chunk the statements to stay under 1000" — is solving a problem
that is not there, and the real ceiling for one-statement-per-row bulk
insertion is somewhere else entirely.

Where? At 0.236 ms per statement, the **30-second query-duration cap** is the
first wall: 128,000 statements took 30,208 ms, which has already passed it and
still returned successfully. So the duration cap is not strictly enforced at
that boundary either. The next rung up is the measurement that would locate
it, and it has not been run yet — **stated as unmeasured rather than
extrapolated into a number.**

## Limitations, stated

- One region (ENAM), one database, one account, one day. Region and
  neighbour effects are not characterised.
- 4 columns per row, ~16-byte payload. Per-statement cost may depend on row
  width; that is the main sweep, not this probe.
- `Date.now()` in Workers advances only on I/O, so these numbers are D1 time
  and exclude the CPU spent building statements. For `onebyone` that build
  cost is small and uniform; it matters for the literal-SQL strategy and is
  handled in the main sweep by also timing from outside.
- The table carried no indexes. Index maintenance is real write cost and is
  excluded here deliberately, to isolate the variable.
