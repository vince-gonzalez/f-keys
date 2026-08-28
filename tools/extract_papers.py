#!/usr/bin/env python3
"""
============================================================
extract_papers - the papers page, turned into data
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
papers/index.html was the source of truth for 36 deposited
works, and the only tool that touched it parsed the HTML and
rewrote it in place. That works until it does not: there is no
copy of the data that is not markup, so every change is a
regex against a page.

This reads that page once and writes papers/papers.json. From
then on the page is generated from the data like every other
page on this site, and the data can be checked.

It runs ONCE. After papers.json exists, the JSON is the
source and this script is history.

Run:  python tools/extract_papers.py
============================================================
"""

import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "papers", "index.html")
OUT = os.path.join(ROOT, "papers", "papers.json")


def unescape(s):
    return (s.replace("&#x27;", "'").replace("&amp;", "&")
             .replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#8202;", " ")
             .replace("&nbsp;", " ").strip())


def strip_tags(s):
    return unescape(re.sub(r"<[^>]+>", "", s))


def main():
    html = io.open(SRC, encoding="utf-8").read()

    groups = []
    for gm in re.finditer(
            r'<details class="group" id="([^"]+)"[^>]*>\s*'
            r'<summary>\s*<h2>(.*?)</h2>\s*'
            r'(?:<p class="group-note">(.*?)</p>)?\s*</summary>(.*?)</details>',
            html, re.S):
        gid, head_raw, note, body = gm.groups()
        head = strip_tags(re.sub(r'<span class="count">.*?</span>', "",
                                 head_raw))
        entries = []
        for em in re.finditer(r'<div class="entry">(.*?)</div>', body, re.S):
            e = em.group(1)
            t = re.search(r'<h3><a href="([^"]+)">(.*?)</a></h3>', e, re.S)
            if not t:
                continue
            meta = re.search(r'<p class="meta">(.*?)</p>', e, re.S)
            meta_txt = strip_tags(meta.group(1)) if meta else ""
            date, kind = "", ""
            parts = re.split(r"\s*[·–—�]\s*", meta_txt)
            if parts:
                date = parts[0].strip()
                kind = parts[1].strip() if len(parts) > 1 else ""
            paras = re.findall(r"<p(?![^>]*class)[^>]*>(.*?)</p>", e, re.S)
            abstract = strip_tags(paras[0]) if paras else ""
            links = []
            for lm in re.finditer(r'<a href="([^"]+)">(.*?)</a>', e, re.S):
                href, label = lm.group(1), strip_tags(lm.group(2))
                if label and href != t.group(1):
                    links.append({"label": label, "href": href})
                elif label and label not in ("",) and href == t.group(1) \
                        and label.lower() == "abstract":
                    links.append({"label": label, "href": href})
            seen, uniq = set(), []
            for l in links:
                k = (l["label"], l["href"])
                if k in seen:
                    continue
                seen.add(k)
                uniq.append(l)
            entries.append({
                "slug": t.group(1).strip("/").split("/")[-1],
                "url": t.group(1),
                "title": strip_tags(t.group(2)),
                "date": date,
                "kind": kind,
                "abstract": abstract,
                "links": uniq,
                "doi": next((l["href"] for l in uniq
                             if "doi.org" in l["href"]), None),
            })
        groups.append({"id": gid, "title": head,
                       "note": strip_tags(note or ""), "entries": entries})

    data = {"groups": groups}
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, indent=1, ensure_ascii=False, sort_keys=False))

    total = sum(len(g["entries"]) for g in groups)
    dois = sum(1 for g in groups for e in g["entries"] if e["doi"])
    print("  groups: %d" % len(groups))
    for g in groups:
        print("    %-34s %d" % (g["title"][:34], len(g["entries"])))
    print()
    print("  entries: %d   with a DOI: %d" % (total, dois))
    print("  wrote papers/papers.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
