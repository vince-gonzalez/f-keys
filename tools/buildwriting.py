#!/usr/bin/env python3
"""
============================================================
buildwriting - /writing/, a selected-writing portfolio
F-Keys | www.f-keys.com
------------------------------------------------------------
WHAT THIS IS

Excerpts from published and shipped work, grouped by the kind
of writing rather than by project. The point of the page is
not that the sentences are nice. It is that every one of them
can be checked: the deposited papers carry DOIs that cannot be
edited after the fact, and the documentation quotes link to the
file in the repository they were taken from.

WHY IT VERIFIES ITSELF

A page of quotations is exactly the sort of thing that drifts
away from its sources: the source gets edited, the quote does
not, and the page is then misquoting its own author. So each
entry names the file it came from, and the build REFUSES to
write the page if the text is not in that file, character for
character after whitespace is normalised.

Run:  python tools/buildwriting.py
============================================================
"""

import html
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import buildsite as B   # noqa: E402

OUT = os.path.join(ROOT, "writing", "index.html")
GH = "https://github.com/vince-gonzalez/f-keys/blob/main/"
DOI = "https://doi.org/"

LEDE = (
    "Excerpts from deposited papers, measurement write-ups and software "
    "documentation. Each one links to where it came from. The papers carry "
    "DOIs, so the deposited text cannot be changed after the fact, and the "
    "documentation links to the file in the repository."
)

