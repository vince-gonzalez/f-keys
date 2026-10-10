# d1bench

How fast can you write N rows to Cloudflare D1, which strategy wins, and which
of the documented limits stops you first.

Results: [`results/FINDINGS.md`](results/FINDINGS.md). Raw data:
[`results/sweep.json`](results/sweep.json),
[`results/rowsize.json`](results/rowsize.json).

## Why it runs inside a Worker

Two of the limits under test only exist inside a Worker invocation - queries
per invocation, and the 30-second cap on one `batch()` call. Measured from a
laptop those limits do not exist, and the number you get is mostly your own
internet connection.

## Why it has its own database

It creates, drops and truncates tables and writes rows in bulk. Pointed at a
database that mattered, a benchmark's `DROP TABLE` would be one typo away from
live data.

## Why every writing route is gated

A public endpoint that inserts D1 rows as fast as it can is a billing hole
with a documented API. `BENCH_TOKEN` gates everything except `/limits`, and
there is no custom domain.

## Run it

```
npx wrangler d1 create f-keys-d1bench     # put the id in wrangler.toml
npx wrangler secret put BENCH_TOKEN
npm run deploy

python -I drive.py            # column-count sweep
python -I drive_rowsize.py    # row-size sweep
```

## The one thing to know before trusting any of it

In Workers, `Date.now()` advances only on I/O. It is frozen across pure
computation. So an inside-the-Worker clock cannot see the CPU spent building a
statement - and the literal-SQL strategy is precisely the one doing that work.
Timed only from inside, literal SQL looks better than it is.

Every run is therefore timed twice: `d1_ms` from inside, around the awaited
`batch()` call, and `total_ms` from the driver, which includes CPU and
network. Reporting one without the other is how this gets the answer wrong.
