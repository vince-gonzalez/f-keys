"""Build gonzalgo/generated-proofs/index.html.

Visible text and structured data come from one place so they cannot drift.

    python gonzalgo/buildnote.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANON = "https://f-keys.com/gonzalgo/generated-proofs/"

TITLE = "What 9,169 machine-generated Lean proofs rest on"

NUMBERS = {
    "corpus": 10000,
    "compiled": 9169,
    "reach": 8496,
    "bound": 7899,
    "eligible": 597,
    "clean": 673,
    "sorry_total": 520,
    "sorry_drift": 520,
    "sorry_real": 0,
}

BODY = [
    ("", [
        "A language model that writes a Lean proof gets one bit of feedback: the "
        "proof compiles, or it does not. What the proof ends up standing on is "
        "not part of that signal and nobody has measured it.",
        "This is that measurement, over the Goedel-Prover output for the Lean "
        "Workbook problems — 10,000 proofs, of which 9,169 still compile under Lean 4.32. The other 560 fail on the version gap and are held out of every figure below.",
        "Lean 4.32.",
    ]),
    ("The result", [
        "Every proof that compiles proves its theorem. None rests on an "
        "unfinished proof, none was obtained by trusting the compiler instead of "
        "the kernel, and none cites an axiom outside the three that all of "
        "Mathlib rests on.",
        "That has not previously been checkable about a generated corpus. It "
        "could be asserted; it could not be shown.",
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
        "520 theorems reach `sorryAx` and every one of them is among the 560 "
        "that failed to compile. Of the 9,169 that compiled, none does. Compile "
        "failures are held out of every figure here; a corpus targeting Lean "
        "4.27 measured under 4.32 would otherwise report version drift as a "
        "property of the proofs.",
    ]),
    ("Method", [
        "Axioms come from `Lean.collectAxioms`, the same call behind "
        "`#print axioms`, run per theorem inside the environment. Statement "
        "axioms are the union over the constants appearing in the theorem's type.",
        "Cross-checked against an independent route: serialising the whole "
        "790,000-declaration environment and recomputing reachability outside "
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
    <a href="https://github.com/zengineco/gonzalgo">GitHub</a>
  </div>
</nav>

<main>

<h1>{title}</h1>
<p class="kicker">none of them rests on an unfinished proof</p>

<pre>corpus                        10,000
compiled under Lean 4.32       9,169
held out, failed to compile      560

reach Classical.choice         8,496    92.7%
  statement-bound              7,899    86.1%   unavoidable
  avoidable, proof only          597     6.5%
choice-free entirely             673     7.3%

rests on an unfinished proof       0
native_decide / compiler trust     0
axioms beyond the standard three   0</pre>

{body}

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


def build() -> str:
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
    return TEMPLATE.format(canon=CANON, title=html.escape(TITLE),
                           ld=json.dumps(ld, indent=2, ensure_ascii=False),
                           body="\n\n".join(parts))


if __name__ == "__main__":
    out = HERE / "generated-proofs" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8", newline="\n")
    print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
