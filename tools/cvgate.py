#!/usr/bin/env python3
"""
============================================================
cvgate - the CV pages are application artifacts, so hold
them to the rules the cover letters are already held to.
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

resume-kit/build_cover_pdf.py has carried five hard gates for
weeks. This site generates CV pages from a SECOND generator
that had none, so the rules were enforced on one artifact and
not the other. What was live on f-keys.com/cv/ as a result:

  - the banned project term, on all four CV pages, twice
    spelled out in full
  - "daily state audit records", which never happened. It was
    a monthly promotional spend budget he allocated himself
  - "national top-15", when the rule is never "nationally" and
    the measured fact is 15th of 400+ across 17 control states
  - "licensed to institutions" for a product with zero sales
  - "Promoted 2022", corrected to 1 May 2023 on 2026-09-09

Every one of those is a claim FACTS.md names. None of them
were caught, because nothing was looking.

Run:  python tools/cvgate.py [path]
============================================================
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Application-facing text only. His product pages may say whatever they
# say about his own products; a CV is a resume and the resume rules bind.
SCOPED = ("cv/",)

BANNED_TERM = ("mcp", "model context", "saydo", "say-do")

BRITISH = ("licence", "defence", "offence", "organisation", "recognise",
           "realise", "analyse", "colour", "favour", "behaviour", "labour",
           "programme", "travelling", "cancelled", "theatre", "apologise",
           "enrolment", "standardise", "optimis", "centred")

# Claims FACTS.md names and forbids outright.
FALSE_CLAIM = [
    (r"daily state audit",
     "never happened. It was a monthly promotional spend budget he "
     "allocated himself, verified in monthly and quarterly expense reports"),
    (r"nationa\w*\s+top[- ]?\d|top[- ]?\d\d?\s+nationa",
     'FACTS.md: never "nationally". The measured fact is 15th of more '
     "than 400 representatives across 17 control states"),
    (r"licen[sc]ed to institutions|institutions licen[sc]e it|"
     r"sold to (?:schools|institutions)",
     "LOCK IN is priced and offered with ZERO sales. No customer verb, ever"),
    (r"promoted\s+(?:in\s+)?2022|supervisor\s+since\s+2022",
     "promoted 1 MAY 2023. His correction 2026-09-09; anything derived "
     "from 2022 was wrong"),
    (r"15\s*[-–]\s*20\s+person",
     "the sort team is fifteen to THIRTY, not fifteen to twenty"),
]

NUM = (r"(?:a decade|fifteen|twenty|thirteen|fourteen|sixteen|seventeen|"
       r"eighteen|nineteen|ten|eleven|twelve|nine|eight|seven|six|five|"
       r"four|three|two|\d{1,2})")
TENURE = [
    re.compile(NUM + r"\s*\+?\s*years?\s+(?:of\s+)?(?:operations|supervis|"
               r"manag|leading|doing|experience|inside|in the)", re.I),
    re.compile(r"for\s+" + NUM + r"\s*years", re.I),
]
OK_NUM = re.compile(r"(?:five|5)", re.I)
BAD_NUM = re.compile(r"(?:a decade|fifteen|twenty|thirteen|fourteen|sixteen|"
                     r"seventeen|eighteen|nineteen|ten|eleven|twelve|nine|"
                     r"eight|seven|six|four|three|two|\d{2,})", re.I)


def visible(path, raw):
    """Drop markup so a class name or a URL is not read as prose."""
    if path.endswith((".html", ".htm")):
        raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
        raw = re.sub(r"(?s)<!--.*?-->", " ", raw)
        raw = re.sub(r"<[^>]+>", " ", raw)
    return " ".join(raw.split())


def walk(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in (".git", "node_modules", "__pycache__")]
        for fn in files:
            if fn.endswith((".html", ".md")):
                p = os.path.join(base, fn)
                rel = os.path.relpath(p, root).replace("\\", "/")
                if any(rel.startswith(s) for s in SCOPED):
                    yield rel, p


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    findings = []
    n = 0

    for rel, path in walk(root):
        n += 1
        try:
            raw = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        flat = visible(path, raw).lower()

        for b in BANNED_TERM:
            if b in flat:
                findings.append((rel, "BANNED TERM", repr(b),
                                 "never on a resume, letter, form or profile"))

        for b in sorted({b for b in BRITISH if b in flat}):
            findings.append((rel, "BRITISH", repr(b),
                             "US spelling only; these are US applications"))

        for pat, why in FALSE_CLAIM:
            m = re.search(pat, flat, re.I)
            if m:
                findings.append((rel, "FALSE CLAIM", repr(m.group(0)), why))

        for p in TENURE:
            for m in p.finditer(flat):
                g = m.group(0).strip()
                if OK_NUM.search(g) and not BAD_NUM.search(g):
                    continue
                findings.append((rel, "TENURE", repr(g),
                                 "state a DATE, never a duration"))

    if not findings:
        print("  cvgate: %d application page(s), clean" % n)
        return 0

    print("  cvgate: %d finding(s) across %d page(s)\n" % (len(findings), n))
    for rel, kind, what, why in findings:
        print("  FAIL  %-11s %-28s %s" % (kind, what, rel))
        print("        %s" % why)
    print("\n  No page was rewritten. Fix buildcv.py and rebuild.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
