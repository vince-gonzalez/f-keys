#!/usr/bin/env python3
"""a11y - the third build gate, beside contrast and typefloor.

Accessibility audit over every HTML page, against named WCAG criteria.

WHY A RUBRIC AND NOT A SCORE OUT OF TEN

"How accessible is it" has no answer until the denominator is stated.
So this checks a fixed list of WCAG 2.2 A/AA success criteria that can be
decided from static HTML, names the criterion on every finding, and
reports the percentage of those criteria that pass. Anything requiring a
keyboard, a screen reader or a human eye is listed as NOT TESTED rather
than silently folded into a number, because counting untested things as
passes is how a site gets an accessibility badge it has not earned.

Usage:
    python a11y_audit.py <dir-or-file> [more...]
    python a11y_audit.py --url https://example.com
"""
import io
import os
import re
import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# criterion id -> (level, human name)
CRITERIA = {
    "1.1.1-img":     ("A",  "Non-text content: every img has an alt attribute"),
    "1.1.1-altquality": ("A",  "Non-text content: alt describes the image, not labels it"),
    "1.1.1-svg":     ("A",  "Non-text content: inline svg used as an image is named"),
    "1.1.1-canvas":  ("A",  "Non-text content: canvas has a text alternative"),
    "1.3.1-labels":  ("A",  "Info and relationships: form controls have labels"),
    "1.3.1-table":   ("A",  "Info and relationships: data tables have header cells"),
    "1.3.1-heading": ("A",  "Info and relationships: heading levels do not skip"),
    "2.4.1-bypass":  ("A",  "Bypass blocks: a skip link or a main landmark exists"),
    "2.4.2-title":   ("A",  "Page titled: non-empty title element"),
    "2.4.4-linktext":("A",  "Link purpose: no empty or meaningless link text"),
    "3.1.1-lang":    ("A",  "Language of page: html lang is set"),
    "4.1.2-name":    ("A",  "Name, role, value: buttons and controls have names"),
    "1.4.2-autoplay":("A",  "Audio control: no autoplaying media"),
    "2.4.3-taborder":("A",  "Focus order: no positive tabindex"),
    "4.1.1-dupid":   ("A",  "Parsing: no duplicated id attributes"),
    "2.4.7-focus":   ("AA", "Focus visible: a :focus or :focus-visible style exists"),
    "1.4.4-zoom":    ("AA", "Resize text: viewport does not block zoom"),
}

NOT_TESTED = [
    ("2.1.1 Keyboard",            "every control reachable and operable by keyboard"),
    ("2.4.3 Focus order",         "that the order actually makes sense"),
    ("1.1.1 alt QUALITY",         "whether an alt text is accurate and useful"),
    ("1.4.3 Contrast",            "covered separately by the repo's contrast gate"),
    ("1.4.4 Text size",           "covered separately by the repo's typefloor gate"),
    ("1.2.x Media",               "captions and audio description for video"),
    ("4.1.3 Status messages",     "live regions announcing dynamic change"),
    ("3.3.x Forms",               "error identification and recovery in practice"),
    ("Screen reader reality",     "how NVDA or VoiceOver actually reads the page"),
]

STYLE_ROOTS = []

VOID_ALT = re.compile(r"<img\b(?![^>]*\balt\s*=)[^>]*>", re.I)
IMGS = re.compile(r"<img\b[^>]*>", re.I)
MEANINGLESS = ("click here", "read more", "here", "link", "more", "this",
               "learn more", "details")


