#!/usr/bin/env python3
"""Fire real requests at the deployed relay and check what it does.

A unit test proves the function is right. This proves the thing that is
actually running on the internet is right, which is a different claim.

Five requests: one genuine, four forgeries of the kinds that matter.
"""
import hashlib
import hmac
import io
import json
import time
import urllib.request
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://f-keys-relay.vince-848.workers.dev"
SECRET_FILE = r"C:\Users\Admin\Desktop\f-keys-docs\RELAY-DEMO-SECRET.txt"
SECRET = io.open(SECRET_FILE, encoding="utf-8").read().strip().split("\n")[-1]

BODY = json.dumps({"id": "evt_live_1", "kind": "demo", "n": 1})


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