# (quote, attribution, href, doi, file the quote must actually appear in)
SECTIONS = [
 ("When a check should fail", "The gates, and what it costs to have one "
  "that cannot.", [

  ("A gate that reports a pass on a tree it never opened is worse than no "
   "gate, so a positional path is now the root.",
   "gatekit README", GH + "gatekit/README.md", None, "gatekit/README.md"),

  ("A stylesheet using neither has nothing to compare, and it says so and "
   "exits 0 — which in CI reads as a pass on a site nobody checked.",
   "gatekit README", GH + "gatekit/README.md", None, "gatekit/README.md"),

  ("If node is not installed the parity checks skip and say so, because a "
   "check that cannot run must not report success.",
   "keyj-cli README", GH + "keyj-cli/README.md", None, "keyj-cli/README.md"),

  ("Dark grey on navy measured 2.64:1 where body text needs 4.5, and a "
   "person found that, not a build.",
   "gatekit README", GH + "gatekit/README.md", None, "gatekit/README.md"),

  ("Three gates for defects a linter does not have an opinion about, "
   "because none of them is a syntax error.",
   "gatekit README", GH + "gatekit/README.md", None, "gatekit/README.md"),
 ]),

 ("Saying what a tool will not do", "The sentence a product page usually "
  "leaves out.", [

  ("keyj play installs a system-wide keyboard listener, which is the same "
   "machinery a keylogger uses.",
   "keyj-cli README", GH + "keyj-cli/README.md", None, "keyj-cli/README.md"),

  ("What it cannot catch is a tab that is internally consistent and simply "
   "wrong; bad frets convert cleanly into bad notes, and only your ear will "
   "find that.",
   "keyj-cli README", GH + "keyj-cli/README.md", None, "keyj-cli/README.md"),

  ("A block with the wrong number of strings produces no notes and says how "
   "many it found, rather than silently guessing a tuning.",
   "keyj-js README", GH + "keyj-js/README.md", None, "keyj-js/README.md"),

  ("A tab in a tuning that does not exist comes back with .error set and no "
   "notes, rather than raising.",
   "keyj-js README", GH + "keyj-js/README.md", None, "keyj-js/README.md"),
 ]),

 ("Measurement", "Findings that turn on a quantity, and what the quantity "
  "is allowed to support.", [

  ("Across 9,169 machine-generated Lean proofs, 92.7% depend on choice, but "
   "86.1% of them are fixed by what the theorems say, and only 6.5% are "
   "avoidable.",
   "gonzalgo", "/gonzalgo/", None, "gonzalgo/index.html"),

  ("Asking which constant a theorem's classical dependence is responsible "
   "to is not the same as asking which constants its proof touches, and the "
   "answers are far apart.",
   "The Dominator Table", "/gonzalgo/dominator-table/",
   "10.5281/zenodo.21900625", "gonzalgo/dominator-table/index.html"),

  ("The common cases are not choice in the mathematician's sense at all "
   "— they are a proof style and a missing instance.",
   "The Module Spend Table", "/gonzalgo/module-spend/", None,
   "gonzalgo/module-spend/index.html"),

  ("Across 532,579 Lean theorems in nine libraries and 71,124 Metamath "
   "theorems in five databases, none rest on an unfinished proof and none "
   "rest on the compiler",
   "gonzalgo", "/gonzalgo/", None, "gonzalgo/index.html"),

  ("The result is a boundary rather than a gradient. norm_num introduces "
   "the axiom of choice on all 15 order goals",
   "The Controlled Tactic Table", "/gonzalgo/controlled-tactics/", None,
   "gonzalgo/controlled-tactics/index.html"),

  ("Classical.propDecidable has 6,775 spenders in its subtree and "
   "Classical.byContradiction 1,854.",
   "The Spend-Point Table", "/gonzalgo/spend-points/", None,
   "gonzalgo/spend-points/index.html"),
 ]),

 ("Stating a limit", "What a result is not allowed to be used for, written "
  "down beside it.", [

  ("Under R5 there is no score, so there is no ranking, so a profile cannot "
   "be used as a league table without leaving the specification.",
   "Kernel Trust Profile", "/gonzalgo/kernel-trust/", None,
   "gonzalgo/kernel-trust/index.html"),

  ("A library reaching 61% of its theorems with the axiom of choice has "
   "made a design decision, not an error.",
   "Kernel Trust Profile", "/gonzalgo/kernel-trust/", None,
   "gonzalgo/kernel-trust/index.html"),

  ("Metamath's set.mm tiers countable and dependent choice separately on "
   "purpose and reaches 1.2%; Lean core does not, and its maintainers have "
   "stated that avoiding choice is a deliberate non-goal.",
   "Kernel Trust Profile", "/gonzalgo/kernel-trust/", None,
   "gonzalgo/kernel-trust/index.html"),

  ("The method therefore constitutes a screening stimulus generator, not a "
   "measurement instrument, and cannot classify deficiency type or grade "
   "severity.",
   "A Procedural Method for Generating Pseudoisochromatic Plates",
   "/papers/procedural-method-generating-pseudoisochromatic-plates-browser/",
   "10.5281/zenodo.21310577",
   "papers/procedural-method-generating-pseudoisochromatic-plates-browser/index.html"),

  ("The method's ceiling is not its design but the display.",
   "A Procedural Method for Generating Pseudoisochromatic Plates",
   "/papers/procedural-method-generating-pseudoisochromatic-plates-browser/",
   "10.5281/zenodo.21310577",
   "papers/procedural-method-generating-pseudoisochromatic-plates-browser/index.html"),

  ("The 58x figure above is one measured pair; computing reach for every "
   "row means a second traversal of the full graph and it has not been run.",
   "The Dominator Table", "/gonzalgo/dominator-table/",
   "10.5281/zenodo.21900625", "gonzalgo/dominator-table/index.html"),

  ("The hidden digit plate returns 27% for protan and 5% for deutan, the "
   "inverted arrangement appearing directly in the measurement.",
   "Pseudoisochromatic plate design type is recoverable from delivered "
   "color and dot geometry alone",
   "/papers/pseudoisochromatic-plate-design-type-recoverable-from/",
   "10.5281/zenodo.21876790",
   "papers/pseudoisochromatic-plate-design-type-recoverable-from/index.html"),

  ("The certifying configurations are given by exact rational coordinates, "
   "and the certifier is validated by negative controls against Fejes "
   "Toth's proven value r_3 = 3/5.",
   "Certified upper bounds for Fejes Toth's point-goalie problem",
   "/papers/certified-upper-bounds-fejes-t-th/", "10.5281/zenodo.21729548",
   "papers/certified-upper-bounds-fejes-t-th/index.html"),
 ]),

 ("Method", "Decisions about how a thing was measured, and why they change "
  "the answer.", [

  ("Compile failures are held out of every figure here; a corpus targeting "
   "Lean 4.27 measured under 4.32 would otherwise report version drift",
   "What machine-generated Lean proofs rest on",
   "/gonzalgo/generated-proofs/", None,
   "gonzalgo/generated-proofs/index.html"),

  ("Run against the top of the dominance ranking it returns 8 of 114 "
   "occurrences, in 3 declarations.",
   "The Substitution Ledger", "/gonzalgo/substitution-ledger/", None,
   "gonzalgo/substitution-ledger/index.html"),
 ]),

 ("Argument", "Positions taken in the papers, stated without the "
  "scaffolding around them.", [

  ("The content remains admissible as evidence of the artifact's own "
   "existence and provenance — the distinction is between what the "
   "content depicts and what the content is.",
   "AI-Generated Evidence Admissibility",
   "/papers/ai-generated-evidence-admissibility-formal-classification/",
   "10.5281/zenodo.19642437",
   "papers/ai-generated-evidence-admissibility-formal-classification/index.html"),

  ("Every classification system presupposes an observer.",
   "The Epistemology of Observation",
   "/papers/epistemology-observation-formal-certification-framework-human/",
   "10.5281/zenodo.19726226",
   "papers/epistemology-observation-formal-certification-framework-human/index.html"),

  ("A clause-by-clause analysis of Article 50 identifies five structural "
   "gaps that DAG-OR closes without displacing the regulation.",
   "The Classification Deficit",
   "/papers/classification-deficit-article-50-eu-ai/",
   "10.5281/zenodo.19578570",
   "papers/classification-deficit-article-50-eu-ai/index.html"),
 ]),
]