def check(html, label):
    """Return {criterion: [findings]} for one document."""
    f = {}

    def add(c, msg):
        f.setdefault(c, []).append(msg)

    low = html.lower()

    # 3.1.1 lang
    if not re.search(r"<html\b[^>]*\blang\s*=\s*['\"][a-z]", low):
        add("3.1.1-lang", "no lang attribute on <html>")

    # 2.4.2 title
    m = re.search(r"<title\b[^>]*>(.*?)</title>", html, re.S | re.I)
    if not m or not m.group(1).strip():
        add("2.4.2-title", "missing or empty <title>")

    # 1.1.1 img alt
    for tag in VOID_ALT.findall(html):
        add("1.1.1-img", "img without alt: " + re.sub(r"\s+", " ", tag)[:90])

    # 1.1.1 alt QUALITY, which is the check that actually mattered.
    #
    # Presence passed on every page while twelve screenshots said "Key-J
    # running." and one said "QR loading...". Those are labels and states,
    # not descriptions, and on a screenshot the picture IS the content - so
    # a blind reader learned only that an image existed. A gate that proves
    # the attribute is spelled correctly and never reads it is theater.
    for tag in IMGS.findall(html):
        am = re.search(r'\balt\s*=\s*(["\'])(.*?)\1', tag, re.S)
        if not am:
            continue
        alt = re.sub(r"\s+", " ", am.group(2)).strip()
        if not alt:
            continue          # decorative; empty alt is the correct answer
        sm = re.search(r'\bsrc\s*=\s*(["\'])(.*?)\1', tag, re.S)
        src = (sm.group(2) if sm else "")
        low_alt = alt.lower()

        if re.search(r"\.(png|jpe?g|gif|svg|webp)$", low_alt):
            add("1.1.1-altquality", 'alt is a filename: "%s"' % alt[:50])
        # The trailing class is [\s.…]* and not \.? because the real
        # offender was "QR loading..." - three dots, so a single optional
        # period did not reach the end of the string and the check stayed
        # silent on the one value that prompted writing it.
        elif re.search(r"\b(loading|placeholder|todo|tbd|image|img|photo|graphic)"
                       r"\b[\s.…]*$", low_alt):
            add("1.1.1-altquality",
                'alt describes a state or says nothing: "%s"' % alt[:50])
        elif re.fullmatch(r"[\w\s'&.-]{1,40}\s+(running|screenshot|logo|icon)\.?",
                          low_alt):
            add("1.1.1-altquality",
                'alt labels the image instead of describing it: "%s"' % alt[:50])
        elif re.search(r"(shot|screenshot|capture)", src, re.I) and len(alt) < 60:
            add("1.1.1-altquality",
                'screenshot with only %d characters of alt: "%s"'
                % (len(alt), alt[:50]))

    # 1.1.1 canvas
    for tag in re.findall(r"<canvas\b[^>]*>(.*?)</canvas>", html, re.S | re.I):
        pass
    for m2 in re.finditer(r"<canvas\b([^>]*)>(.*?)</canvas>", html, re.S | re.I):
        attrs, inner = m2.group(1), m2.group(2)
        named = re.search(r"aria-label|aria-labelledby|role\s*=", attrs, re.I)
        if not named and not inner.strip():
            add("1.1.1-canvas", "canvas with no fallback content and no aria name")

    # 1.1.1 svg used as content
    for m3 in re.finditer(r"<svg\b([^>]*)>(.*?)</svg>", html, re.S | re.I):
        attrs, inner = m3.group(1), m3.group(2)
        hidden = re.search(r"aria-hidden\s*=\s*['\"]true", attrs, re.I)
        named = re.search(r"aria-label|aria-labelledby|<title", attrs + inner, re.I)
        if not hidden and not named:
            add("1.1.1-svg", "svg neither aria-hidden nor named")

    # 1.3.1 form labels / 4.1.2 names
    for m4 in re.finditer(r"<(input|select|textarea)\b([^>]*)>", html, re.I):
        kind, attrs = m4.group(1).lower(), m4.group(2)
        t = re.search(r"\btype\s*=\s*['\"]?(\w+)", attrs, re.I)
        ttype = (t.group(1).lower() if t else "text")
        if kind == "input" and ttype in ("hidden", "submit", "button", "image", "reset"):
            if ttype in ("submit", "button", "reset") and not re.search(
                    r"\bvalue\s*=|aria-label", attrs, re.I):
                add("4.1.2-name", "%s input with no value or aria-label" % ttype)
            continue
        has_name = re.search(r"aria-label|aria-labelledby|\btitle\s*=", attrs, re.I)
        idm = re.search(r"\bid\s*=\s*['\"]([^'\"]+)", attrs, re.I)
        labelled = False
        if idm:
            labelled = bool(re.search(
                r"<label\b[^>]*\bfor\s*=\s*['\"]" + re.escape(idm.group(1)) + r"['\"]",
                html, re.I))
        if not has_name and not labelled:
            add("1.3.1-labels", "%s has no label, aria-label or title" % kind)

    # 4.1.2 button names
    for m5 in re.finditer(r"<button\b([^>]*)>(.*?)</button>", html, re.S | re.I):
        attrs, inner = m5.group(1), m5.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if not text and not re.search(r"aria-label|aria-labelledby", attrs, re.I):
            add("4.1.2-name", "button with no text and no aria-label")

    # 2.4.4 link text
    for m6 in re.finditer(r"<a\b([^>]*)>(.*?)</a>", html, re.S | re.I):
        attrs, inner = m6.group(1), m6.group(2)
        if not re.search(r"\bhref\s*=", attrs, re.I):
            continue
        text = re.sub(r"<[^>]+>", " ", inner)
        text = re.sub(r"\s+", " ", text).strip().lower().strip(" .>→·")
        if not text:
            if not re.search(r"aria-label|aria-labelledby", attrs, re.I):
                add("2.4.4-linktext", "link with no text and no aria-label")
        elif text in MEANINGLESS:
            add("2.4.4-linktext", 'link text is "%s"' % text[:40])

    # 1.3.1 tables
    for m7 in re.finditer(r"<table\b([^>]*)>(.*?)</table>", html, re.S | re.I):
        attrs, inner = m7.group(1), m7.group(2)
        if re.search(r"role\s*=\s*['\"]presentation|none", attrs, re.I):
            continue
        if "<th" not in inner.lower():
            add("1.3.1-table", "table with no <th> header cells")

    # 1.3.1 heading order
    hs = [int(x) for x in re.findall(r"<h([1-6])\b", html, re.I)]
    if hs:
        prev = hs[0]
        if prev != 1:
            add("1.3.1-heading", "first heading is h%d, not h1" % prev)
        for h in hs[1:]:
            if h > prev + 1:
                add("1.3.1-heading", "h%d follows h%d (level skipped)" % (h, prev))
            prev = h

    # 2.4.1 bypass blocks
    if not re.search(r"<main\b|role\s*=\s*['\"]main", low) and \
       not re.search(r"href\s*=\s*['\"]#(main|content|skip)", low):
        add("2.4.1-bypass", "no <main>, role=main or skip link")

    # 1.4.2 autoplay
    if re.search(r"<(video|audio)\b[^>]*\bautoplay", low):
        add("1.4.2-autoplay", "autoplaying media")

    # 2.4.3 positive tabindex
    for v in re.findall(r"tabindex\s*=\s*['\"]?(\d+)", low):
        if int(v) > 0:
            add("2.4.3-taborder", "positive tabindex=%s" % v)

    # 4.1.1 duplicate ids
    ids = re.findall(r"\bid\s*=\s*['\"]([^'\"]+)['\"]", html, re.I)
    seen, dup = set(), set()
    for i in ids:
        if i in seen:
            dup.add(i)
        seen.add(i)
    for d in sorted(dup)[:5]:
        add("4.1.1-dupid", 'duplicate id="%s"' % d)

    # 2.4.7 focus visible
    #
    # THIS CHECK WAS WRONG ONCE AND ITS WRONGNESS WAS INVISIBLE. It looked
    # only inside the document, so a site whose focus styles live in an
    # external stylesheet - which is every well-built site - came back
    # failing on every page. It reported 122 failures on the run AFTER the
    # fix had landed. A check that cannot pass is not a check.
    #
    # Linked local stylesheets are now read as well, and the finding only
    # stands when no :focus rule exists in the document OR in any sheet the
    # document pulls in.
    if re.search(r"<(button|a|input|select|textarea)\b", low):
        css = ""
        for href in re.findall(
                r"<link\b[^>]*href\s*=\s*['\"]([^'\"]+\.css)[^'\"]*['\"]",
                html, re.I):
            cand = href.split("?")[0].lstrip("/")
            for base in (STYLE_ROOTS or ["."]):
                fp = os.path.join(base, cand)
                if os.path.isfile(fp):
                    css += io.open(fp, encoding="utf-8",
                                   errors="replace").read()
                    break
        both = low + css.lower()
        if ":focus" not in both and "focus-visible" not in both:
            add("2.4.7-focus",
                "no :focus or :focus-visible in the document or its stylesheets")

    # 1.4.4 zoom
    mv = re.search(r"<meta\b[^>]*name\s*=\s*['\"]viewport['\"][^>]*>", html, re.I)
    if mv:
        c = mv.group(0).lower()
        if "user-scalable=no" in c or re.search(r"maximum-scale\s*=\s*1(\.0)?\b", c):
            add("1.4.4-zoom", "viewport blocks zoom")

    return f


