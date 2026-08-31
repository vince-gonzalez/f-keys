# Stream Sniper

> They go live. It is on the TV.

Canonical: https://f-keys.com/streamsniper/

A streamer you follow goes live, and it is on the television. No phone, no notification, no clicking &mdash; a small Debian box that starts on boot and puts the stream on the screen.

**MIT** · Debian or Ubuntu · Streamlink, VLC, pygame · starts on boot via systemd

## What it does

Point a spare mini PC at the television and give it a list of Twitch channels. It shows
a clock until someone goes live, then puts them fullscreen with the ads out of the path.
When the stream ends, the clock comes back.

## How it behaves

One username per line in a text file, and order is priority: if two are live, the one
nearer the top gets the screen. A stream already playing runs to the end, so nobody higher
in the list can cut in halfway through. Edits apply at the next check, with no restart.

## How it works

## What it does

## Specifications

| Field | Value |
| --- | --- |
| Licence | MIT |
| Platform | Debian or Ubuntu |
| Needs | Streamlink, VLC, pygame |
| Starts | systemd, on boot |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
