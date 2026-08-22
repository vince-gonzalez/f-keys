#!/usr/bin/env python3
"""
============================================================
buildmd - the markdown variant of every generated page
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
An agent that asks for `Accept: text/markdown` was handed the
Explorer window: a tree, a toolbar, a status bar and the
content buried in the middle of it. None of that chrome is
the answer to anything, and an agent pays for all of it.

This converts the content pane of each generated page - and
only the content pane - into markdown, so the same words are
available without the window around them. It reads the built
HTML rather than the catalogue, so the two cannot disagree:
if buildsite changes a sentence, the markdown changes with it.

The Worker in worker/ is what actually serves these in
response to an Accept header. Without it these files are
still fetchable directly at their .md URL.

WORKFLOW STACK
  1. content()  - lift the content pane out of a built page
  2. convert()  - the tag subset the generator emits, to md
  3. main()     - write a .md beside every generated .html

Run:  python tools/buildmd.py
      python tools/buildmd.py --check
============================================================
"""

import html as htmllib
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://f-keys.com"


def content(source):
    """The content pane, without the window that surrounds it."""
    m = re.search(r'<section class="content sunken">(.*?)</section>',
                  source, flags=re.S)
    return m.group(1) if m else ""


def head(source):
    def grab(pattern):
        m = re.search(pattern, source, flags=re.S)
        return htmllib.unescape(m.group(1)).strip() if m else ""
    return (grab(r"<title>(.*?)</title>"),
            grab(r'<meta name="description" content="(.*?)">'),
            grab(r'<link rel="canonical" href="(.*?)">'))


def inline(s):
    """Links, bold and entities. Everything else is dropped."""
    # the folder and document glyphs are chrome, and they were riding
    # along inside the link text as "[<doc glyph>Key-J](...)"
    s = re.sub(r'<span class="ic">.*?</span>', "", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<a [^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>",
               lambda m: "[{}]({})".format(
                   re.sub(r"<[^>]+>", "", m.group(2)).strip(),
                   m.group(1) if "://" in m.group(1) or
                   m.group(1).startswith("mailto:") else SITE + m.group(1)),
               s, flags=re.S | re.I)
    s = re.sub(r"</?(b|strong)>", "**", s, flags=re.I)
    s = re.sub(r"</?(i|em)>", "*", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmllib.unescape(s)
    return re.sub(r"[ \t]+", " ", s).strip()


def cells(row, tag):
    return [inline(c) for c in
            re.findall(r"<{0}[^>]*>(.*?)</{0}>".format(tag), row, flags=re.S | re.I)]


def table(block):
    """Both table shapes the generator emits: the product listing, which
    has a header row, and the facts table, which is label/value pairs."""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", block, flags=re.S | re.I)
    if not rows:
        return ""
    # A row of th and nothing else is a header. A row of th AND td is a
    # facts row, where the th is the label - reading it as a header drops
    # its value, which is how Key-J briefly lost its version number.
    first_th, first_td = cells(rows[0], "th"), cells(rows[0], "td")
    header = first_th if first_th and not first_td else []
    body = []
    for r in rows[1:] if header else rows:
        th, td = cells(r, "th"), cells(r, "td")
        if th and td:                      # facts table: label then value
            body.append(th + td)
        elif td:
            body.append(td)
    if not body:
        return ""
    width = max([len(header)] + [len(r) for r in body])
    if not header:
        # markdown has no headerless table, and a facts table read without
        # one is two anonymous columns
        header = ["Field", "Value"] if width == 2 else [""] * width
    header = header + [""] * (width - len(header))
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join([" --- "] * width) + "|"]
    for r in body:
        r = [c.replace("|", "\\|").replace("\n", " ") for c in r]
        out.append("| " + " | ".join(r + [""] * (width - len(r))) + " |")
    return "\n".join(out)


def convert(pane):
    """The generator emits a narrow tag subset, and this handles that
    subset rather than pretending to be a general HTML converter."""
    out = []
    pattern = (r"<(h1|h2|h3)[^>]*>(.*?)</\1>"
               r"|<p[^>]*>(.*?)</p>"
               r"|<ul[^>]*>(.*?)</ul>"
               r"|<table[^>]*>(.*?)</table>")
    for m in re.finditer(pattern, pane, flags=re.S | re.I):
        if m.group(1):
            level = int(m.group(1)[1])
            text = inline(m.group(2))
            if text:
                out.append("#" * level + " " + text)
        elif m.group(3) is not None:
            text = inline(m.group(3))
            if text:
                out.append(text)
        elif m.group(4) is not None:
            items = re.findall(r"<li[^>]*>(.*?)</li>", m.group(4),
                               flags=re.S | re.I)
            lines = [("- " + inline(i)) for i in items if inline(i)]
            if lines:
                out.append("\n".join(lines))
        elif m.group(5) is not None:
            t = table(m.group(5))
            if t:
                out.append(t)
    return "\n\n".join(out)


def page(path):
    source = io.open(path, encoding="utf-8").read()
    title, description, canonical = head(source)
    body = convert(content(source))
    # the heading leads, because a reader and a parser both take the
    # first line as what the page is
    if body.startswith("# "):
        first, rest = (body.split("\n", 1) + [""])[:2]
    else:
        first, rest = "# " + title, body
    meta = []
    if description:
        meta.append("> " + description)
    if canonical:
        meta.append("Canonical: " + canonical)
    parts = [first] + meta + [rest.strip()]
    text = "\n\n".join(p for p in parts if p).rstrip() + "\n"
    # the same pointer the HTML carries, so a markdown reader can find
    # the rest of the site without parsing a nav tree
    return text + "\n---\n\nMore: [all products](" + SITE + \
        ") - [llms.txt](" + SITE + "/llms.txt) - [sitemap](" + \
        SITE + "/sitemap.xml)\n"


def targets():
    """Every page buildsite writes, which is every page this governs."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import buildsite
    names = ["index.html", "about.html", "contact.html", "privacy.html",
             "developers.html", "404.html"]
    names += [c[0] + ".html" for c in buildsite.CATEGORIES]
    names += [os.path.join(s, "index.html") for s in buildsite.PAGES]
    names += [os.path.join("keyj", "privacy", "index.html"),
              os.path.join("keyj", "manual", "index.html")]
    return names


def main():
    check = "--check" in sys.argv
    stale, written = [], 0
    for name in targets():
        src = os.path.join(ROOT, name)
        if not os.path.exists(src):
            print("buildmd: missing", name)
            return 1
        dst = src[:-len(".html")] + ".md"
        text = page(src)
        if check:
            old = io.open(dst, encoding="utf-8").read() if os.path.exists(dst) else None
            if old != text:
                stale.append(os.path.relpath(dst, ROOT).replace("\\", "/"))
            continue
        io.open(dst, "w", encoding="utf-8", newline="\n").write(text)
        written += 1

    if check:
        for s in stale:
            print("buildmd: stale or missing:", s)
        print("buildmd: ok" if not stale else
              "buildmd: {} FAILED - run python tools/buildmd.py".format(len(stale)))
        return 1 if stale else 0

    print("buildmd: {} markdown pages".format(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
