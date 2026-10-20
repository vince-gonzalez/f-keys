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
import hashlib
import urllib.request
import urllib.parse

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

# When auditing a live URL, linked stylesheets have to be fetched rather
# than opened. Set by the --url path; empty for a local run, where the
# filesystem answers instead.
STYLE_URL_BASE = ""
_CSS_CACHE = {}


def fetch_css(url):
    """One linked stylesheet, over HTTP. Failure returns "" and is NOT
    treated as 'no focus styles' by the caller, which only concludes that
    after looking everywhere it can reach."""
    if url in _CSS_CACHE:
        return _CSS_CACHE[url]
    try:
        req = urllib.request.Request(
            url, headers={"user-agent": "a11y-audit/0.1"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception:                                        # noqa: BLE001
        body = ""
    _CSS_CACHE[url] = body
    return body

# A <label> element with its whole contents, used to find controls
# that are labelled by being INSIDE one rather than by a for=.
#
# Written with an explicit character class instead of a word boundary,
# after the escape came through as a literal backspace byte and the
# regex silently matched nothing - so the check reported fifty
# correctly-labelled controls as unlabelled and looked like it was
# working the whole time. A regex that cannot match is indistinguishable
# from a rule with nothing to complain about.
LABEL_BLOCK = re.compile(r"<label[\s>][^>]*>.*?</label>|<label>.*?</label>", re.S | re.I)

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
        # A control hidden with inline display:none is not in the
        # accessibility tree, so there is no name for a screen reader to
        # read and nothing for this criterion to decide. Every one of
        # these on this site is a file picker opened by a visible button,
        # which is the normal way to build one. They are named anyway -
        # the cost is nothing, and a later change that reveals one should
        # not silently lose its label - but a missing name on a hidden
        # control is not a barrier and is not counted as one.
        if re.search(r"style\s*=\s*['\"][^'\"]*display\s*:\s*none", attrs,
                     re.I):
            continue
        has_name = re.search(r"aria-label|aria-labelledby|\btitle\s*=", attrs, re.I)
        idm = re.search(r"\bid\s*=\s*['\"]([^'\"]+)", attrs, re.I)

        # EXPLICIT: <label for="x"> ... and the control has id="x".
        labelled = False
        if idm:
            labelled = bool(re.search(
                r"<label\b[^>]*\bfor\s*=\s*['\"]" + re.escape(idm.group(1)) + r"['\"]",
                html, re.I))

        # IMPLICIT: the control sits INSIDE a <label>. This is a valid
        # association and the check used to miss it entirely, which made
        # it report fifty correctly-labelled controls on one page as
        # unlabelled - and would have had somebody "fix" markup that was
        # already right. Anyone testing to 508 needs both forms counted,
        # because authors use both.
        if not labelled and not has_name:
            labelled = any(lm.start() < m4.start() < lm.end()
                           for lm in LABEL_BLOCK.finditer(html))

        if not has_name and not labelled:
            add("1.3.1-labels", "%s has no label, aria-label or title" % kind)

    # 4.1.2 button names
    for m5 in re.finditer(r"<button\b([^>]*)>(.*?)</button>", html, re.S | re.I):
        attrs, inner = m5.group(1), m5.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        # title= counts. It is the last fallback in the accessible-name
        # computation, so a button carrying title="Close" and nothing else
        # does have a name - weaker than aria-label, and not nothing. The
        # check used to ignore it and reported six named buttons as
        # nameless, which is the sort of false positive that teaches
        # people to stop reading the report.
        if not text and not re.search(r"aria-label|aria-labelledby|\btitle\s*=",
                                      attrs, re.I):
            add("4.1.2-name", "button with no text, aria-label or title")

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
    # Script bodies are stripped first. An id inside a JavaScript string
    # is a template for one branch of a widget, and the branches never
    # render together, so counting them finds duplicates the browser
    # never sees. Checked by hand on remapwrap's ed-arg (three branches
    # of one field) and Key-J's seqEmpty (a placeholder the script puts
    # back) before relaxing this.
    markup = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
    ids = re.findall(r"\bid\s*=\s*['\"]([^'\"]+)['\"]", markup, re.I)
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
            got = False
            for base in (STYLE_ROOTS or ["."]):
                fp = os.path.join(base, cand)
                if os.path.isfile(fp):
                    css += io.open(fp, encoding="utf-8",
                                   errors="replace").read()
                    got = True
                    break
            # OVER HTTP TOO. Reading only local files meant that auditing a
            # live URL could never see the stylesheet, so 2.4.7 failed on
            # every remote site whose focus rules are in a sheet - which is
            # every well-built site. The check was right locally and wrong
            # everywhere else, and a false fail on a site that is fine is
            # how a report gets ignored.
            if not got and STYLE_URL_BASE:
                css += fetch_css(urllib.parse.urljoin(STYLE_URL_BASE, href))
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


def lift_function(html, name):
    """Return one JavaScript function's source by matching braces, or ""."""
    i = html.find("function %s(" % name)
    if i < 0:
        return ""
    try:
        j = html.index("{", i)
    except ValueError:
        return ""
    depth, k = 0, j
    while k < len(html):
        if html[k] == "{":
            depth += 1
        elif html[k] == "}":
            depth -= 1
            if depth == 0:
                return html[i:k + 1].replace("\r\n", "\n")
        k += 1
    return ""


# Findings this audit cannot settle by reading, because the markup does
# not exist until the page runs - and which have been settled by running
# it instead.
#
# Each entry carries the function that does the naming and a fingerprint
# of that function's source. EDIT THE FUNCTION AND THE EXCEPTION DIES:
# the hash stops matching, the findings come back, and the report says
# the builder changed. An exception that outlives the thing it was
# granted for is not an exception, it is a hole.
RUNTIME_VERIFIED = {
    ("remapwrap/dashboard.html", "1.3.1-labels"): (
        "row",
        "86aaf299ddaa5bd23d09142790d54b12aafebc0cec667d84e531b91c1753bce1",
        "Twelve key-editor fields are emitted by row(), which attaches an\n"
        "      aria-label carrying the caption it was given. Verified two ways\n"
        "      on 2026-10-17: row(), escAttr() and escHtml() were lifted out of\n"
        "      the page and run in node against six shapes - a select, a number\n"
        "      input, a colour input, an id-less select, a body that already\n"
        "      carries a name, and a label containing a quote - and all six came\n"
        "      back with exactly one correct name; then the source parentheses\n"
        "      were matched to confirm each of the twelve is an argument to a\n"
        "      row() call. The two that were not, add-type and the arg field,\n"
        "      were fixed rather than excused."),
}


def runtime_exception(name, html, crit):
    """(applies, note) for one page and criterion."""
    key = (name.replace("\\", "/"), crit)
    for (page, c), (fn, want, why) in RUNTIME_VERIFIED.items():
        if c != crit or not key[0].endswith(page):
            continue
        got = hashlib.sha256(lift_function(html, fn).encode("utf-8")).hexdigest()
        if not lift_function(html, fn):
            return False, "%s(): NOT FOUND in the page - exception void" % fn
        if got != want:
            return False, ("%s() has changed since it was verified "
                           "(%s...) - exception void, re-verify it"
                           % (fn, got[:12]))
        return True, why
    return False, ""


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
    excepted = []
    for name, html in docs:
        f = check(html, name)
        for c in list(f):
            ok, why = runtime_exception(name, html, c)
            if ok:
                excepted.append((name, c, len(f.pop(c)), why))
            elif why:
                f[c].append("RUN-TIME EXCEPTION VOID: " + why)
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
    if excepted:
        print()
        print("  PASSED BY RUNNING IT, NOT BY READING IT")
        print("  (printed every run, on purpose - a quiet exception is a hole)")
        for name, c, n, why in excepted:
            print("    %s  %s  %d finding(s) set aside"
                  % (name.replace("\\", "/"), c, n))
            print("      %s" % why)
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
        STYLE_URL_BASE = url
        globals()["STYLE_URL_BASE"] = url
        report([(url, html)], url)
        # The honest exclusions belong on BOTH paths. They were printed
        # only on a local run, so auditing a URL produced a report that
        # looked complete and silently dropped the list of things nobody
        # checked - which is the exact lie this section exists to stop.
        print()
        print("  NOT TESTED HERE (counting these as passes would be the lie):")
        for c, w in NOT_TESTED:
            print("    %-26s %s" % (c, w))
        print()
        print("  ONE PAGE ONLY. A criterion passes here only for this URL; "
              "the rest of the site was not fetched.")
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
