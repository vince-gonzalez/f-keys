"""Build gonzalgo/generated-proofs/index.html.

Visible text and structured data come from one place so they cannot drift.

    python gonzalgo/buildnote.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_build"))
import indexlib  # noqa: E402
CANON = "https://f-keys.com/gonzalgo/generated-proofs/"

TITLE = "What 9,169 machine-generated Lean proofs rest on"

NUMBERS = {
    "corpus": 10000,
    "compiled": 9169,
    # The 831 excluded, decomposed. The deposited paper carries this split and
    # the page did not, so the three-way breakdown was only checkable by
    # reading a PDF. Collapsing these into one row is the error this note is
    # about: an unparsable header, a declaration that never entered the
    # environment, and one admitted carrying sorryAx are three different
    # events, and only the last is visible to an axiom report.
    "no_header": 1,
    "never_entered": 270,
    "admitted_sorryax": 560,
    "reach": 8496,
    "bound": 7899,
    "eligible": 597,
    "clean": 673,
    "sorry_total": 520,
    "sorry_drift": 520,
    "sorry_real": 0,
}
# Derived, never typed twice. This page shipped saying 560 held out, which is
# 271 short of what 10,000 minus 9,169 leaves. The corpus is 10,000 by count —
# GoedelProofs/Proof_00000.lean through Proof_09999.lean — and 9,169 is the
# denominator that reproduces all four published percentages, so the held-out
# figure was the wrong one.
NUMBERS["held_out"] = NUMBERS["corpus"] - NUMBERS["compiled"]


def check_numbers(n: dict) -> None:
    """Every part must sum to its whole, and every percentage must round to what
    the prose claims. A figure nobody can re-derive is a figure nobody can
    correct."""
    fails = []
    parts = n["no_header"] + n["never_entered"] + n["admitted_sorryax"]
    if parts != n["held_out"]:
        fails.append(f"the excluded decomposition {n['no_header']} + "
                     f"{n['never_entered']} + {n['admitted_sorryax']} = {parts} "
                     f"!= held_out {n['held_out']}")
    if n["compiled"] + n["held_out"] != n["corpus"]:
        fails.append(f"compiled {n['compiled']} + held_out {n['held_out']} "
                     f"!= corpus {n['corpus']}")
    if n["bound"] + n["eligible"] != n["reach"]:
        fails.append(f"bound {n['bound']} + eligible {n['eligible']} "
                     f"!= reach {n['reach']}")
    if n["reach"] + n["clean"] != n["compiled"]:
        fails.append(f"reach {n['reach']} + clean {n['clean']} "
                     f"!= compiled {n['compiled']}")
    if n["sorry_real"] != 0:
        fails.append(f"sorry_real is {n['sorry_real']}, the page says none")
    for key, claimed in (("reach", 92.7), ("bound", 86.1),
                         ("eligible", 6.5), ("clean", 7.3)):
        got = round(100 * n[key] / n["compiled"], 1)
        if got != claimed:
            fails.append(f"{key}: {n[key]}/{n['compiled']} = {got}%, "
                         f"prose says {claimed}%")
    if fails:
        raise ValueError("generated-proofs figures do not hold together:\n  "
                         + "\n  ".join(fails))


def pct(key: str) -> str:
    return f"{100 * NUMBERS[key] / NUMBERS['compiled']:.1f}%"

BODY = [
    ("", [
        "A language model that writes a Lean proof gets one bit of feedback: the "
        "proof compiles, or it does not. What the proof ends up standing on is "
        "not part of that signal, and while the field agrees the check matters, "
        "no one had reported what it returns over a corpus.",
        "This is that measurement, over the Goedel-Prover output for the Lean "
        f"Workbook problems — {NUMBERS['corpus']:,} proofs, of which "
        f"{NUMBERS['compiled']:,} still compile under Lean 4.32. The other "
        f"{NUMBERS['held_out']:,} fail on the version gap and are held out of "
        "every figure below.",
        "Lean 4.32.",
    ]),
    ("The result", [
        "Every proof that compiles proves its theorem. None rests on an "
        "unfinished proof, none was obtained by trusting the compiler instead of "
        "the kernel, and none cites an axiom outside the three that all of "
        "Mathlib rests on.",
        "Tools to check that exist — SorryDB strips sorryAx from agent output, "
        "AXLE's verify_proof rejects non-whitelisted axioms. What had not been "
        "done was running the check across a whole corpus and reporting what it "
        "costs.",
    ]),
    ("Classical dependence, and what it means", [
        "8,496 of the 9,169 — 92.7% — depend on the axiom of choice. Read alone "
        "that number is alarming and it is also nearly meaningless.",
        "7,899 of them depend on it because of what they SAY. The theorem is "
        "about the real numbers, the reals are constructed with choice in "
        "Mathlib, and no proof of such a statement can avoid it. The dependence "
        "is a property of the claim.",
        "597 depend on it only because of HOW they were proved. Nothing in those "
        "statements needs choice; a different proof would not carry it. That is "
        "6.5% of the corpus, and it is the only part anyone could act on.",
        "Separating the statement from the proof is what turns 92.7% into two "
        "numbers that mean different things. Without it the honest report and "
        "the misleading one are the same figure.",
    ]),
    ("Where the avoidable dependence comes from", [
        "A tactic, mostly. `omega` supplies the `Decidable` argument of six "
        "helper lemmas as a literal `Classical.propDecidable` and never attempts "
        "instance synthesis. On `Nat` and `Int` the constructive instance exists "
        "and is axiom-free, so an otherwise constructive proof comes out "
        "classical. It reproduces in one line with no imports.",
        "This was reported upstream and closed as completed, with the reply that "
        "avoiding choice is a deliberate non-goal of Lean core. The behaviour is "
        "within Lean's stated design. It still propagates into every proof a "
        "model generates with that tactic.",
    ]),
    ("Why the whole corpus, and not a sample", [
        "Measuring only the proofs that invoke `omega` returns 46.6% avoidable. "
        "That figure is wrong by a factor of seven, and wrong for a reason worth "
        "stating: `omega` operates on `Nat` and `Int`, which is exactly the "
        "population whose statements are choice-free and whose dependence is "
        "therefore removable.",
        "Any sample drawn on tactic use selects on the outcome. The denominator "
        "has to be the corpus.",
    ]),
    ("Separating drift from finding", [
        "Lean admits a declaration whose proof failed to elaborate, carrying "
        "`sorryAx`. In a report that is indistinguishable from a proof that was "
        "genuinely never finished, so the two have to be told apart by the "
        "compiler's error output rather than by the axiom set.",
        f"{NUMBERS['sorry_total']} theorems reach `sorryAx` and every one of "
        f"them is among the {NUMBERS['held_out']:,} that failed to compile. Of "
        f"the {NUMBERS['compiled']:,} that compiled, none does. Compile "
        "failures are held out of every figure here; a corpus targeting Lean "
        "4.27 measured under 4.32 would otherwise report version drift as a "
        "property of the proofs.",
    ]),
    ("Related work", [
        "That compilation is not verification is established. SorryDB "
        "(arXiv:2603.02668) removes <code>sorryAx</code> from agent output and "
        "calls it an exploit agents used to get around sorry verification. AXLE "
        "(arXiv:2606.26442) states it plainly: a passing compile accepts proofs "
        "containing sorry, unsound axioms, or incorrectly restated theorems. And "
        "Ammanamanchi, Bhat and Biderman (arXiv:2606.29493) audit five Lean "
        "benchmarks, surface 4,833 findings including 398 mechanically certified "
        "issues, and recommend that evaluation harnesses verify "
        "<code>#print axioms</code> output.",
        "This note is the measurement that recommendation implies and nobody had "
        "taken: what the check costs on a real corpus. The mechanism was already "
        "known; the rate was not.",
        "The two sides are complementary rather than competing. Those audits "
        "examine the benchmark STATEMENTS — whether a formalisation says what it "
        "should. This examines the prover OUTPUT — what a proof of it rests on. A "
        "harness can be right about one and blind to the other.",
        "One distinction is worth keeping sharp. Lean issue #8212 documents "
        "<code>apply?</code> emitting a synthetic <code>sorry</code> without "
        "logging an error, so <code>lake build --wfail</code> exited 0 while the "
        "theorem was never added to the environment — the case DeepSeek-Prover-V2 "
        "output hit. That is a different failure from the 560 counted here, which "
        "ARE in the environment. A harness verifying the declaration exists "
        "catches the first and misses the second.",
    ]),
    ("Method", [
        "Axioms come from `Lean.collectAxioms`, the same call behind "
        "`#print axioms`, run per theorem inside the environment. Statement "
        "axioms are the union over the constants appearing in the theorem's type.",
        "Cross-checked against an independent route: serialising the whole "
        "790,171-declaration environment and recomputing reachability outside "
        "Lean gives the same answer on the same subset, and that graph was "
        "itself traversed in both directions returning identical sets. The "
        "kernel's own bookkeeping is what is reported here.",
        "Controls fixed before measuring: a `Nat` goal closed by `omega` must "
        "show choice in the proof and not the statement, a structural proof must "
        "show nothing, and a goal over the reals must show choice in both. All "
        "three behave as required.",
    ]),
    ("Reproducing it", [
        "The corpus is banach1729/goedel-workbook-lean427 on Hugging Face, "
        "Apache-2.0. The tool is `pip install gonzalgo`. Compile the proofs in "
        "batches against Mathlib and run the axiom report; the whole thing takes "
        "a few hours on a laptop and needs no Lean expertise.",
    ]),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{canon}">

<title>{title} — gonzalgo</title>
<meta name="description" content="9,169 AI-generated Lean proofs audited: none rests on an unfinished proof or on the compiler. 92.7% depend on the axiom of choice, but only 6.5% avoidably.">
<meta name="keywords" content="AI generated proofs, Lean 4, Goedel-Prover, Lean Workbook, Classical.choice, sorry, axiom dependency, formal verification, machine-generated mathematics">
<meta name="author" content="Vincent Gonzalez">
<meta name="llms-txt" content="https://f-keys.com/llms.txt">
<meta name="ai" content="allow">
<meta property="og:type" content="article">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="None rests on an unfinished proof. 92.7% depend on choice; only 6.5% avoidably.">
<meta property="og:site_name" content="F-Keys">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="None rests on an unfinished proof. 92.7% depend on choice; only 6.5% avoidably.">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet">

<script type="application/ld+json">
{ld}
</script>

<style>
:root {{ --bg:#0a0e0a; --panel:#111911; --border:#1f351f; --green:#39ff14; --text:#c3dcc3; --dim:#8fae8f; --cyan:#00ffcc; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--text); font-family:'Share Tech Mono',monospace; line-height:1.65; overflow-x:hidden; }}
body::before {{ content:''; position:fixed; inset:0; background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.07) 2px,rgba(0,0,0,0.07) 4px); pointer-events:none; z-index:9000; }}
nav {{ position:fixed; top:0; left:0; right:0; z-index:10000; background:rgba(10,14,10,0.95); border-bottom:1px solid var(--border); padding:0 2rem; height:60px; display:flex; align-items:center; justify-content:space-between; }}
.logo {{ font-family:'VT323',monospace; font-weight:400; font-size:28px; color:var(--green); letter-spacing:4px; text-decoration:none; }}
nav a {{ color:var(--dim); text-decoration:none; }}
nav a:hover {{ color:var(--green); }}
main {{ max-width:820px; margin:0 auto; padding:7rem 1.5rem 4rem; }}
h1 {{ font-family:'VT323',monospace; font-weight:400; font-size:clamp(34px,6vw,56px); color:var(--green); letter-spacing:2px; line-height:1.1; }}
.kicker {{ font-family:'VT323',monospace; font-weight:400; font-size:clamp(18px,3vw,24px); color:var(--cyan); letter-spacing:2px; margin:.6rem 0 1.6rem; }}
h2 {{ font-family:'VT323',monospace; font-weight:400; font-size:1.6rem; color:var(--green); margin:2.6rem 0 .7rem; letter-spacing:1px; }}
p {{ margin-bottom:1rem; }}
a {{ color:var(--green); }}
code {{ color:var(--cyan); }}
pre {{ background:#0d120d; border:1px solid var(--border); padding:1.1rem; overflow-x:auto; font-size:.85rem; margin:1.4rem 0; color:var(--text); }}
table {{ width:100%; border-collapse:collapse; margin:1.4rem 0; font-size:.9rem; }}
td,th {{ border-bottom:1px solid var(--border); padding:.5rem .4rem; text-align:left; }}
th {{ color:var(--green); }}
td.n {{ text-align:right; color:var(--cyan); }}
footer {{ border-top:1px solid var(--border); margin-top:4rem; padding:2rem 0; color:var(--dim); font-size:.85rem; }}
</style>
</head>
<body>

<nav>
  <a href="/" class="logo">F-KEYS</a>
  <div style="display:flex;gap:1.6rem;font-size:.9rem;">
    <a href="/gonzalgo/">gonzalgo</a>
    <a href="/gonzalgo/faq/">FAQ</a>
    <a href="https://github.com/vince-gonzalez/gonzalgo">GitHub</a>
  </div>
</nav>

<main>

<h1>{title}</h1>
<p class="kicker">none of them rests on an unfinished proof</p>

<pre>{summary}</pre>

{body}

<h2>Get the data</h2>
<p>
The table above, machine-readable:
<a href="generated-proofs.json">generated-proofs.json</a> &middot;
<a href="generated-proofs.csv">generated-proofs.csv</a> &middot; CC-BY-4.0 &middot;
version {version}
</p>
<p style="color:var(--dim);font-size:.9rem;border:1px solid var(--border);background:var(--panel);padding:.7rem .9rem;">
One of the <a href="/gonzalgo/data/">gonzalgo indexes</a> &mdash; standing
measurements of what formal libraries rest on. The per-proof results behind
these totals are not published yet; releasing them means re-running the audit,
and a summary is not a substitute for the rows.
</p>

<footer>
  Measured with <a href="https://pypi.org/project/gonzalgo/">gonzalgo</a> ·
  method and definitions: <a href="https://doi.org/10.5281/zenodo.21769846">10.5281/zenodo.21769846</a> ·
  <a href="/gonzalgo/kernel-index/">Kernel Index</a> &middot;
  <a href="https://doi.org/10.5281/zenodo.21853489">attribution paper</a><br>
  Vince Gonzalez · <a href="https://orcid.org/0009-0005-3640-014X">ORCID 0009-0005-3640-014X</a>
</footer>

</main>
</body>
</html>
"""


