#!/usr/bin/env python3
"""
============================================================
slopgate - finds the machine in the prose
F-Keys | www.f-keys.com
------------------------------------------------------------
Every other gate here checks something a machine can measure
exactly: a contrast ratio, a font size, a retired brand name.
This one checks a thing that is softer and matters more - does
the writing sound like a person, or does it sound like a model
that was asked to sound like a person.

It does not use a model to decide. It counts, because a count
can be argued with and a verdict cannot.

Three kinds of finding:

  TELL       a word or phrase that is close to a fingerprint.
             "delve", "tapestry", "a testament to". Weight 3.
  TIC        a sentence shape models fall into. "It's not just
             X, it's Y." "Whether you're X or Y." Weight 2.
  COUNT      a total recited as an achievement. Skipped on the log
             and the status page, where a number is the content.
  BOAST      self-praise, or marketing scaffolding on what is a
             catalogue. Applies everywhere. Weight 3.
  DRIFT      a house rule about this specific site's voice:
             third person about him, subtractive counts,
             hedging. Weight 3.

Volume is the signal, not the single hit. One "crucial" is a
word; nine is a habit. So a term with a floor only counts once
the file crosses that floor, and the score is per thousand
words so a long page is not punished for being long.

Run:  python tools/slopgate.py [path] [--list] [--json] [--top N]
Exit: 1 if any file is over the threshold, else 0.
============================================================
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "dist", "build", "vendor", "assets", "fonts", ".wrangler",
             ".private-snapshot", "gatekit"}

# Score per 1000 words at or above which a file fails...
THRESHOLD = 12.0
# ...but never on fewer than this many raw points. One unlucky word on a
# short page is a word. A voice problem is a habit, and a habit repeats.
MIN_SCORE = 6

# ── the vocabulary ──────────────────────────────────────────
# (pattern, weight, floor) - floor is how many hits a file needs
# before any of them count. A floor of 1 means one is too many.

TELLS = [
    # close to fingerprints: rare in human writing, common in generated
    (r"\bdelv(?:e|es|ing|ed)\b",                     3, 1),
    (r"\btapestr(?:y|ies)\b",                        3, 1),
    (r"\ba testament to\b",                          3, 1),
    (r"\bin the (?:ever[- ]evolving|rapidly evolving)\b", 3, 1),
    (r"\bever[- ]evolving\b",                        3, 1),
    (r"\bnavigat(?:e|ing) the (?:complex|world|landscape|realm)", 3, 1),
    (r"\bthe (?:world|realm|landscape) of\b",        3, 1),
    (r"\bin today's (?:digital )?(?:world|age|landscape|market)\b", 3, 1),
    (r"\bunlock(?:ing)? the (?:power|potential|secrets)\b", 3, 1),
    (r"\bharness(?:ing)? the power\b",               3, 1),
    (r"\bembark(?:ing)? on\b",                       3, 1),
    (r"\bat the forefront of\b",                     3, 1),
    (r"\bplays? a (?:pivotal|crucial|vital|key) role\b", 3, 1),
    (r"\bit'?s worth noting\b",                      3, 1),
    (r"\bneedless to say\b",                         3, 1),
    (r"\blet'?s (?:dive|delve) in",                  3, 1),
    (r"\bdive deep(?:er)? into\b",                   3, 1),
    (r"\bgame[- ]chang(?:er|ing)\b",                 3, 1),
    (r"\bcutting[- ]edge\b",                         3, 1),
    (r"\bstate[- ]of[- ]the[- ]art\b",               3, 1),
    (r"\bsynerg(?:y|ies|istic)\b",                   3, 1),
    (r"\bparadigm shift\b",                          3, 1),
    (r"\bin conclusion\b",                           3, 1),
    (r"\bmyriad\b",                                  3, 1),
    (r"\bplethora\b",                                3, 1),
    (r"\bbustling\b",                                3, 1),

    # real words, overused: only a tell once they pile up
    (r"\bseamless(?:ly)?\b",                         2, 2),
    (r"\beffortless(?:ly)?\b",                       2, 2),
    (r"\belevat(?:e|es|ing) your\b",                 2, 1),
    (r"\bempower(?:s|ing|ed)?\b",                    2, 2),
    (r"\bleverag(?:e|es|ing|ed)\b",                  2, 2),
    (r"\bstreamlin(?:e|es|ing|ed)\b",                2, 2),
    (r"\bcurated\b",                                 2, 2),
    (r"\bbespoke\b",                                 2, 2),
    (r"\bvibrant\b",                                 2, 2),
    (r"\bmeticulous(?:ly)?\b",                       2, 2),
    (r"\bholistic\b",                                2, 2),
    (r"\brobust\b",                                  1, 3),
    (r"\bcrucial\b",                                 1, 3),
    (r"\bvital\b",                                   1, 3),
    (r"\bpivotal\b",                                 2, 2),
    (r"\bintricate\b",                               2, 2),
    (r"\bnuanced\b",                                 2, 2),
    (r"\bcomprehensive\b",                           1, 3),
    (r"\bfoster(?:s|ing)?\b",                        2, 2),
    (r"\bunderscor(?:e|es|ing)\b",                   2, 2),
    (r"\brevolutioni[sz](?:e|es|ing)\b",             3, 1),
]

TICS = [
    # the shapes, not the words
    (r"(?i)\bit'?s not (?:just|only) [^.!?]{3,60}?[,—-] it'?s\b",   3, 1),
    (r"(?i)\bthat'?s not [^.!?]{3,50}?\. that'?s\b",                     2, 2),
    (r"(?i)\bnot only [^.!?]{3,60}? but also\b",                         2, 1),
    (r"(?i)\bwhether you'?re [^.!?]{3,50}? or\b",                        2, 1),
    (r"(?i)\bwhen it comes to\b",                                        2, 2),
    (r"(?i)\bthe (?:key|secret|beauty) (?:is|to|of)\b",                  2, 2),
    (r"(?i)\bmore than just\b",                                          2, 1),
    (r"(?i)\bisn'?t (?:just|only) about\b",                              2, 1),
    (r"(?i)\bhere'?s the thing\b",                                       2, 1),
    (r"(?i)\bat the end of the day\b",                                   2, 1),
    (r"(?i)\bone thing is (?:clear|certain)\b",                          2, 1),
    (r"(?i)\bsay goodbye to\b",                                          3, 1),
    (r"(?i)\bthink of it (?:as|like)\b",                                 1, 2),
    (r"(?i)\bbuilt (?:from the ground up|with love|to last)\b",          2, 1),
    (r"(?i)\byour (?:one[- ]stop|go[- ]to) (?:shop|solution|destination)\b", 3, 1),
]

# ── house voice, specific to this site ──────────────────────
# These are his rulings, not general style advice.

# ── register: cold and technical, his ruling 2026-09-24 ──────
# "Minimize word count and boastfulness. All wording. Technical field
#  register... coldly mechanical. But super important you don't repeat
#  '47 packages 9 npm' like anyone reading will care."
#
# A datasheet states a number in a table. Prose that states it AT the
# reader is a boast. So these catch the sentence, not the figure - the
# About facts table carries the live count and is meant to.

# Pages whose function is to report a measurement. A number in the log or
# on the status page is the content, not a brag: "the first run reported
# 457 installs a week" is a record, and "checking deposits ... ok 58 works"
# is a check printing its own output. The voice rules still apply there.
REPORTING = ("log/", "status/", "portfolio.html", "snapshot", "latest.json")

BOAST_COUNTS = [
    # counts recited as achievement
    # A bare number plus a noun is not a boast on its own: the intake
    # form offers "Online Store (up to 20 products)", which is a
    # customer's store, and ROADMAP.md says "8 of 22 products are not
    # shipped", which is self-critical. Only a possessive frame counts.
    (r"(?i)\b(?:my|our|his) \d{2,}\+? (?:packages|products|repos|deposits|works)\b", 3, 1),
    (r"(?i)\b\d{2,}\+? (?:packages|products) (?:across|shipped|published|live on)\b", 3, 1),
    (r"(?i)\b(?:forty-seven|fifty-six|thirty-five|twenty-eight|nineteen|nine) (?:packages|works|deposits|servers|merges|pull requests)\b", 3, 1),
    (r"(?i)\bpackages are installed\b", 3, 1),
    # The shape he named: an inventory recited as a lede - "Four
    # command-line tools, sixteen PyPI packages, nineteen on npm". Two or
    # more counted nouns in one breath is a brag, and it goes stale: that
    # line said sixteen PyPI when the true figure was twenty-eight.
    (r"(?i)\b(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|[0-9]{1,3})[a-z-]* (?:PyPI |npm |MCP |command-line )?(?:packages|tools|servers|repos|repositories|projects|products)\b[^.!?]{0,40}?, (?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|[0-9]{1,3})[a-z-]* ", 3, 1),
    (r"(?i)\b(?:installed|downloaded) (?:more than |over )?[\w-]+ (?:thousand|hundred) times\b", 3, 1),
    (r"(?i)\b(?:are|were) deposited with DOIs\b", 3, 1),
    (r"(?i)\b\w+ pull requests to\b", 3, 1),
]

BOAST_VOICE = [
    # self-praise and effort claims
    # NOT here: "every one of them". Key-J's privacy page uses it to say
    # what the app does NOT read, which is the opposite of a boast, and
    # the sentence it came from is caught by the "I designed, wrote" rule.
    (r"(?i)\bI (?:designed|wrote|built|shipped),? (?:wrote|deployed|documented)", 3, 1),
    (r"(?i)\bfrom the ground up\b", 3, 1),
    (r"(?i)\bsingle[- ]handedly\b", 3, 1),
    (r"(?i)\bthe whole company\b", 2, 1),
    (r"(?i)\bwhat I (?:ship|build and keep running)\b", 2, 1),
    # marketing scaffolding on a catalogue
    # NOT a bare "who it is for": Trailer Load uses it as a facts-table
    # row with a one-line answer, which is a spec. What he killed was
    # the heading over a paragraph of customer personas, and the two
    # rules below catch that without catching the table.
    (r"(?i)\bthere is no single customer\b", 3, 1),
    (r"(?i)\bthe people who end up here\b", 3, 1),
    (r"(?i)\bwhat is on the shelves\b", 2, 1),
    (r"(?i)\bwhat to expect\b", 2, 1),
    (r"(?i)\bwhat not to expect\b", 2, 1),
]

DRIFT = [
    # third person about himself - his ruling after outside feedback
    (r"\bVince(?:nt)? Gonzalez is\b",                                3, 1),
    (r"\bVince(?:nt)? Gonzalez,? an? (?:independent|self)\b",         3, 1),
    (r"\bF-Keys is Vince(?:nt)? Gonzalez\b",                          3, 1),
    (r"\bbuilt by Vince(?:nt)? Gonzalez\b",                           3, 1),
    # the "big boy" clause - he never claimed to work alone
    (r"\bworking alone\b",                                            3, 1),
    (r"\bby the same person\b",                                       3, 1),
    (r"\bone[- ]man (?:shop|band|team)\b",                            3, 1),
    (r"\bsolo (?:developer|builder|founder)\b",                       3, 1),
    # subtractive counts - say what is live, not what is not
    (r"\b(?:the rest|the others?) (?:are|is) (?:labell?ed |marked )?(?:alpha|beta|unfinished|coming)\b", 3, 1),
    # NOTE: "32 of them are live" is NOT a violation - he asked for exactly
    # that phrasing ("WE CAN'T SAY 32 LIVE?"). The ruling was against
    # publishing the leftover, which the rule above catches. Do not add a
    # rule that catches the count itself.
    # hedging and AI disclosure
    (r"(?i)\b(?:may|might|can) help you\b",                            2, 2),
    (r"(?i)\bcan be a great way to\b",                                 3, 1),
    (r"(?i)\bas an AI\b",                                              3, 1),
    # A DISCLOSURE, not the subject. He has papers titled "AI-Generated
    # Evidence Admissibility" and a note about a bad AI-generated forum
    # answer; neither is a disclosure, and a rule that cannot tell the
    # difference flags his own scholarship as slop. So the page has to be
    # talking about ITSELF.
    (r"(?i)\bthis (?:page|site|post|article|document|content|text|copy)\b[^.!?]{0,60}\b(?:AI|Claude|ChatGPT|GPT)[- ]?(?:generated|written|assisted)?\b", 3, 1),
    (r"(?i)\b(?:written|generated|created|produced) (?:by|with|using) (?:an? )?(?:AI|LLM|Claude|ChatGPT|GPT)\b", 3, 1),
    # Deliberately NOT here: a bare "AI-generated content". It is the term
    # of art in EU AI Act Article 50 and the subject of two of his papers,
    # so on this site it is scholarship far more often than it is a
    # confession. Self-reference is what makes it a disclosure.
    (r"(?i)\bwith (?:the help of )?AI assistance\b",                    3, 1),
]

ALL = ([("TELL", p, w, f) for p, w, f in TELLS]
       + [("TIC", p, w, f) for p, w, f in TICS]
       + [("COUNT", p, w, f) for p, w, f in BOAST_COUNTS]
       + [("BOAST", p, w, f) for p, w, f in BOAST_VOICE]
       + [("DRIFT", p, w, f) for p, w, f in DRIFT])

COMPILED = [(kind, re.compile(pat), pat, weight, floor)
            for kind, pat, weight, floor in ALL]


# ── turning a file into the words a reader actually sees ────

def visible_text(path, raw):
    """Strip everything a human never reads, and keep line numbers.

    Returns a list of (line_number, text). Scripts, styles, HTML
    comments, code fences and inline code come out, because a
    variable named `delve` is not prose and a gate that cannot
    tell the difference gets switched off.
    """
    ext = os.path.splitext(path)[1].lower()
    text = raw

    if ext in (".html", ".htm"):
        # blank out, do not delete - line numbers have to survive
        def blank(m):
            return re.sub(r"[^\n]", " ", m.group(0))
        text = re.sub(r"(?is)<script\b.*?</script>", blank, text)
        text = re.sub(r"(?is)<style\b.*?</style>", blank, text)
        text = re.sub(r"(?s)<!--.*?-->", blank, text)
        text = re.sub(r"<[^>]+>", lambda m: " " * len(m.group(0)), text)
    elif ext in (".md", ".markdown"):
        def blank(m):
            return re.sub(r"[^\n]", " ", m.group(0))
        text = re.sub(r"(?s)```.*?```", blank, text)
        text = re.sub(r"`[^`\n]+`", lambda m: " " * len(m.group(0)), text)
        text = re.sub(r"(?s)<!--.*?-->", blank, text)

    return list(enumerate(text.split("\n"), start=1))


def unescape(s):
    for a, b in (("&amp;", "&"), ("&mdash;", "—"), ("&ndash;", "–"),
                 ("&nbsp;", " "), ("&quot;", '"'), ("&#39;", "'"),
                 ("&lt;", "<"), ("&gt;", ">"), ("&rsquo;", "'")):
        s = s.replace(a, b)
    return s


def scan(path):
    try:
        raw = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None

    lines = visible_text(path, raw)
    # Unescape ONCE per line, not once per line per pattern. Doing it
    # inside the pattern loop meant ten string replaces x 90 patterns x
    # every line, which took minutes on a 2,550-file corpus.
    lines = [(n, unescape(t)) for n, t in lines]
    joined = " ".join(t for _, t in lines)
    words = len(re.findall(r"[A-Za-z']+", joined))
    if words < 40:
        return None                      # too short to have a voice

    # A page whose job is reporting may state a number; it may not adopt a
    # sales voice. So COUNT is skipped there and BOAST is not.
    relp = path.replace("\\", "/")
    reporting = any(m in relp for m in REPORTING)

    hits = []
    for kind, rx, pat, weight, floor in COMPILED:
        if kind == "COUNT" and reporting:
            continue
        # Cheap whole-file test first. Most patterns miss most files, and
        # a miss here skips the per-line pass entirely.
        if not rx.search(joined):
            continue
        found = []
        for lineno, text in lines:
            for m in rx.finditer(text):
                found.append((lineno, m.group(0).strip(), text.strip()[:110]))
        if len(found) >= floor:
            for lineno, phrase, context in found:
                hits.append({"kind": kind, "line": lineno, "phrase": phrase,
                             "weight": weight, "pattern": pat,
                             "context": context})

    score = sum(h["weight"] for h in hits)
    per_k = round(score * 1000.0 / words, 2)
    return {"path": path, "words": words, "hits": hits,
            "score": score, "per_1000": per_k}


DOUBLE_ESCAPED = re.compile(
    r"&amp;(?:nbsp|mdash|ndash|amp|quot|lt|gt|hellip|middot|rsquo|lsquo"
    r"|ldquo|rdquo|#x?[0-9A-Fa-f]+);")


def escape_check(root):
    """An entity escaped twice shows its own source to the reader.

    TAG's first line read "One player is IT &mdash; get in someone's
    face" on the live page because a lede containing &mdash; went
    through html.escape. Once seen it is trivial to test for, so it is
    tested for.
    """
    bad = []
    for path in walk(root):
        try:
            raw = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        n = len(DOUBLE_ESCAPED.findall(raw))
        if n:
            bad.append((n, os.path.relpath(path, root).replace("\\", "/")))
    return sorted(bad, reverse=True)


def walk(root):
    if os.path.isfile(root):
        yield root
        return
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if name.lower().endswith((".html", ".htm", ".md", ".markdown")):
                yield os.path.join(base, name)


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    list_all = "--list" in args
    top = 20
    if "--top" in args:
        try:
            top = int(args[args.index("--top") + 1])
        except (ValueError, IndexError):
            pass
    positional = [a for a in args
                  if not a.startswith("--") and not a.isdigit()]
    root = os.path.abspath(positional[0]) if positional else ROOT

    results = []
    for path in walk(root):
        r = scan(path)
        if r and (r["hits"] or list_all):
            r["rel"] = os.path.relpath(path, root).replace("\\", "/")
            results.append(r)

    escapes = escape_check(root)
    results.sort(key=lambda r: (-r["per_1000"], -r["score"]))
    # Both conditions: a rate high enough to be a habit, AND enough raw
    # points that it is not one unlucky word on a short page.
    failing = [r for r in results
               if r["per_1000"] >= THRESHOLD and r["score"] >= MIN_SCORE]

    if as_json:
        print(json.dumps({"threshold": THRESHOLD,
                          "scanned": len(results),
                          "failing": len(failing),
                          "files": results[:top]}, indent=1))
        return 1 if failing else 0

    if escapes:
        print("  slopgate: %d double-escaped entit(ies) in %d file(s) - these"
              % (sum(n for n, _ in escapes), len(escapes)))
        print("            render as their own source text to a reader")
        print()
        for n, rel in escapes[:12]:
            print("           %3d  %s" % (n, rel))
        print()

    if not results:
        if not escapes:
            print("  slopgate: clean - nothing in the prose reads as generated")
        return 1 if escapes else 0

    print("  slopgate: %d file(s) with findings, %d over %.0f per 1000 words\n"
          % (len(results), len(failing), THRESHOLD))

    for r in results[:top]:
        flag = ("FAIL" if (r["per_1000"] >= THRESHOLD
                           and r["score"] >= MIN_SCORE) else "    ")
        print("  %s %6.2f/1k  %3d pts  %5d words  %s"
              % (flag, r["per_1000"], r["score"], r["words"], r["rel"]))
        seen = set()
        for h in sorted(r["hits"], key=lambda x: (-x["weight"], x["line"])):
            key = h["phrase"].lower()
            if key in seen:
                continue
            seen.add(key)
            if len(seen) > 6:
                print("           ... and %d more"
                      % (len(r["hits"]) - 6))
                break
            print("           %-5s L%-5d %s"
                  % (h["kind"], h["line"], h["phrase"]))
        print()

    if len(results) > top:
        print("  ... %d more file(s) with findings not shown (--top N)\n"
              % (len(results) - top))

    return 1 if (failing or escapes) else 0


if __name__ == "__main__":
    sys.exit(main())
