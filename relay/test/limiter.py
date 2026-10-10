#!/usr/bin/env python3
"""Does the limiter cap a flood, and does it leave a real sender alone.

The first version of this test checked STATUS CODES and was wrong twice.

It looked for 429 on a throttled rejection, but a throttled rejection
deliberately answers 401 - telling a stranger "you are being rate
limited" tells them the endpoint is real and that they found the edge of
it. The observable claim is not the code. It is how many rows the flood
managed to write.

And it originally accepted a good sender being throttled, with the excuse
"the bucket is shared, which is expected" written into it. It is not
expected. A stranger silencing a real sender by shouting is the bug the
two-bucket design exists to prevent, and this now FAILS on it.

Pass the slug as argv[1] to run against a fresh endpoint; a bucket that
is already half empty from an earlier run proves nothing.
"""
import hashlib
import hmac
import io
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The address is relay.f-keys.com since 2026-10-10. workers.dev still
# serves the same Worker, so the old host is a fallback, not a second
# service. Every request here sets an explicit user-agent on purpose:
# Cloudflare answers 403 to the Python-urllib default on every zone, so
# a script that does not set one tests the bot rule instead of the relay.
BASE = "https://relay.f-keys.com"
SECRET = io.open(r"C:\Users\Admin\Desktop\f-keys-docs\RELAY-DEMO-SECRET.txt",
                 encoding="utf-8").read().strip().split("\n")[-1]
SLUG = sys.argv[1] if len(sys.argv) > 1 else "ratetest"
FLOOD = 40
BAD_CAPACITY = 20          # must match src/limiter.js


def post(body, sig):
    req = urllib.request.Request(
        f"{BASE}/in/{SLUG}", data=body.encode(), method="POST",
        headers={"content-type": "application/json",
                 "user-agent": "relay-selftest/0.1",
                 **({"x-relay-signature": sig} if sig else {})})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def good(body):
    ts = int(time.time())
    mac = hmac.new(SECRET.encode(), f"{ts}.{body}".encode(),
                   hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


def rows_written():
    out = subprocess.run(
        ["npx", "wrangler", "d1", "execute", "f-keys-relay", "--remote", "-y",
         "--command",
         f"SELECT signature_ok, COUNT(*) AS n FROM events "
         f"WHERE source='{SLUG}' GROUP BY signature_ok"],
        capture_output=True, text=True, shell=True,
        # wrangler writes ANSI colour; cp1252 cannot decode it and the
        # whole subprocess read dies on a byte that is not the point.
        encoding="utf-8", errors="replace").stdout
    import re
    m = re.search(r"\[\s*\{.*\}\s*\]", out, re.S)
    if not m:
        return None, None
    rows = json.loads(m.group(0))[0]["results"]
    t = {r["signature_ok"]: r["n"] for r in rows}
    return t.get(0, 0), t.get(1, 0)


stamp = int(time.time())
print("  endpoint: %s" % SLUG)

# THE ENDPOINT HAS TO EXIST OR NOTHING BELOW MEANS ANYTHING.
# This check is here because the run that prompted it reported
# "** THROTTLED BY THE FLOOD, which is the bug **" and "capped - the
# flood could not grow the table" when the real answer was that every
# request 404'd: the endpoint row had never been inserted, because it
# omitted created_at (NOT NULL, no default) and INSERT OR IGNORE
# swallowed the violation. Two false statements from one missing row,
# one of them accusing the service of the exact bug it was built to
# prevent. A rate-limit test that cannot tell "throttled" from "no such
# endpoint" is not measuring the limiter.
probe = json.dumps({"id": "exists_%d" % stamp})
probe_code = post(probe, good(probe))
if probe_code == 404:
    print()
    print("  ABORT: /in/%s does not exist, so no result here is about" % SLUG)
    print("  the limiter. Create the endpoint row - all seven columns,")
    print("  created_at included - and run again.")
    sys.exit(2)
if probe_code not in (200, 202):
    print()
    print("  ABORT: a good request got %s before the flood even started."
          % probe_code)
    sys.exit(2)
print("  endpoint reachable, a good request is accepted")
print()
print("  1. %d requests with BAD signatures, fired together" % FLOOD)
with ThreadPoolExecutor(max_workers=8) as pool:
    codes = list(pool.map(
        lambda i: post(json.dumps({"id": f"flood_{stamp}_{i}"}),
                       "t=1,v1=deadbeef"),
        range(FLOOD)))
print("     status codes seen: %s" % dict(
    (c, codes.count(c)) for c in sorted(set(codes))))

print()
print("  2. a GOOD sender, immediately after")
body = json.dumps({"id": f"survivor_{stamp}", "kind": "rate-test"})
code = post(body, good(body))
survived = code in (200, 202)
print("     status %s - %s" % (code, "gets through" if survived
      else "** THROTTLED BY THE FLOOD, which is the bug **"))

print()
print("  3. what the flood actually wrote")
bad_rows, ok_rows = rows_written()
if bad_rows is None:
    print("     could not read D1")
    sys.exit(1)
# "0 rows written" is only a cap if the requests actually arrived. If
# nothing reached the service, zero rows proves nothing and must not be
# dressed up as a pass.
arrived = any(c in (401, 429) for c in codes)
capped = arrived and bad_rows <= BAD_CAPACITY + 4   # some refill mid-run
if not arrived:
    print("     ** no request reached the limiter - codes were %s **"
          % sorted(set(codes)))
print("     rejected rows : %d   (from %d attempts, bucket holds %d)"
      % (bad_rows, FLOOD, BAD_CAPACITY))
print("     verified rows : %d" % ok_rows)
print("     %s" % ("capped - the flood could not grow the table" if capped
                   else "** the flood wrote freely **"))

print()
ok = survived and capped
print("  " + ("the limiter holds and a real sender is unaffected" if ok
              else "FAILED"))
sys.exit(0 if ok else 1)
