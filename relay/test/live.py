#!/usr/bin/env python3
"""Fire real requests at the deployed relay and check what it does.

A unit test proves the function is right. This proves the thing that is
actually running on the internet is right, which is a different claim.

Seven requests: one genuine, four forgeries of the kinds that matter,
one deliberate replay, and one unknown endpoint.

THE EVENT ID IS STAMPED PER RUN, and that is not a detail. The first
version of this file sent a hardcoded "evt_live_1" and demanded 202.
It passed exactly once. Every run after that the relay recognised the
id it had already stored and correctly answered 200 duplicate - so a
PASSING dedupe made the happy-path case read as a failure, and the
reflex is to go looking for a bug in the service that is behaving.

A test that can only pass on a virgin database is not testing the
service, it is testing whether anyone ran it before. So: a fresh id
each run for the accept case, and the duplicate behaviour is now a
case of its own that asserts it on purpose rather than tripping over it.
"""
import hashlib
import hmac
import io
import json
import time
import urllib.request
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The address is relay.f-keys.com since 2026-10-10. workers.dev still
# serves the same Worker, so the old host is a fallback, not a second
# service. Every request here sets an explicit user-agent on purpose:
# Cloudflare answers 403 to the Python-urllib default on every zone, so
# a script that does not set one tests the bot rule instead of the relay.
BASE = "https://relay.f-keys.com"
SECRET_FILE = r"C:\Users\Admin\Desktop\f-keys-docs\RELAY-DEMO-SECRET.txt"
SECRET = io.open(SECRET_FILE, encoding="utf-8").read().strip().split("\n")[-1]

# Unique per run. See the docstring: a fixed id makes dedupe look like
# a defect on the second run and every run after it.
EVENT_ID = "evt_live_%d" % int(time.time())
BODY = json.dumps({"id": EVENT_ID, "kind": "demo", "n": 1})


def sign(body, ts, secret=SECRET):
    mac = hmac.new(secret.encode(), f"{ts}.{body}".encode(),
                   hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


def post(path, body, sig):
    req = urllib.request.Request(
        BASE + path, data=body.encode(), method="POST",
        headers={"content-type": "application/json",
                 # Cloudflare bot protection answers 403/1010 to
                 # Python-urllib before the Worker ever sees it. A real
                 # webhook sender has its own agent string; this stands
                 # in for one.
                 "user-agent": "relay-selftest/0.1",
                 **({"x-relay-signature": sig} if sig else {})})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode()[:160]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:160]
    except Exception as e:
        return 0, str(e)[:160]


now = int(time.time())
CASES = [
    ("genuine, correct signature",      "/in/demo", BODY, sign(BODY, now), 202),
    ("body tampered after signing",     "/in/demo", BODY.replace("demo", "evil"),
                                        sign(BODY, now), 401),
    ("signed with the wrong secret",    "/in/demo", BODY,
                                        sign(BODY, now, "wrong-secret"), 401),
    ("replay, signed 2 hours ago",      "/in/demo", BODY,
                                        sign(BODY, now - 7200), 401),
    ("no signature at all",             "/in/demo", BODY, None, 401),
    ("endpoint that does not exist",    "/in/nope", BODY, sign(BODY, now), 404),
    # Asserted, not stumbled into. Same id, same secret, valid signature:
    # a sender retrying something we already hold. 200 and not 202, because
    # 202 would claim we accepted something new and we did not.
    ("REPLAY of the accepted event",    "/in/demo", BODY, sign(BODY, now), 200),
]

print("  %-34s %-6s %-6s %s" % ("CASE", "GOT", "WANT", ""))
print("  " + "-" * 72)
ok = True
for name, path, body, sig, want in CASES:
    status, text = post(path, body, sig)
    good = status == want
    ok &= good
    note = ""
    try:
        note = json.loads(text).get("reason") or json.loads(text).get("error") or ""
    except Exception:
        note = text[:40]
    print("  %-34s %-6s %-6s %s  %s"
          % (name, status, want, "OK" if good else "** WRONG **", note[:30]))

print()
print("  " + ("every case behaved as specified" if ok
              else "SOMETHING IS WRONG - do not advertise this endpoint"))
sys.exit(0 if ok else 1)