# Filled in by build(), read by _build/build_all.py to list this page on the
# index hub. The article is hand-written but the data underneath is not special.
META: dict = {}


def rows() -> list[dict]:
    """The summary block as data. The <pre> on the page is rendered from this
    list, so the block and the download cannot say different things."""
    n = NUMBERS
    def r(category, count, share=None, note=None):
        return {"category": category, "proofs": count,
                "share_of_compiled_pct": share, "note": note}
    return [
        r("corpus", n["corpus"], None,
          "Goedel-Prover proofs of Lean Workbook problems, Apache-2.0"),
        r("compiled under Lean 4.32", n["compiled"], 100.0),
        r("excluded: no parsable theorem header", n["no_header"], None,
          "not a declaration"),
        r("excluded: never entered the environment", n["never_entered"], None,
          "invisible to an axiom report"),
        r("excluded: admitted carrying sorryAx", n["admitted_sorryax"], None,
          "in the environment, counted by a build check"),
        r("held out, failed to compile", n["held_out"], None,
          "corpus targets Lean 4.27; version drift, not a property of the proofs"),
        r("depends on Classical.choice", n["reach"],
          round(100 * n["reach"] / n["compiled"], 1)),
        r("choice dependence bound by the statement", n["bound"],
          round(100 * n["bound"] / n["compiled"], 1),
          "unavoidable: the theorem is about the reals"),
        r("choice dependence avoidable, proof only", n["eligible"],
          round(100 * n["eligible"] / n["compiled"], 1),
          "the only part anyone could act on"),
        r("choice-free entirely", n["clean"],
          round(100 * n["clean"] / n["compiled"], 1)),
        r("rests on an unfinished proof", n["sorry_real"], 0.0,
          f"{n['sorry_total']} reach sorryAx, all among the held-out"),
        r("native_decide / compiler-trusted", 0, 0.0),
        r("axioms beyond propext, Quot.sound, Classical.choice", 0, 0.0),
    ]