# ------------------------------------------------------------ verification
def flatten(path):
    raw = io.open(os.path.join(ROOT, path), encoding="utf-8",
                  errors="replace").read()
    if path.endswith((".html", ".htm")):
        raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
        raw = re.sub(r"(?s)<!--.*?-->", " ", raw)
        raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    # the sources render some of these with typographic punctuation, and
    # accents survive a round trip through PDF differently than through
    # HTML, so compare on letters, digits and spacing only
    raw = (raw.replace("’", "'").replace("‘", "'")
              .replace("“", '"').replace("”", '"')
              .replace("—", " ").replace("–", "-")
              .replace("ó", "o").replace("é", "e")
              .replace("τ", "tau").replace(" ", " "))
    # markdown code ticks are markup, exactly as HTML tags are, and
    # stripping a tag leaves a space in front of the punctuation that
    # followed it ("lt_or_eq_of_le ;"). Neither is a quoting discrepancy.
    raw = raw.replace("`", "")
    return squeeze(raw)


def squeeze(t):
    """Undo the spacing that stripping inline markup leaves behind."""
    t = t.replace("`", "")
    t = re.sub(r"\s+([;:,.)])", r"\1", t)
    t = re.sub(r"([(])\s+", r"\1", t)
    return " ".join(t.split())


def check():
    bad = []
    for _, _, items in SECTIONS:
        for quote, label, _, _, src in items:
            want = squeeze(quote.replace("—", " "))
            if want not in flatten(src):
                bad.append((label, src, want[:70]))
    if bad:
        print("  buildwriting REFUSED: %d quote(s) are not in the source "
              "they name\n" % len(bad))
        for label, src, want in bad:
            print("    %-34s %s" % (label[:34], src))
            print("      %s..." % want)
        print("\n  Nothing was written. Fix the quote or the source.")
        sys.exit(1)


# ------------------------------------------------------------------ render
def render():
    e = B.esc
    o = ['<p class="lede">%s</p>' % e(LEDE)]
    n = 0
    for title, blurb, items in SECTIONS:
        o.append("<h2>%s</h2>" % e(title))
        o.append('<p class="note">%s</p>' % e(blurb))
        for quote, label, href, doi, _ in items:
            n += 1
            cite = '<a href="%s">%s</a>' % (e(href), e(label))
            if doi:
                cite += ' &middot; <a href="%s%s">DOI %s</a>' % (
                    DOI, e(doi), e(doi))
            o.append('<figure class="ex"><blockquote><p>%s</p></blockquote>'
                     '<figcaption>%s</figcaption></figure>'
                     % (e(quote), cite))
    o.append('<h2>Everything else</h2>')
    o.append('<p>The full list of deposited work is at '
             '<a href="/papers/">/papers/</a>, the measurements at '
             '<a href="/gonzalgo/">/gonzalgo/</a>, and the products at '
             '<a href="/portfolio.html">/portfolio</a>. '
             'CVs: <a href="/cv/">/cv/</a>.</p>')
    return "\n".join(o), n


def main():
    check()
    body, n = render()
    doc = B.shell(
        "Selected Writing — F-Keys",
        "F-Keys\\Research\\Selected Writing",
        body,
        "%d excerpt(s)" % n,
        active_cat="research",
        description="Excerpts from deposited papers, measurement write-ups "
                    "and software documentation, each one linked to the "
                    "source it was taken from.",
        canonical="https://f-keys.com/writing/")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(doc)
    print("  buildwriting: /writing/ with %d excerpt(s), every one verified "
          "against its source" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
