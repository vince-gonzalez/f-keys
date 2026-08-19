#!/usr/bin/env python3
"""
============================================================
buildlog v1.0.0
Renders log/entries.md into log/index.html.
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
A record of the work that lives on his own domain, where no
algorithm decides who sees it. Writing an entry is appending
to one markdown file. CI renders it.

WORKFLOW STACK
  1. Read log/entries.md
  2. Split on '## YYYY-MM-DD' headers, newest first in the file
  3. Convert a deliberately small subset of markdown
  4. Write log/index.html

FORMAT
  ## 2026-08-19
  First paragraph.

  Second paragraph. **bold**, `code`, [link](https://…).

  ## 2026-08-18
  ...

  Nothing else is supported on purpose. The point is that
  adding an entry never requires thinking about markup.
============================================================
"""

import html
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR  = os.path.join(ROOT, "log")
SRC      = os.path.join(LOG_DIR, "entries.md")
OUT      = os.path.join(LOG_DIR, "index.html")

MONTHS = ("January February March April May June July "
          "August September October November December").split()


def pretty_date(iso):
    """2026-08-19 -> 19 August 2026. Falls back to the raw string."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso)
    if not m:
        return iso
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mo <= 12:
        return iso
    return f"{d} {MONTHS[mo - 1]} {y}"


def inline(text):
    """Escape first, then re-introduce the few marks we allow."""
    t = html.escape(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" rel="noopener">\1</a>', t)
    return t


def parse(md):
    """Return [(iso_date, [paragraph, ...]), ...] in file order."""
    entries = []
    current = None
    for raw in md.splitlines():
        line = raw.rstrip()
        head = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$", line)
        if head:
            current = {"date": head.group(1), "lines": []}
            entries.append(current)
        elif current is not None:
            current["lines"].append(line)

    out = []
    for e in entries:
        blocks, buf = [], []
        for line in e["lines"]:
            if line.strip():
                buf.append(line.strip())
            elif buf:
                blocks.append(" ".join(buf))
                buf = []
        if buf:
            blocks.append(" ".join(buf))
        if blocks:
            out.append((e["date"], blocks))
    return out


def render(entries):
    items = []
    for iso, blocks in entries:
        body = "\n      ".join(f"<p>{inline(b)}</p>" for b in blocks)
        items.append(
            f'''    <article class="entry">
      <time datetime="{iso}">{pretty_date(iso)}</time>
      {body}
    </article>''')
    body = "\n".join(items) or '    <p class="dim">Nothing logged yet.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Log — F-Keys</title>
<meta name="description" content="A working record of what gets built at F-Keys, kept by Vince Gonzalez.">
<link rel="canonical" href="https://f-keys.com/log/">
<meta name="robots" content="index, follow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
:root {{ --bg:#0a0e0a; --panel:#111911; --border:#1f351f;
        --green:#39ff14; --cyan:#00ffcc; --text:#c3dcc3; --dim:#8fae8f; }}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'Share Tech Mono',monospace;
     line-height:1.75;overflow-x:hidden}}
body::before{{content:'';position:fixed;inset:0;z-index:9000;pointer-events:none;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.07) 2px,rgba(0,0,0,.07) 4px)}}
nav{{position:fixed;top:0;left:0;right:0;z-index:10000;height:60px;padding:0 2rem;
    background:rgba(10,14,10,.95);border-bottom:1px solid var(--border);
    display:flex;align-items:center;justify-content:space-between}}
.logo{{font-family:'VT323',monospace;font-size:24px;color:var(--green);letter-spacing:3px}}
.back{{color:var(--dim);text-decoration:none}}
.back:hover{{color:var(--green)}}
main{{max-width:720px;margin:0 auto;padding:8rem 1.5rem 6rem}}
h1{{font-family:'VT323',monospace;font-weight:400;font-size:clamp(48px,9vw,76px);
   color:var(--green);letter-spacing:6px;line-height:1}}
.standfirst{{color:var(--dim);margin:.75rem 0 4rem;max-width:34rem}}
.entry{{padding-bottom:3rem;margin-bottom:3rem;border-bottom:1px solid var(--border)}}
.entry:last-of-type{{border-bottom:0;margin-bottom:0}}
time{{display:block;font-family:'VT323',monospace;font-size:1.5rem;color:var(--cyan);
     letter-spacing:2px;margin-bottom:1rem}}
.entry p{{margin-bottom:1rem}}
.entry p:last-child{{margin-bottom:0}}
code{{color:var(--cyan)}}
a{{color:var(--green)}}
.dim{{color:var(--dim)}}
footer{{border-top:1px solid var(--border);margin-top:4rem;padding-top:1.5rem;
       color:var(--dim);font-size:.85rem;text-align:center}}
footer a{{color:var(--green);text-decoration:none}}
</style>
</head>
<body>

<nav>
  <div class="logo">F-KEYS / LOG</div>
  <a href="/" class="back">← Back to F-Keys</a>
</nav>

<main>
  <h1>LOG</h1>
  <p class="standfirst">A working record. What got built, what broke, and what
     turned out to be true.</p>

{body}

  <footer>
    <p>Kept by Vince Gonzalez · <a href="/">F-Keys</a> · <a href="/status/">status</a></p>
  </footer>
</main>

</body>
</html>
"""


def main():
    if not os.path.exists(SRC):
        print(f"buildlog: no {SRC} - nothing to render")
        return 1
    md = open(SRC, encoding="utf-8").read()
    entries = parse(md)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(entries))
    print(f"buildlog: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} -> log/index.html")
    for iso, blocks in entries[:3]:
        print(f"  {iso}  {len(blocks)} paragraph(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
