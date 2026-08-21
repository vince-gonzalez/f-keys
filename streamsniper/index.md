# Stream Sniper

> They go live. It is on the TV.

Canonical: https://f-keys.com/streamsniper/

They go live. It is on the TV.

| Field | Value |
| --- | --- |
| Licence | MIT |
| Platform | Debian or Ubuntu |
| Needs | Streamlink, VLC, pygame |
| Starts | systemd, on boot |

## What it does

Point a spare mini PC at the television and give it a list of Twitch channels. It shows
a clock until someone goes live, then puts them fullscreen with the ads out of the path.
When the stream ends, the clock comes back.

## How it behaves

One username per line in a text file, and order is priority: if two are live, the one
nearer the top gets the screen. A stream already playing runs to the end, so nobody higher
in the list can cut in halfway through. Edits apply at the next check, with no restart.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