def gather(paths):
    docs = []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in
                           (".git", "node_modules", ".wrangler", "dist", "retired")]
                for fn in files:
                    if fn.endswith(".html"):
                        fp = os.path.join(root, fn)
                        docs.append((os.path.relpath(fp, p),
                                     io.open(fp, encoding="utf-8",
                                             errors="replace").read()))
        elif os.path.isfile(p):
            docs.append((p, io.open(p, encoding="utf-8", errors="replace").read()))
    return docs


def report(docs, title):
    percrit = {}
    perdoc = {}
    for name, html in docs:
        f = check(html, name)
        perdoc[name] = f
        for c, msgs in f.items():
            percrit.setdefault(c, {"docs": 0, "count": 0, "example": msgs[0]})
            percrit[c]["docs"] += 1
            percrit[c]["count"] += len(msgs)

    print("=" * 78)
    print("%s  —  %d pages" % (title, len(docs)))
    print("=" * 78)
    print()
    passed = [c for c in CRITERIA if c not in percrit]
    failed = [c for c in CRITERIA if c in percrit]
    print("  %-16s %-5s %-7s %-9s %s" % ("CRITERION", "LVL", "PAGES", "FINDINGS", "WHAT"))
    print("  " + "-" * 74)
    for c in sorted(CRITERIA, key=lambda x: (x not in percrit, x)):
        lvl, nm = CRITERIA[c]
        if c in percrit:
            d = percrit[c]
            print("  %-16s %-5s %-7d %-9d %s" % (c, lvl, d["docs"], d["count"], nm[:34]))
        else:
            print("  %-16s %-5s %-7s %-9s %s" % (c, lvl, "-", "pass", nm[:34]))
    print()
    pct = 100.0 * len(passed) / len(CRITERIA)
    print("  PASS: %d of %d statically-checkable criteria = %.0f%%"
          % (len(passed), len(CRITERIA), pct))
    clean = sum(1 for n in perdoc if not perdoc[n])
    print("  pages with zero findings: %d of %d (%.0f%%)"
          % (clean, len(docs), 100.0 * clean / max(1, len(docs))))
    return percrit, perdoc, pct


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        # Same convention as contrast.py and typefloor.py: no argument means
        # this repository.
        args = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    if "--url" in sys.argv:
        url = args[0]
        req = urllib.request.Request(url, headers={"user-agent": "a11y-audit/0.1"})
        html = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
        report([(url, html)], url)
    else:
        STYLE_ROOTS.extend([a for a in args if os.path.isdir(a)])
        docs = gather(args)
        percrit, perdoc, pct = report(docs, " ".join(args))
        print()
        print("  NOT TESTED HERE (counting these as passes would be the lie):")
        for c, w in NOT_TESTED:
            print("    %-26s %s" % (c, w))
        print()
        print("  WORST PAGES")
        worst = sorted(perdoc.items(),
                       key=lambda kv: -sum(len(v) for v in kv[1].values()))[:10]
        for n, f in worst:
            tot = sum(len(v) for v in f.values())
            if tot:
                print("    %-52s %3d findings  %s" % (n[:52], tot,
                      ",".join(sorted(f))[:40]))
