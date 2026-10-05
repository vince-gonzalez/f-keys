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
 ("Measurement", "Findings that turn on a quantity, and what the quantity "
  "is allowed to support.", [

  ("Asking which constant a theorem's classical dependence is responsible to "
   "is not the same as asking which constants its proof touches, and the "
   "answers are far apart. 116,766 theorems reach the order lemma "
   "lt_or_eq_of_le; 2,018 would stop being classical if it were rebuilt.",
   "The Dominator Table", "/gonzalgo/dominator-table/",
   "10.5281/zenodo.21900625", "gonzalgo/dominator-table/index.html"),

  ("It does not say how far each use travels, and the two are wildly "
   "different: 324,808 theorems depend on choice while 18,109 declarations "
   "spend it.",
   "The Module Spend Table", "/gonzalgo/module-spend/", None,
   "gonzalgo/module-spend/index.html"),

  ("For Mathlib that is 13.1% of theorems, against a figure of 55% that "
   "circulates without a measurement behind it.",
   "gonzalgo", "/gonzalgo/", None, "gonzalgo/index.html"),

  ("The result is a boundary rather than a gradient. norm_num introduces the "
   "axiom of choice on all 15 order goals (≤, <, ≥ over Nat and "
   "Int) and on none of the 12 equality and divisibility goals.",
   "The Controlled Tactic Table", "/gonzalgo/controlled-tactics/", None,
   "gonzalgo/controlled-tactics/index.html"),

  ("15 of these 20 sites contain no direct use of a choice primitive "
   "anywhere in their subtree.",
   "The Spend-Point Table", "/gonzalgo/spend-points/", None,
   "gonzalgo/spend-points/index.html"),
 ]),

 ("Stating a limit", "What the work does not establish, written down where "
  "the result is.", [

  ("It does not assert that tau(20) = 19448 or tau(21) = 29768; both remain "
   "open, and other constructions are not excluded.",
   "The added-vector code of the odd-sign construction is maximal",
   "/papers/added-vector-code-odd-sign-construction/",
   "10.5281/zenodo.21702301",
   "papers/added-vector-code-odd-sign-construction/index.html"),

  ("For n = 6 an unstructured search converged back to Fejes Toth's own "
   "configuration and produced no improvement; that is reported as a "
   "negative result, not as evidence of optimality.",
   "Certified upper bounds for Fejes Toth's point-goalie problem",
   "/papers/certified-upper-bounds-fejes-t-th/",
   "10.5281/zenodo.21729548",
   "papers/certified-upper-bounds-fejes-t-th/index.html"),

  ("The method therefore constitutes a screening stimulus generator, not a "
   "measurement instrument, and cannot classify deficiency type or grade "
   "severity.",
   "A Procedural Method for Generating Pseudoisochromatic Plates",
   "/papers/procedural-method-generating-pseudoisochromatic-plates-browser/",
   "10.5281/zenodo.21310577",
   "papers/procedural-method-generating-pseudoisochromatic-plates-browser/"
   "index.html"),

  ("Unsupervised recovery of the figure/ground assignment itself was also "
   "attempted and fails: recall reaches 100% on ten plates while precision "
   "falls to 38 to 63% on the vanishing plates, with no confidence signal "
   "distinguishing successes from failures.",
   "Pseudoisochromatic plate design type is recoverable from delivered "
   "color and dot geometry alone",
   "/papers/pseudoisochromatic-plate-design-type-recoverable-from/",
   "10.5281/zenodo.21876790",
   "papers/pseudoisochromatic-plate-design-type-recoverable-from/index.html"),

  ("A library reaching 61% of its theorems with the axiom of choice has made "
   "a design decision, not an error.",
   "Kernel Trust Profile", "/gonzalgo/kernel-trust/", None,
   "gonzalgo/kernel-trust/index.html"),
 ]),

 ("Method", "Why a number is trustworthy, or why an earlier one is not.", [

  ("Compile failures are held out of every figure here; a corpus targeting "
   "Lean 4.27 measured under 4.32 would otherwise report version drift as a "
   "property of the proofs.",
   "What machine-generated Lean proofs rest on",
   "/gonzalgo/generated-proofs/", None,
   "gonzalgo/generated-proofs/index.html"),

  ("A previous run over the same question returned 404 synthesis timeouts "
   "against this run's 12, and had no not-a-goal category at all, so nearly "
   "every site it could not clean was recorded as a time limit being hit.",
   "The Site Diagnosis Table", "/gonzalgo/site-diagnosis/", None,
   "gonzalgo/site-diagnosis/index.html"),

  ("Of 114 occurrences only 21 were testable at all. The rest occur under "
   "binders, where the proposition is not closed and cannot be handed to "
   "instance synthesis from outside its declaration.",
   "The Substitution Ledger", "/gonzalgo/substitution-ledger/", None,
   "gonzalgo/substitution-ledger/index.html"),
 ]),

 ("Argument", "Openings and load-bearing claims from the written papers.", [

  ("This document does not explain Modulign.",
   "The Formal Logic of Modulign", "/papers/formal-logic-modulign/",
   "10.5281/zenodo.19350848", "papers/formal-logic-modulign/index.html"),

  ("Every classification system presupposes an observer.",
   "The Epistemology of Observation",
   "/papers/epistemology-observation-formal-certification-framework-human/",
   "10.5281/zenodo.19726226",
   "papers/epistemology-observation-formal-certification-framework-human/"
   "index.html"),

  ("The evidentiary problem of AI-generated content is not a disclosure "
   "problem.",
   "The Classification Deficit",
   "/papers/classification-deficit-article-50-eu-ai/",
   "10.5281/zenodo.19578570",
   "papers/classification-deficit-article-50-eu-ai/index.html"),

  ("not because any rule prohibits its admission, but because its address "
   "structure formally encodes the absence of the causal chain that "
   "observational authentication requires",
   "AI-Generated Evidence Admissibility",
   "/papers/ai-generated-evidence-admissibility-formal-classification/",
   "10.5281/zenodo.19642437",
   "papers/ai-generated-evidence-admissibility-formal-classification/"
   "index.html"),
 ]),

 ("Documentation", "Software documentation, including the parts a reader is "
  "entitled to be warned about.", [

  ("keyj play installs a system-wide keyboard listener, which is the same "
   "machinery a keylogger uses.",
   "keyj-cli README", GH + "keyj-cli/README.md", None,
   "keyj-cli/README.md"),

  ("If node is not installed the parity checks skip and say so, because a "
   "check that cannot run must not report success.",
   "keyj-cli README", GH + "keyj-cli/README.md", None,
   "keyj-cli/README.md"),

  ("A tab in a tuning that does not exist comes back with .error set and "
   "no notes, rather than raising.",
   "keyj-js README", GH + "keyj-js/README.md", None, "keyj-js/README.md"),

  ("so the package and the page cannot answer differently",
   "keyj-js README", GH + "keyj-js/README.md", None, "keyj-js/README.md"),

  ("Dark grey on navy measured 2.64:1 where body text needs 4.5, and a "
   "person found that, not a build.",
   "gatekit README", GH + "gatekit/README.md", None, "gatekit/README.md"),

  ("Three gates for defects a linter does not have an opinion about, because "
   "none of them is a syntax error.",
   "gatekit README", GH + "gatekit/README.md", None, "gatekit/README.md"),

  ("Both halves matter: a gate that cannot tell those apart gets switched "
   "off.",
   "gatekit README", GH + "gatekit/README.md", None, "gatekit/README.md"),
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
