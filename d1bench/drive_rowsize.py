#!/usr/bin/env python3
"""The other axis: sweep ROW SIZE at fixed column count.

The column sweep showed literal SQL pulling away as C rises, because
the 100-parameter ceiling drives bound-parameter chunking down to
floor(100/C) rows a statement and reaches 1 at C=51.

That cannot be the whole picture, because the two strategies are capped
by different limits. Bound parameters are capped by COLUMN COUNT and do
not care how big a value is - the values travel beside the SQL, not
inside it. Literal SQL is capped by the 100,000-byte STATEMENT LENGTH,
so its chunk shrinks as rows get fatter, and at some row size a single
row's literal tuple will not fit in one statement at all. At that point
literal SQL is not slower, it is unavailable.

So there should be a crossover on this axis running the other way, and
a region beyond it where only bound parameters work. This measures it.

N IS SCALED DOWN AS ROWS GET FATTER, to hold bytes-written per run near
a few megabytes. That means times are NOT comparable across row sizes -
only params against literal WITHIN one row size, which is the
comparison the crossover needs. Stated here so nobody reads the columns
sideways.
"""
import io
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------
# CONFIGURED FROM THE ENVIRONMENT, not baked in. Two reasons, and
# neither is tidiness: the hardcoded value was an account's own
# workers.dev subdomain and a local home directory, and this file is
# published. Anyone reproducing this points it at their own deployment.
#
#   set D1BENCH_BASE=https://<your-worker>.workers.dev
#   set D1BENCH_TOKEN=<the value of BENCH_TOKEN>
#
# or put the token in a file and give its path as D1BENCH_TOKEN_FILE.
# ---------------------------------------------------------------------
BASE = os.environ.get("D1BENCH_BASE", "").rstrip("/")
if not BASE:
    sys.exit("set D1BENCH_BASE to the deployed Worker's origin")


def _token():
    direct = os.environ.get("D1BENCH_TOKEN")
    if direct:
        return direct.strip()
    path = os.environ.get("D1BENCH_TOKEN_FILE")
    if path and os.path.exists(path):
        # Last non-empty line, so the file may carry a header describing
        # what the value is for.
        lines = [l for l in io.open(path, encoding="utf-8").read().splitlines()
                 if l.strip()]
        if lines:
            return lines[-1].strip()
    sys.exit("set D1BENCH_TOKEN, or D1BENCH_TOKEN_FILE to a file holding it")


TOKEN = _token()

COLUMNS = 8
REPEATS = 3
# (bytes per column value, rows) - rows chosen to keep each run near 4 MB
CASES = [
    (16, 1000),
    (64, 1000),
    (256, 1000),
    (1024, 500),
    (4096, 125),
    (16384, 32),
    (65536, 8),
]
STRATEGIES = ["params", "literal"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "results", "rowsize.json")


def call(path, body, timeout=240):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(), method="POST",
        headers={"content-type": "application/json",
                 "x-bench-token": TOKEN,
                 "user-agent": "d1bench-driver/0.1"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode()), \
                (time.perf_counter() - t0) * 1000.0
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {"error": "http", "status": e.code}
        return e.code, body, (time.perf_counter() - t0) * 1000.0
    except Exception as e:
        return 0, {"error": "transport", "message": str(e)[:300]}, \
            (time.perf_counter() - t0) * 1000.0


print("  d1bench - row size sweep at C=%d, %d passes" % (COLUMNS, REPEATS))
print("  N scaled per row size to hold each run near 4 MB")
print()

samples = {}
shape = {}
errors = {}

