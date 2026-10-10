#!/usr/bin/env python3
"""
============================================================
buildstack - /stack/, what the work actually required
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

The portfolio names products. A reader evaluating technical
work cannot tell from "Websites" that the intake funnel is a
Worker writing D1, uploading to R2, handing back links signed
with HMAC and compared in constant time, and sending mail
through an HTTP API because a Worker has no TCP.

So this page is not a skills list. A skills list says "D1" and
proves nothing; anybody can type D1. Each entry here names the
DECISION the work forced, because the decision is the part that
cannot be faked.

EVERY CLAIM WAS READ OUT OF THE SOURCE, not from notes.
Anything that could not be found in code was cut, including a
Queues claim that turned out to be Python's queue module doing
producer/consumer between two threads - a real pattern, a
different one, and labelling it Cloudflare Queues would have
been a lie on a page whose whole purpose is being checkable.

The page also states what is NOT used. A stack page listing
only wins reads as marketing.

Run:  python tools/buildstack.py
============================================================
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import buildsite as B   # noqa: E402

OUT = os.path.join(ROOT, "stack", "index.html")

LEDE = (
    "What the work required, and the decision each piece forced. A list of "
    "technologies proves nothing, so every entry below names the thing that "
    "had to be decided and what it was decided against. All of it is in the "
    "source."
)

SECTIONS = [
 ("Data", [
  ("SQL at the edge, Cloudflare D1",
   "the intake funnel and a five-source data pipeline",
   "D1 binds at most a hundred parameters per query. The upsert binds five "
   "per row, and a chunk size of forty written next to the limit meant every "
   "statement carried two hundred, so every run of every source failed on "
   "“too many SQL variables” and had done for months. The chunk is "
   "now derived from the limit rather than written beside it, so adding a "
   "column cannot quietly put it back over."),

  ("SQLite inside a Durable Object",
   "DaisuPop, a room per game",
   "A room is addressed by name rather than by a generated id, so two "
   "players typing the same room string reach the same object without a "
   "lookup table anywhere. The class is declared in a migration as a "
   "SQLite-backed Durable Object, which puts the room's state and its "
   "storage in the same place as its WebSocket."),

  ("Postgres with row-level security",
   "LOCK IN",
   "A view declared security_invoker runs as the original caller even when "
   "it sits inside a view the owner owns, so owner rights do not pass "
   "through it. Anything that genuinely has to cross the RLS boundary goes "
   "through a SECURITY DEFINER function instead, which is the only "
   "construct that actually changes who the query runs as."),

  ("SQLite on the desktop",
   "PlumHUD",
   "A polling thread writes each reading straight to SQLite and hands the "
   "batch to the interface thread, so the database is never touched from "
   "the thread that draws."),
 ]),

 ("Objects, links and mail", [
  ("R2 with signed, expiring links",
   "the intake funnel",
   "A client's logo is their property, not the internet's, so the bucket is "
   "private and a link in an email cannot carry an admin key. The link "
   "carries its own expiry and an HMAC over it instead, and the signature "
   "is verified BEFORE the database lookup, so file ids cannot be walked by "
   "asking for them."),

  ("Constant-time comparison",
   "the same signature check",
   "Signatures are compared with an XOR walk over the whole string rather "
   "than with ===, because an equality check returns early on the first "
   "wrong character and a wrong signature could then be guessed one "
   "character at a time from how long the answer took."),

  ("Hashing in the log, not the address",
   "the same worker",
   "Visitor addresses are salted, hashed and truncated before they are "
   "written anywhere, so the log cannot identify anyone if it ever leaks."),

  ("Transactional mail on a subdomain",
   "the intake funnel",
   "The apex MX belongs to Apple and every address already forwards "
   "correctly, so sender records went on a send subdomain. Writing SPF at "
   "the apex would have broken mail that was working in order to add mail "
   "that was not. And a Worker has no TCP, so it cannot speak SMTP at all: "
   "an HTTP mail API is a requirement here, not a preference."),

  ("The order is the design",
   "the intake funnel",
   "The database row is written before the mail is sent, and the response "
   "reports recorded and notified as two separate facts. A mail failure "
   "costs a notification. It never costs the enquiry."),
 ]),

 ("Edge and real time", [
  ("Workers, routed on custom domains",
   "several properties",
   "Static assets are served through an assets binding on the same Worker "
   "that handles the dynamic routes, so there is one deploy and one origin "
   "rather than a site and an API that can drift apart."),

  ("WebSockets",
   "DaisuPop over Durable Objects, RemapWrap over a LAN",
   "Two different problems. The game needs every player in a room to see "
   "the same state, which is what the Durable Object is for. RemapWrap "
   "needs a phone to act as an input device for the desktop beside it, so "
   "it runs a local bridge on the network they already share and nothing "
   "leaves the building."),

  ("A native global keyboard hook",
   "Key-J",
   "Installing a system-wide keyboard listener is the same machinery a "
   "keylogger uses. The documentation says exactly that, in those words, "
   "because a reader deciding whether to trust it is entitled to know "
   "before they install rather than after."),

  ("Desktop packaging",
   "Key-J, Electron and NSIS",
   "The installer resolves its scope at compile time rather than "
   "negotiating it at run time. The assisted installer carries a UAC "
   "relaunch and a scope-selection interface that initialise even during a "
   "silent install, which is machinery a package manager has no way to "
   "answer."),
 ]),

 ("Concurrency, and taking things out", [
  ("Producer and consumer across threads",
   "PlumHUD",
   "A daemon thread polls the fleet on a timer and hands batches to the "
   "interface thread through a queue, which the interface drains on its own "
   "clock. Nothing blocks the thread that draws."),

  ("Deleting an event loop",
   "PlumHUD 3.0 to 4.0",
   "The previous version ran a private asyncio loop with an aiohttp session "
   "and a thread-pool fallback behind it. The library underneath already "
   "did the concurrency with the standard library, so the loop, the "
   "optional dependency and the fallback path were all removed. Measured "
   "afterwards: no loss of speed. Three moving parts and one dependency "
   "gone for nothing in return except less to go wrong."),
 ]),
]

def render():
    e = B.esc
    o = ['<div class="doc">', "<h1>Stack</h1>",
         '<p class="sub">%s</p>' % e(LEDE)]
    n = 0
    for title, rows in SECTIONS:
        o.append("<h2>%s</h2>" % e(title))
        for name, where, decision in rows:
            n += 1
            o.append('<div class="stk">'
                     '<div class="stk-h"><strong>%s</strong>'
                     '<span class="stk-w">%s</span></div>'
                     '<p>%s</p></div>' % (e(name), e(where), e(decision)))
    o.append('<p class="note">The products these came out of are on '
             '<a href="/portfolio.html">the work page</a>. Writing, with the '
             'source of every excerpt linked, is at '
             '<a href="/writing/">/writing/</a>.</p>')
    o.append("</div>")
    return "\n".join(o), n


def main():
    body, n = render()
    doc = B.shell(
        "Stack — F-Keys",
        "F-Keys\\Stack",
        body,
        "%d entries" % n,
        description="What the work required and the decision each piece "
                    "forced, read out of the source rather than listed as "
                    "skills.",
        canonical="https://f-keys.com/stack/",
        app="wordpad")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(doc)
    print("  buildstack: /stack/ with %d entries" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
