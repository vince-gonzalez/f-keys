#!/usr/bin/env python3
"""Does the live relay actually refuse a duplicate, including a racing one.

Two tests, and the second is the one that counts.

  1. Send the same event twice, one after the other. KV should answer the
     second one.
  2. Send it EIGHT TIMES AT ONCE. This is the case KV cannot win on its
     own, because eventual consistency means several of them can read
     "not seen" before any write has propagated. If exactly one row
     exists afterwards, the unique index is doing its job.

A dedupe test that only fires sequentially proves nothing about a retry
storm, which is the only situation where duplicates actually happen.
"""
import hashlib
import hmac
import io
import json
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


def post(body):
    ts = int(time.time())
    mac = hmac.new(SECRET.encode(), f"{ts}.{body}".encode(),
                   hashlib.sha256).hexdigest()
    req = urllib.request.Request(
        BASE + "/in/demo", data=body.encode(), method="POST",
        headers={"content-type": "application/json",
                 "user-agent": "relay-selftest/0.1",
                 "x-relay-signature": f"t={ts},v1={mac}"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"raw": e.read().decode()[:120]}


stamp = int(time.time())

print("  1. the same event, twice in a row")
body = json.dumps({"id": f"dup_seq_{stamp}", "kind": "demo"})
s1, b1 = post(body)
s2, b2 = post(body)
print("     first  %s  id=%s" % (s1, b1.get("id")))
print("     second %s  id=%s  duplicate=%s"
      % (s2, b2.get("id"), b2.get("duplicate")))
seq_ok = (s1 == 202 and s2 == 200 and b2.get("duplicate") is True
          and b1.get("id") == b2.get("id"))
print("     %s" % ("same id returned, nothing stored twice" if seq_ok
                   else "** WRONG **"))

print()
print("  2. the same event eight times AT ONCE (the case KV loses alone)")
body2 = json.dumps({"id": f"dup_race_{stamp}", "kind": "demo"})
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(lambda _: post(body2), range(8)))

codes = [s for s, _ in results]
ids = {b.get("id") for _, b in results if b.get("id")}
accepted = codes.count(202)
dups = codes.count(200)
print("     status codes : %s" % codes)
print("     distinct ids : %d  %s" % (len(ids), list(ids)[:2]))
print("     202 accepted : %d      200 duplicate : %d" % (accepted, dups))

race_ok = accepted == 1 and dups == 7 and len(ids) == 1
print("     %s" % ("one accepted, seven told the first one's id"
                   if race_ok else "** CHECK THE ROW COUNT BELOW **"))

print()
print("  Verify in D1:")
print("    npx wrangler d1 execute f-keys-relay --remote -y --command \\")
print("      \"SELECT sender_id, COUNT(*) n FROM events"
      " WHERE sender_id LIKE 'dup_%%' GROUP BY sender_id\"")

sys.exit(0 if (seq_ok and race_ok) else 1)
