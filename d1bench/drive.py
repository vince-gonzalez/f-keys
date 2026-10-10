#!/usr/bin/env python3
"""Sweep the three write strategies across column count, with repeats.

WHY REPEATS ARE OUTER AND NOT INNER. The naive loop runs strategy A
five times, then B five times, then C five times. If the service gets
slower over the ten minutes the sweep takes - a neighbour warms up, a
region gets busy - that drift lands entirely on whichever strategy ran
last, and the drift gets reported as a difference between strategies.

So the repeat loop is the OUTER one: every pass covers all (columns,
strategy) pairs before the next pass starts. Drift then spreads across
all conditions instead of pooling in one, and the spread is visible in
the variance column rather than hiding in the median.

WHY TWO CLOCKS. The Worker reports d1_ms, measured around the awaited
batch() call. In Workers, Date.now() advances only on I/O, so that
clock cannot see CPU - and the literal strategy is the one doing extra
CPU, building and escaping SQL strings. Timed only from inside, literal
SQL would look better than it is and the headline would be an artifact
of the instrument.

This script therefore also records total_ms, the wall clock of the
whole HTTP request from here. total_ms includes network and the CPU the
inside clock is blind to. Neither number is the answer on its own:
d1_ms isolates the database, total_ms catches what d1_ms structurally
cannot, and the gap between them is itself reportable.

TRUNCATE BEFORE EVERY MEASURED RUN. Otherwise the first condition
writes into an empty table and the last writes into one holding tens of
thousands of rows, and table size becomes a hidden variable.
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

COLUMNS = [2, 4, 8, 16, 32, 64]
STRATEGIES = ["params", "literal", "onebyone"]
ROWS = 1000
ROW_BYTES = 16
REPEATS = 5

OUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "results", "sweep.json")


def call(path, body, timeout=180):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data, method="POST",
        headers={"content-type": "application/json",
                 "x-bench-token": TOKEN,
                 # Cloudflare answers 403 to the Python-urllib default
                 # user agent on every zone. Without this the script
                 # measures a bot rule.
                 "user-agent": "d1bench-driver/0.1"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read().decode())
            status = r.status
    except urllib.error.HTTPError as e:
        payload = {"error": "http", "status": e.code,
                   "body": e.read().decode()[:300]}
        status = e.code
    except Exception as e:
        payload = {"error": "transport", "message": str(e)[:300]}
        status = 0
    total_ms = (time.perf_counter() - t0) * 1000.0
    return status, payload, total_ms


def truncate():
    call("/truncate", {"columns": COLUMNS}, timeout=120)


print("  d1bench sweep")
print("  rows=%d  row_bytes=%d  repeats=%d  columns=%s"
      % (ROWS, ROW_BYTES, REPEATS, COLUMNS))
print("  two clocks: d1_ms from inside the Worker, total_ms from here")
print()

samples = {}        # (strategy, columns) -> list of dicts
shape = {}          # (strategy, columns) -> statements / params / bytes

for rep in range(1, REPEATS + 1):
    print("  pass %d of %d" % (rep, REPEATS))
    for c in COLUMNS:
        line = "    c=%-3d" % c
        for s in STRATEGIES:
            truncate()
            status, body, total_ms = call(
                "/run", {"strategy": s, "columns": c, "rows": ROWS,
                         "row_bytes": ROW_BYTES})
            if status != 200 or "d1_ms" not in body:
                line += "  %-9s ERR" % s
                samples.setdefault((s, c), []).append(
                    {"error": body.get("message") or body.get("error")})
                continue
            samples.setdefault((s, c), []).append(
                {"d1_ms": body["d1_ms"], "total_ms": total_ms})
            shape[(s, c)] = {
                "statements": body["statements"],
                "rows_per_stmt": body["rows_per_stmt_max"],
                "max_bound_params": body["max_bound_params"],
                "max_stmt_bytes": body["max_stmt_bytes"],
            }
            line += "  %s=%dms" % (s[:4], body["d1_ms"])
        print(line)
print()

# ---- report ----------------------------------------------------------
def med(vals):
    return statistics.median(vals) if vals else None


print("  RESULTS - median of %d passes, %d rows each" % (REPEATS, ROWS))
print()
print("  %-4s %-9s %7s %7s %7s %6s %7s %6s %9s"
      % ("C", "strategy", "d1_med", "d1_min", "d1_max", "sd",
         "tot_med", "stmts", "rows/stmt"))
print("  " + "-" * 82)

rows_out = []
for c in COLUMNS:
    for s in STRATEGIES:
        got = samples.get((s, c), [])
        d1 = [g["d1_ms"] for g in got if "d1_ms" in g]
        tot = [g["total_ms"] for g in got if "total_ms" in g]
        if not d1:
            print("  %-4d %-9s  all runs failed: %s"
                  % (c, s, got[0].get("error") if got else "?"))
            continue
        sh = shape.get((s, c), {})
        sd = statistics.stdev(d1) if len(d1) > 1 else 0.0
        print("  %-4d %-9s %7.0f %7.0f %7.0f %6.1f %7.0f %6d %9d"
              % (c, s, med(d1), min(d1), max(d1), sd, med(tot),
                 sh.get("statements", 0), sh.get("rows_per_stmt", 0)))
        rows_out.append({
            "columns": c, "strategy": s, "rows": ROWS,
            "row_bytes": ROW_BYTES, "passes": len(d1),
            "d1_ms_median": med(d1), "d1_ms_min": min(d1),
            "d1_ms_max": max(d1), "d1_ms_stdev": round(sd, 2),
            "total_ms_median": round(med(tot), 1) if tot else None,
            **sh,
        })
    print()

# ---- the crossover, stated only where the spread allows it ----------
print("  CROSSOVER - params vs literal, per column count")
print()
print("  %-4s %9s %9s %9s  %s" % ("C", "params", "literal", "diff", "verdict"))
print("  " + "-" * 62)
for c in COLUMNS:
    p = [g["d1_ms"] for g in samples.get(("params", c), []) if "d1_ms" in g]
    l = [g["d1_ms"] for g in samples.get(("literal", c), []) if "d1_ms" in g]
    if not p or not l:
        continue
    pm, lm = med(p), med(l)
    # A difference smaller than the noise is not a result. The spread of
    # both conditions has to be cleared before either is called faster.
    noise = max(statistics.stdev(p) if len(p) > 1 else 0,
                statistics.stdev(l) if len(l) > 1 else 0)
    diff = lm - pm
    if abs(diff) <= noise:
        verdict = "within noise (sd %.0f) - no call" % noise
    elif diff < 0:
        verdict = "LITERAL faster by %.0fms" % -diff
    else:
        verdict = "params faster by %.0fms" % diff
    print("  %-4d %9.0f %9.0f %+9.0f  %s" % (c, pm, lm, diff, verdict))

io.open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(
    json.dumps({
        "meta": {
            "base": BASE, "rows": ROWS, "row_bytes": ROW_BYTES,
            "repeats": REPEATS, "columns": COLUMNS,
            "strategies": STRATEGIES,
            "note": ("d1_ms is measured inside the Worker around the awaited "
                     "batch() call and excludes CPU, because Date.now() in "
                     "Workers advances only on I/O. total_ms is the whole "
                     "request measured by the driver and includes CPU and "
                     "network. Tables are truncated before every measured "
                     "run. Repeats are the outer loop so drift spreads "
                     "across conditions instead of pooling in one."),
        },
        "results": rows_out,
    }, indent=2) + "\n")
print()
print("  wrote %s" % OUT_JSON)
