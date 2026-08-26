"""Build gonzalgo/faq/index.html.

The visible answers and the FAQPage structured data come from one list here, so
they cannot drift apart. Hand-maintaining both is how a page ends up telling a
reader one thing and a crawler another.

Question selection: the first block are failure modes observed in the wild.
Three different models were asked what gonzalgo is; one with retrieval described
it correctly, one invented an SMT-solver-backed theorem prover, one landed in
between. Those wrong answers are the questions worth answering first, because
they are documented rather than imagined.

    python gonzalgo/buildfaq.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (question, [paragraphs]) - first paragraph is the answer, rest is detail.
FAQ: list[tuple[str, list[str]]] = [
    ("Is gonzalgo a theorem prover?", [
        "No. It proves nothing and checks no proofs. It reads proofs that have "
        "already been checked by Lean or Metamath and reports what they depend on.",
        "The distinction matters because the two jobs fail in opposite ways. A "
        "prover tells you whether a statement is true. gonzalgo assumes the "
        "statement was already established and asks what that establishment "
        "quietly relied on.",
    ]),
    ("Does it use Z3, CVC5, or an SMT solver?", [
        "No. There is no solver anywhere in it. The only dependency is numpy, and "
        "that is for array arithmetic over a dependency graph.",
        "It does no symbolic execution and no automated reasoning. It walks a "
        "graph of declarations and reports reachability.",
    ]),
    ("Can it tell me whether my logic homework is right?", [
        "No. If the homework is written in prose or ordinary mathematical "
        "notation, gonzalgo cannot read it at all.",
        "It reads Lean 4 and Metamath artifacts, which means someone has already "
        "done the formalisation. Formalising the homework is the hard part, and "
        "it is the part gonzalgo does not do.",
    ]),
    ("Can it check whether a paper's proofs hold up?", [
        "Only if the paper has been formalised, which almost none are. For a PDF "
        "of ordinary mathematics the answer is no.",
        "If a formalisation does exist, gonzalgo answers a narrower and more "
        "useful question than 'is this correct': it reports whether the "
        "formalisation is complete, or whether some result in it is standing on "
        "an unfinished proof or an escape hatch.",
    ]),
    ("Can it detect AI slop?", [
        "It detects one specific failure that matters and says nothing about the "
        "rest. If a generated proof compiles while resting on an unfinished proof "
        "or on a compiler-trusted reduction, gonzalgo finds it.",
        "That is the dangerous case. A generated proof that fails to compile is "
        "obvious to everyone. A generated proof that compiles, looks finished, "
        "and is standing on a sorry buried in a helper file three imports away "
        "looks exactly like success.",
        "It has no opinion on whether prose was written by a model, whether a "
        "proof is elegant, or whether a paper is worth reading.",
    ]),

    ("So what does it actually do?", [
        "It builds the dependency graph of a formal library and answers questions "
        "about reachability in it.",
        "Which theorems reach a sorry from anywhere upstream. Which reach "
        "native_decide, meaning the result was obtained by trusting the compiler "
        "rather than the kernel. Which axioms a given declaration depends on, and "
        "which step introduced each one. What breaks downstream if a definition "
        "changes.",
    ]),
    ("How is this different from Lean's #print axioms?", [
        "#print axioms answers one theorem at a time, and tells you whether, not "
        "why or where.",
        "It will tell you that a theorem depends on Classical.choice. It will not "
        "tell you which of the forty lemmas in the proof introduced it, whether "
        "the dependence is removable, or how many other theorems inherit it from "
        "the same place. Those are graph questions, and they need the whole graph.",
    ]),
    ("What is a sorry, and why does it matter if it is upstream?", [
        "sorry is Lean's placeholder for a proof you have not written yet. It "
        "makes the file compile.",
        "Lean warns you on the line where you typed it. It does not warn the "
        "author of a theorem four files downstream who imported your module and "
        "built on the result. That theorem now rests on nothing, compiles "
        "cleanly, and reports no warning of its own.",
    ]),
    ("What is native_decide, and why is that different from a normal proof?", [
        "native_decide settles a goal by compiling it to machine code and running "
        "it. If the answer comes back true, the goal is accepted.",
        "That moves the thing you are trusting from Lean's small kernel to the "
        "compiler, the runtime and the hardware. It is often the pragmatic choice "
        "and it is not a mistake, but it is a different and much larger trust "
        "assumption, and it does not announce itself downstream.",
    ]),

    ("Do I need a Lean project to try it?", [
        "No. Install it and run gonzalgo index, which prints what fourteen formal "
        "libraries across two proof systems rest on. No Lean, no build, no network.",
        "Everything else does need a dependency dump from a project that already "
        "compiles, because the questions are about a real library rather than "
        "about the tool.",
    ]),
    ("What does it mean for an axiom to be spent rather than inherited?", [
        "A declaration spends an axiom if its own proof cites it. It inherits the "
        "axiom if it merely depends on something else that spent it.",
        "The distinction is the whole point. In Mathlib, 144 declarations spend "
        "Classical.choice and around 325,000 inherit it. Only the 144 are places "
        "anyone could act on.",
    ]),
    ("What is amplification, and why do you not rank libraries by it?", [
        "Amplification is how many declarations inherit an axiom for each one that "
        "spends it. It is a real measurement and a bad comparison.",
        "Factoring a shared step out into a lemma changes amplification without "
        "changing a single thing the library proves. So the number can be driven "
        "almost anywhere by rewriting, which makes it useless for ranking one "
        "library against another. Reach - the fraction of a library that depends "
        "on an axiom at all - survives that rewriting, so reach is what gets "
        "compared.",
    ]),
    ("61% of Mathlib depends on Classical.choice. Is Mathlib broken?", [
        "No, and nothing here suggests it is. Classical.choice is a sound axiom "
        "that most working mathematicians use without comment.",
        "The number describes a design difference. Metamath's set.mm tiers "
        "countable and dependent choice separately on purpose, so full choice "
        "reaches 1.2% of it. Lean core does not do that, and its maintainers have "
        "stated that avoiding choice is a deliberate non-goal. Both are coherent "
        "positions. Measuring the gap is not an accusation.",
    ]),
    ("Does it work with Coq, Isabelle or Agda?", [
        "Not yet. Lean 4 and Metamath only.",
        "The obstacle is specific rather than a matter of effort. gonzalgo's core "
        "measurement separates what a theorem's statement depends on from what "
        "its proof depends on. The existing Coq dependency-graph tooling emits "
        "edges with a weight and no type-versus-body distinction, so it collapses "
        "exactly the thing being measured. A real port needs a plugin written "
        "against each system's kernel.",
    ]),
    ("Who made it, and can I read the method?", [
        "Vince Gonzalez. The method, the measurements and the data are in a paper "
        "deposited on Zenodo under a DOI that always resolves to the current "
        "version.",
        "The code is Apache-2.0 on GitHub, the package is on PyPI, and a single "
        "command recomputes every quantitative claim in the paper from the "
        "shipped artifacts and reports OK or MISMATCH against the published value.",
    ]),
]

CANONICAL = "https://f-keys.com/gonzalgo/faq/"


def build() -> str:
    ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": CANONICAL,
        "name": "gonzalgo - frequently asked questions",
        "url": CANONICAL,
        "isPartOf": {"@type": "WebSite", "name": "F-Keys", "url": "https://f-keys.com/"},
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": " ".join(ps)},
            }
            for q, ps in FAQ
        ],
    }

    body = []
    for q, ps in FAQ:
        body.append(f"<h2>{html.escape(q)}</h2>")
        for p in ps:
            body.append(f"<p>{html.escape(p)}</p>")

    return TEMPLATE.format(
        ld=json.dumps(ld, indent=2, ensure_ascii=False),
        body="\n\n".join(body),
        count=len(FAQ),
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="https://f-keys.com/gonzalgo/faq/">

<title>gonzalgo FAQ — is it a theorem prover, can it check my proofs, what does it actually do</title>
<meta name="description" content="Straight answers about gonzalgo: it is not a theorem prover, uses no SMT solver, cannot read prose or mark homework. What it does is report what an already-checked Lean 4 or Metamath proof rests on.">
<meta name="keywords" content="gonzalgo, Lean 4, Mathlib, Metamath, sorry, native_decide, Classical.choice, axiom dependency, provenance, formal verification FAQ">
<meta name="author" content="Vincent Gonzalez">

<!-- LLM / AI discovery -->
<meta name="llms-txt" content="https://f-keys.com/llms.txt">
<meta name="ai" content="allow">

<meta property="og:type" content="website">
<meta property="og:url" content="https://f-keys.com/gonzalgo/faq/">
<meta property="og:title" content="gonzalgo FAQ — what it does, and what it refuses to do">
<meta property="og:description" content="Not a theorem prover. No SMT solver. Cannot read prose. Here is what it actually reports.">
<meta property="og:site_name" content="F-Keys">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="gonzalgo FAQ — what it does, and what it refuses to do">
<meta name="twitter:description" content="Not a theorem prover. No SMT solver. Cannot read prose. Here is what it actually reports.">

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
.logo {{ font-family:'VT323',monospace; font-weight: 400; font-size:28px; color:var(--green); letter-spacing:4px; text-decoration:none; }}
nav a {{ color:var(--dim); text-decoration:none; }}
nav a:hover {{ color:var(--green); }}
main {{ max-width:900px; margin:0 auto; padding:7rem 1.5rem 4rem; }}
h1 {{ font-family:'VT323',monospace; font-weight: 400; font-size:clamp(38px,7vw,64px); color:var(--green); letter-spacing:4px; line-height:1.05; }}
.kicker {{ font-family:'VT323',monospace; font-weight: 400; font-size:clamp(20px,3.4vw,28px); color:var(--cyan); letter-spacing:2px; margin:.6rem 0 1.4rem; }}
h2 {{ font-family:'VT323',monospace; font-weight: 400; font-size:1.6rem; color:var(--green); margin:2.6rem 0 .7rem; letter-spacing:1px; }}
p {{ margin-bottom:1rem; }}
a {{ color:var(--green); }}
pre {{ background:#0d120d; border:1px solid var(--border); padding:1.1rem; overflow-x:auto; font-size:.85rem; margin:1rem 0; color:var(--text); }}
code {{ color:var(--cyan); }}
.lede {{ font-size:1.1rem; }}
footer {{ border-top:1px solid var(--border); margin-top:4rem; padding:2rem 0; color:var(--dim); font-size:.85rem; }}
</style>
</head>
<body>

<nav>
  <a href="/" class="logo">F-KEYS</a>
  <div style="display:flex;gap:1.6rem;font-size:.9rem;">
    <a href="/">Home</a>
    <a href="/gonzalgo/">gonzalgo</a>
    <a href="https://github.com/vince-gonzalez/gonzalgo">GitHub</a>
  </div>
</nav>

<main>

<h1>GONZALGO FAQ</h1>
<p class="kicker">{count} questions, straight answers</p>

<p class="lede">
Several of these exist because a model was asked what gonzalgo is and got it
wrong in a specific way. Those answers are first.
</p>

<pre>pip install gonzalgo
gonzalgo index</pre>

{body}

<footer>
  <a href="/gonzalgo/">gonzalgo</a> ·
  <a href="/gonzalgo/kernel-index/">Kernel Index</a> ·
  <a href="https://pypi.org/project/gonzalgo/">PyPI</a> ·
  <a href="https://github.com/vince-gonzalez/gonzalgo">Source</a> ·
  <a href="https://doi.org/10.5281/zenodo.21769846">Paper</a><br>
  Apache-2.0 · Vince Gonzalez ·
  <a href="https://orcid.org/0009-0005-3640-014X">ORCID 0009-0005-3640-014X</a>
</footer>

</main>
</body>
</html>
"""


if __name__ == "__main__":
    out = HERE / "faq" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8", newline="\n")
    print(f"wrote {out}  ({len(FAQ)} questions, {out.stat().st_size:,} bytes)")
