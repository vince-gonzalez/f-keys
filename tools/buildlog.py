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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    """
    Wrap the entries in the shared Explorer shell. The log used to carry its
    own stylesheet, which is exactly how it drifted into looking like a
    different site from the rest of f-keys.com.
    """
    import buildsite as B

    items = []
    for iso, blocks in entries:
        body = "\n      ".join("<p>{}</p>".format(inline(b)) for b in blocks)
        items.append(
            '<article class="entry"><time datetime="{}">{}</time>\n      {}</article>'
            .format(iso, pretty_date(iso), body))
    inner = "\n".join(items) or '<p class="muted">Nothing logged yet.</p>'

    doc = ('<div class="doc"><h1>Log</h1>'
           '<p class="sub">A working record. What got built, what broke, and '
           'what turned out to be true.</p>' + inner + '</div>')

    return B.shell("Log \u2014 F-Keys", "F-Keys\\Log", doc,
                   "{} entr{}".format(len(entries), "y" if len(entries) == 1 else "ies"),
                   description="A working record of what gets built at F-Keys.",
                   canonical="https://f-keys.com/log/")


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