for rep in range(1, REPEATS + 1):
    print("  pass %d of %d" % (rep, REPEATS))
    for payload, n in CASES:
        line = "    %6dB x %d cols, n=%-5d" % (payload, COLUMNS, n)
        for s in STRATEGIES:
            call("/truncate", {"columns": [COLUMNS]}, timeout=180)
            status, body, total_ms = call(
                "/run", {"strategy": s, "columns": COLUMNS, "rows": n,
                         "row_bytes": payload})
            key = (s, payload)
            if status != 200 or "d1_ms" not in body:
                msg = body.get("message") or body.get("error") or "?"
                errors[key] = msg
                line += "  %-8s REFUSED" % s
                continue
            samples.setdefault(key, []).append(
                {"d1_ms": body["d1_ms"], "total_ms": total_ms})
            shape[key] = {
                "statements": body["statements"],
                "rows_per_stmt": body["rows_per_stmt_max"],
                "max_bound_params": body["max_bound_params"],
                "max_stmt_bytes": body["max_stmt_bytes"],
            }
            line += "  %-8s %5dms" % (s, body["d1_ms"])
        print(line)
print()

print("  RESULTS - median of %d passes, C=%d" % (REPEATS, COLUMNS))
print()
print("  %8s %6s %-9s %8s %8s %9s %11s  %s"
      % ("bytes/col", "n", "strategy", "d1_med", "stmts", "rows/stmt",
         "max_stmt_B", "status"))
print("  " + "-" * 88)

out = []
for payload, n in CASES:
    for s in STRATEGIES:
        key = (s, payload)
        got = [g["d1_ms"] for g in samples.get(key, [])]
        if not got:
            print("  %8d %6d %-9s %8s %8s %9s %11s  %s"
                  % (payload, n, s, "-", "-", "-", "-",
                     ("REFUSED: " + str(errors.get(key, "?")))[:40]))
            out.append({"bytes_per_col": payload, "rows": n, "strategy": s,
                        "refused": True,
                        "error": str(errors.get(key, ""))[:300]})
            continue
        sh = shape.get(key, {})
        print("  %8d %6d %-9s %8.0f %8d %9d %11d  ok"
              % (payload, n, s, statistics.median(got),
                 sh.get("statements", 0), sh.get("rows_per_stmt", 0),
                 sh.get("max_stmt_bytes", 0)))
        out.append({
            "bytes_per_col": payload, "rows": n, "strategy": s,
            "refused": False, "passes": len(got),
            "d1_ms_median": statistics.median(got),
            "d1_ms_min": min(got), "d1_ms_max": max(got),
            "d1_ms_stdev": round(statistics.stdev(got), 2) if len(got) > 1 else 0,
            **sh,
        })
    print()

print("  CROSSOVER on row size - params vs literal at C=%d" % COLUMNS)
print()
for payload, n in CASES:
    p = [g["d1_ms"] for g in samples.get(("params", payload), [])]
    l = [g["d1_ms"] for g in samples.get(("literal", payload), [])]
    row_bytes = payload * COLUMNS
    if not l and p:
        print("  %7dB/col (row ~%7d B): literal UNAVAILABLE, params works"
              % (payload, row_bytes))
        continue
    if not p or not l:
        continue
    pm, lm = statistics.median(p), statistics.median(l)
    noise = max(statistics.stdev(p) if len(p) > 1 else 0,
                statistics.stdev(l) if len(l) > 1 else 0)
    d = lm - pm
    if abs(d) <= noise:
        v = "within noise (sd %.0f)" % noise
    elif d < 0:
        v = "literal faster by %.0fms (%.0f%%)" % (-d, 100.0 * -d / pm)
    else:
        v = "PARAMS faster by %.0fms (%.0f%%)" % (d, 100.0 * d / lm)
    print("  %7dB/col (row ~%7d B): %s" % (payload, row_bytes, v))

io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps({
    "meta": {
        "columns": COLUMNS, "repeats": REPEATS, "cases": CASES,
        "note": ("N is scaled down as row size rises to hold bytes written "
                 "per run near 4 MB, so times are comparable only between "
                 "strategies WITHIN one row size, never across row sizes. "
                 "A refused literal run is the finding, not a failure: it "
                 "marks the region where one row's literal tuple exceeds "
                 "the 100,000-byte statement limit and only bound "
                 "parameters remain available."),
    },
    "results": out,
}, indent=2) + "\n")
print()
print("  wrote %s" % OUT)