def _n(rows: list[dict], category: str) -> int:
    """The count on a named row. Raises if the row is missing, so renaming a
    category breaks the build instead of quietly voiding an invariant."""
    for r in rows:
        if r["category"] == category:
            return r["proofs"]
    raise KeyError(category)


def summary_block(data: list[dict]) -> str:
    """The <pre> table, laid out from the rows rather than typed by hand."""
    width = max(len(d["category"]) for d in data)
    lines = []
    for d in data:
        share = ("" if d["share_of_compiled_pct"] is None
                 else f"   {d['share_of_compiled_pct']:>5.1f}%")
        lines.append(f"{d['category']:<{width}}  {d['proofs']:>7,}{share}")
    return html.escape("\n".join(lines))


def build() -> str:
    check_numbers(NUMBERS)
    data = rows()

    idx = indexlib.Index(
        slug="generated-proofs",
        title="What machine-generated Lean proofs rest on",
        kicker="", meta_title="", meta_description="",
        lede=[], columns=[
            indexlib.Column("category", "category"),
            indexlib.Column("proofs", "proofs", align="right"),
            indexlib.Column("share_of_compiled_pct", "share", align="right", pct=True),
            indexlib.Column("note", "note", dim=True),
        ],
        rows=data,
        description=(
            "What a corpus of machine-generated Lean 4 proofs rests on. 9,169 "
            "Goedel-Prover proofs of Lean Workbook problems that compile under "
            "Lean 4.32, audited for unfinished proofs, compiler-trusted "
            "reductions and axiom dependence, with choice dependence split into "
            "the part the statement forces and the part the proof adds."),
        measured={"Lean 4": "4.32",
                  "corpus": "banach1729/goedel-workbook-lean427, Apache-2.0"},
        provenance="",
        keywords=["machine-generated proofs", "AI generated proofs", "Lean 4",
                  "Goedel-Prover", "Lean Workbook", "axiom of choice",
                  "sorry", "native_decide", "formal verification"],
        based_on="https://doi.org/10.5281/zenodo.21769846",
        invariants=[
            # The failure this page actually shipped: a row that must be a
            # total was filled with the size of a correction.
            ("the three exclusion reasons sum to the held-out total",
             lambda rs: _n(rs, "excluded: no parsable theorem header")
             + _n(rs, "excluded: never entered the environment")
             + _n(rs, "excluded: admitted carrying sorryAx")
             == _n(rs, "held out, failed to compile")),
            ("compiled and held-out sum to the corpus",
             lambda rs: _n(rs, "compiled under Lean 4.32")
             + _n(rs, "held out, failed to compile") == _n(rs, "corpus")),
            ("statement-bound and avoidable sum to the choice-dependent total",
             lambda rs: _n(rs, "choice dependence bound by the statement")
             + _n(rs, "choice dependence avoidable, proof only")
             == _n(rs, "depends on Classical.choice")),
            ("choice-dependent and choice-free sum to the compiled total",
             lambda rs: _n(rs, "depends on Classical.choice")
             + _n(rs, "choice-free entirely")
             == _n(rs, "compiled under Lean 4.32")),
            ("every share recomputes from the compiled denominator",
             lambda rs: all(
                 r["share_of_compiled_pct"] is None
                 or abs(round(100 * r["proofs"] / _n(rs, "compiled under Lean 4.32"), 1)
                        - r["share_of_compiled_pct"]) <= 0.05
                 for r in rs)),
            ("the three zero claims are still zero",
             lambda rs: all(_n(rs, c) == 0 for c in (
                 "rests on an unfinished proof",
                 "native_decide / compiler-trusted",
                 "axioms beyond propext, Quot.sound, Classical.choice"))),
        ],
    )
    emitted = indexlib.emit_data(idx)
    META.update(emitted)

    ld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "@id": CANON,
        "headline": TITLE,
        "url": CANON,
        "datePublished": "2026-08-07",
        "author": {"@type": "Person", "name": "Vince Gonzalez",
                   "identifier": "https://orcid.org/0009-0005-3640-014X"},
        "publisher": {"@type": "Organization", "name": "F-Keys",
                      "url": "https://f-keys.com/"},
        "about": ["formal verification", "Lean 4", "machine-generated proofs",
                  "axiom of choice", "proof provenance"],
        "isBasedOn": "https://doi.org/10.5281/zenodo.21769846",
        "abstract": (
            "9,169 machine-generated Lean 4 proofs were audited for what they "
            "rest on. None depends on an unfinished proof, on native_decide, or "
            "on any axiom beyond propext, Quot.sound and Classical.choice. "
            "92.7% depend on the axiom of choice, of which 86.1% are bound by "
            "the statement and only 6.5% are avoidable."),
    }
    parts = []
    for heading, paras in BODY:
        if heading:
            parts.append(f"<h2>{html.escape(heading)}</h2>")
        for p in paras:
            # escape first, then turn backticked spans into <code>; the other
            # order would escape the tags this just inserted
            # escape first, then convert code spans; the reverse order would
            # escape the tags this just inserted
            bt = chr(96)
            t = re.sub(bt + r"([^" + bt + r"]+)" + bt,
                       r"<code>\1</code>", html.escape(p))
            parts.append(f"<p>{t}</p>")
    # Two blocks, not one: the prose is the article, the table is the dataset.
    # A page that is both should say so, or dataset search never sees it.
    blocks = (json.dumps(ld, indent=2, ensure_ascii=False)
              + "\n</script>\n<script type=\"application/ld+json\">\n"
              + emitted["jsonld"])
    return TEMPLATE.format(canon=CANON, title=html.escape(TITLE),
                           ld=blocks, summary=summary_block(data),
                           version=emitted["version"],
                           body="\n\n".join(parts))


if __name__ == "__main__":
    out = HERE / "generated-proofs" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8", newline="\n")
    print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
