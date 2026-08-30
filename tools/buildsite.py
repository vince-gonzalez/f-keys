#!/usr/bin/env python3
"""
============================================================
buildsite — generates every page of f-keys.com
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Thirteen hand-written pages each carried their own copy of
the chrome, so they drifted into different websites. The
catalogue below is the single source of truth; the shell is
written once; every page is generated. Two pages cannot
disagree about the navigation because there is only one
navigation.

WORKFLOW STACK
  1. CATALOGUE  — every product, its category, status, blurb
  2. PAGES      — the long-form detail for each product
  3. shell()    — Explorer window: tree left, content right
  4. main()     — writes index.html, a page per category, and
                  a page per product

Run:  python tools/buildsite.py
============================================================
"""

import html
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── status vocabulary ────────────────────────────────────────
READY = ("Ready", "st-ready")
DISCORD = ("In Discord", "st-plat")
FORTNITE = ("In Fortnite", "st-plat")
SETUP = ("Needs setup", "st-setup")
ALPHA = ("Alpha", "st-setup")
PIP = ("pip install", "st-ready")
PUBLISHED = ("Published", "st-ready")
LIVE = ("Live", "st-ready")

# ── the catalogue ────────────────────────────────────────────
# (slug, name, category, type, status, one-line, href)
CATALOGUE = [
    ("keyj", "Key-J", "apps", "Application", READY,
     "Every keystroke plays a note, in any application. Live staff, WAV export.", "/keyj/"),
    ("pixelstaff", "Pixel Staff", "apps", "Application", READY,
     "An 8-bit composer. Piano roll, waveform per channel, WAV or ringtone out.", "/pixelstaff/"),
    ("opticquiz", "OpticQuiz", "apps", "Web app", READY,
     "Colour-vision and acuity tests that run entirely in the browser.", "https://opticquiz.com"),
    ("qv", "QV", "apps", "Web app", READY,
     "Live ballots. Put a question to a room and watch the count move.", "/qv/"),
    ("remapwrap", "RemapWrap", "apps", "Application", ALPHA,
     "Any smartphone becomes a programmable macro pad. No app, no dongle.", "/remapwrap/"),

    ("trailer-load", "Trailer Load", "games", "Simulator", READY,
     "Warehouse load training that plays like a game. Institutional licensing.", "https://trailer-load.com"),
    ("prompt", "PROMPT", "games", "Discord activity", DISCORD,
     "A multiplayer word game inside Discord, in a 90s CRT shell.", "https://prompt.f-keys.com"),
    ("daisupop", "DaisuPop", "games", "Discord activity", DISCORD,
     "A dice popper. Everyone in the room sees the same roll at the same moment.", "https://dp.f-keys.com"),
    ("micdrop", "MICDROP", "games", "Fortnite island", FORTNITE,
     "A live open-mic arena. 120 seconds to win the crowd. Code 1534-0440-5810.", "/micdrop/"),
    ("fytecraft", "FyteCraft", "games", "Game", ALPHA,
     "An RTS built around combat rather than base-building. Early, and openly so.", "https://github.com/vince-gonzalez/fytecraft.com"),

    ("wikipolish", "WikiPolish", "tools", "Web tool", READY,
     "Grammar scout for Wikipedia. Finds a first edit nobody will revert.", "/wikipolish/"),
    ("leadseer", "LeadSeer", "tools", "Desktop tool", SETUP,
     "Finds the local businesses that still have no website.", "/leadseer/"),
    ("plumhud", "PlumHUD", "tools", "Python package", PIP,
     "Miner fleet monitor. Overlay HUD, alerts, and local history.", "/plumhud/"),

    # Shipped 2026-08-26. Listed the same day, because the failure this
    # site keeps repeating is not building things - it is building them
    # and leaving them where nobody can find them.
    # 2026-08-29. SayDo is the flagship and it is honestly an alpha: the
    # declarations are drafts and the receipts are unsigned, which the
    # page says in the same size type as everything else.
    ("saydo", "SayDo", "tools", "Standard + harness", ALPHA,
     "Prove a tool behaves as it says. A signed contract, a conformance harness, a receipt anyone can check.", "/saydo/"),
    ("axsent", "axsent", "research", "Python package", PIP,
     "What a formal library assumes, measured from source: Rocq, Agda and Isabelle, with nothing built.", "/axsent/"),
    ("authorecon", "authorecon", "research", "Python package", PIP,
     "Reconcile published work against every place it lives, for any ORCID, from public sources.", "/authorecon/"),

    ("legible", "legible", "tools", "Python package", PIP,
     "Three build gates: unreadable type, unreadable colour, a retired name.", "/legible/"),
    ("openapi-drift", "openapi-drift", "tools", "Python package", PIP,
     "Has your API drifted from its spec, and can a machine still read it?", "/openapi-drift/"),
    ("changewatch", "changewatch", "tools", "Python package", PIP,
     "A doorbell for your published work. Silent until somebody else acts.", "/changewatch/"),
    ("keyjockey", "keyjockey", "tools", "npm package", PIP,
     "Guitar tablature to notes: eight tunings, capo offsets, MIDI and frequency.", "/keyjockey/"),

    ("streamsniper", "Stream Sniper", "hardware", "Appliance", SETUP,
     "A spare mini PC shows a channel fullscreen the moment it goes live.", "/streamsniper/"),
    ("moonbeam", "Moonbeam", "hardware", "Python package", PIP,
     "Finds the NerdMiners on your network and reads their vitals.", "/moonbeam/"),

    ("gonzalgo", "gonzalgo", "research", "Research tool", PUBLISHED,
     "Which axioms a Lean 4 or Metamath theorem spends rather than inherits.", "/gonzalgo/"),
    ("papers", "Papers", "research", "Publications", PUBLISHED,
     "Where formal libraries spend their axioms. Full text, DOIs, archives.", "/papers/"),
    ("modulign", "Modulign", "research", "Standard", PUBLISHED,
     "A dimensional address grammar for observable reality. DAG-OR v3.", "https://modulign.org"),

    ("5best2buy", "5Best2Buy", "properties", "Website", LIVE,
     "A sourcing map for independent American food.", "https://www.5best2buy.com"),
    ("poticas", "Poticas", "properties", "Website", LIVE,
     "The home of potica. History, method, and who still ships one.", "https://poticas.com"),
    ("tipstreams", "TipStreams", "properties", "Website", LIVE,
     "Branded tip pages and OBS overlays. The widget never touches money.", "https://tipstreams.com"),
    ("fundoge", "FunDoge", "properties", "Website", LIVE,
     "Free isometric mini-golf in the browser.", "https://dogefundme.com"),
]

CATEGORIES = [
    ("apps", "Apps", "Things you sit in front of and use."),
    ("games", "Games", "Things you play."),
    ("tools", "Tools", "Things that do the work for you."),
    ("hardware", "Hardware", "Software that makes a box do one thing forever."),
    ("research", "Research", "Things you read. Every claim carries a DOI."),
    ("properties", "Properties", "Sites that stand on their own."),
]



# ── long-form detail, one entry per product ──────────────────
PAGES = {
"saydo": dict(
  title="SayDo", tagline="Prove a tool behaves as it says.",
  facts=[("Status", "Working proof of concept \u2014 name provisional"),
         ("Declarations", "5 F-Keys servers, 4 third-party \u2014 all draft"),
         ("Receipts", "Unsigned"),
         ("Invariant types", "10 in the current draft"),
         ("Licence", "Apache-2.0 on the open layers"),
         ("Source", "vince-gonzalez/saydo")],
  body="""
<h2>The gap</h2>
<p>Signing and provenance prove a tool&rsquo;s code is what the publisher
released. They do not prove the tool behaves as its description promises.
Tool poisoning, capability rug-pulls and silent behavioral drift are one
problem wearing three names: the distance between what a tool declares and
what it does.</p>
<p>The provenance standards say so themselves. <b>TBOM</b> states it cannot
verify that tool behavior matches descriptions. <b>CTMS</b> states it verifies
that a tool&rsquo;s claims have not changed, not that they are true. That
out-of-scope line is what this is for.</p>
<p>SayDo does not replace either. It extends them: a declaration binds to the
same tool-definition digests a Tool Bill of Materials already records, and
attaches to one without changing its schema.</p>

<h2>Four layers</h2>
<table class="facts">
<tr><th>Declaration</th><td>A signed, machine-readable contract per tool: the
behavior it is permitted to show &mdash; no network, writes only here,
deterministic, returns errors as values. Ten invariant types in the current
draft.</td></tr>
<tr><th>Conformance</th><td>A harness exercises the tool under observation
&mdash; valid calls, adversarial input, egress and filesystem monitoring
&mdash; and reports pass, fail or <b>not-covered</b> per invariant. It cannot
prove an invariant it did not exercise, and it says so rather than passing
it.</td></tr>
<tr><th>Receipt</th><td>Every run emits a hash-chained record, one row per
verdict, chained by <code>row_hash = sha256(prev + row)</code>. Edit one row
and the chain breaks at it. An auditor re-verifies it in a browser &mdash; no
account, no request to us.</td></tr>
<tr><th>Trust mark</th><td>A &ldquo;Warranted&rdquo; badge served from the
registry, linking to the full findings rather than a bare grade, with expiry
and revocation. <b>Not built yet.</b></td></tr>
</table>

<h2>Run it</h2>
<p>Install one of the covered servers, then put it under SayDo. The command
captures the tool definitions, exercises the server, and writes a receipt.</p>
<pre><b>saydo verify certivl</b>
  certivl   CONFORMANT
  tally     {'pass': 9}
  receipt   receipts/certivl.receipt.jsonl
  head      353e94cd497115aa49e10ab76874ab7bd9645fed&hellip;</pre>
<p>A harness that only ever passes is worth nothing, so it ships with a server
built to fail. <code>saydo selfcheck</code> runs that one and requires the
harness to catch every violation &mdash; the same discipline the rest of this
catalogue is built on, pointed at itself.</p>

<h2>A receipt, actually</h2><p>This is the receipt for <code>saydo verify certivl</code>, from the repository. Thirteen rows: the declaration it was checked against, the captured tool definitions, what the monitor could and could not see, one row per invariant, and a close. Each row carries the hash of the row before it.</p><div class="receipt"><table><thead><tr><th>#</th><th>row</th><th></th><th>prev_hash</th><th>row_hash</th></tr></thead><tbody><tr><td class="sq">1</td><td class="ty">open</td><td class="ex">pkg:pypi/certivl@0.2.0</td><td class="hx">31b446b87a387b3d…</td><td class="hx">2911aee89d746f02…</td></tr><tr><td class="sq">2</td><td class="ty">capture</td><td class="ex"></td><td class="hx">2911aee89d746f02…</td><td class="hx">8bbcbdebf275fae5…</td></tr><tr><td class="sq">3</td><td class="ty">monitor</td><td class="ex"></td><td class="hx">8bbcbdebf275fae5…</td><td class="hx">8db9473951715e22…</td></tr><tr><td class="sq">4</td><td class="ty">verdict</td><td class="ex">refusal.scope</td><td class="hx">8db9473951715e22…</td><td class="hx">a192845eb5d858e8…</td></tr><tr><td class="sq">5</td><td class="ty">verdict</td><td class="ex">network.none</td><td class="hx">a192845eb5d858e8…</td><td class="hx">94ff9d07b07e1140…</td></tr><tr><td class="sq">6</td><td class="ty">verdict</td><td class="ex">writes.none</td><td class="hx">94ff9d07b07e1140…</td><td class="hx">2792b46310d90e1e…</td></tr><tr><td class="sq">7</td><td class="ty">verdict</td><td class="ex">reads.none</td><td class="hx">2792b46310d90e1e…</td><td class="hx">6953d604c4a27794…</td></tr><tr><td class="sq">8</td><td class="ty">verdict</td><td class="ex">subprocess.none</td><td class="hx">6953d604c4a27794…</td><td class="hx">fe0193b67cfeab17…</td></tr><tr><td class="sq">9</td><td class="ty">verdict</td><td class="ex">answers.deterministic</td><td class="hx">fe0193b67cfeab17…</td><td class="hx">e83fd3722b937d43…</td></tr><tr><td class="sq">10</td><td class="ty">verdict</td><td class="ex">errors.are-values</td><td class="hx">e83fd3722b937d43…</td><td class="hx">8d7fb1429449889e…</td></tr><tr><td class="sq">11</td><td class="ty">verdict</td><td class="ex">undecided.on-overlap</td><td class="hx">8d7fb1429449889e…</td><td class="hx">27850d284c2f007b…</td></tr><tr><td class="sq">12</td><td class="ty">verdict</td><td class="ex">decimal.read-exactly</td><td class="hx">27850d284c2f007b…</td><td class="hx">6f174eaa56827918…</td></tr><tr><td class="sq">13</td><td class="ty">close</td><td class="ex">tally {'pass': 9}</td><td class="hx">6f174eaa56827918…</td><td class="hx">754a675f79ea0f92…</td></tr></tbody></table></div><p class="sub">Every <code>prev_hash</code> above equals the <code>row_hash</code> on the line before it &mdash; checked, not asserted. Change any row and every hash below it stops matching, which is the whole mechanism. Paste it into <code>verifier/index.html</code> and it checks offline, with no account and no request to anybody.</p><h2>What the monitor admits it cannot see</h2><p>Row 3 is not a result. It is the harness recording its own blind spots &mdash; that it observes filesystem opens and socket connects at the host process, and does <b>not</b> observe activity below the Python runtime, such as a native extension. An invariant it did not exercise is reported <code>not-covered</code> rather than passed.</p><h2>What it is not, yet</h2>
<p>This is a working proof of concept and the name is provisional. Every
declaration currently carries <code>status: "draft"</code>. Every receipt is
unsigned. Nothing here is a claim of conformance about anybody&rsquo;s
software, including ours, and the trust mark does not exist.</p>
<p>Those sentences are on this page in the same size type as the rest, because
a tool whose entire purpose is the distance between what software claims and
what it does would be a poor place to start overstating.</p>

<h2>Prior art it builds on</h2>
<p>TBOM v1.0.2, Jason M. Lovell, 2026 &mdash;
<a href="https://doi.org/10.5281/zenodo.18459260" rel="noopener">10.5281/zenodo.18459260</a>.
CTMS 1.0, George Kanellopoulos, 2026 &mdash;
<a href="https://github.com/gkanellopoulos/ctms" rel="noopener">gkanellopoulos/ctms</a>.
Both are provenance; both state that verifying behavior against the metadata
is out of their scope.</p>
<div class="btnrow">
  <a class="btn default" href="https://github.com/vince-gonzalez/saydo" rel="noopener">The repository</a>
  <a class="btn" href="/papers/">Related work</a>
</div>"""),

 "axsent": dict(
  title="axsent", tagline="What a formal library assumes, measured from source.",
  facts=[("Install", "pip install axsent"),
         ("Reads", "Rocq, Agda, Isabelle"),
         ("Builds", "Nothing"),
         ("Source", "vince-gonzalez/axsent")],
  body="""
<h2>What it does</h2>
<p>Measures what a formal library actually assumes &mdash; its axioms, and the
interface assumptions that get counted alongside them &mdash; across Rocq,
Agda and Isabelle, read from source with nothing compiled.</p>
<pre><b>pip install axsent</b>
axsent &lt;path-to-library&gt;</pre>
<h2>Why nothing is built</h2>
<p>A census that requires building the library can only measure libraries that
still build. That silently excludes the old, the abandoned and the ones
pinned to a compiler nobody has &mdash; which is a biased sample of exactly the
wrong kind, because those are the ones whose assumptions nobody has looked at
lately.</p>
<h2>The finding behind it</h2>
<p>Every census of this kind conflates two different things: assumptions that
are <em>mathematical</em>, and assumptions that are about the
<em>interface</em> to the outside world. They are counted together and
reported as one number. Separating them is most of what this tool is for, and
the measurements are written up in the papers.</p>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/axsent/" rel="noopener">PyPI</a>
  <a class="btn" href="https://github.com/vince-gonzalez/axsent" rel="noopener">Source</a>
  <a class="btn" href="/papers/">The papers</a>
</div>"""),

 "authorecon": dict(
  title="authorecon", tagline="Every place your published work ended up.",
  facts=[("Install", "pip install authorecon"),
         ("Takes", "Any ORCID"),
         ("Sources", "Public ones only"),
         ("Also", "Gates that run before work leaves your hands"),
         ("Source", "vince-gonzalez/apriori")],
  body="""
<h2>What it does</h2>
<p>Reconciles a body of published work against every place it lives &mdash; for
any ORCID, from public sources. A deposit exists in more places than the person
who made it can hold in their head: the DOI, the index, the profile, the
repository, the aggregator that copied it, and the one that copied it wrong.</p>
<pre><b>pip install authorecon</b>
authorecon 0009-0005-3640-014X</pre>
<h2>The half people skip</h2>
<p>It also carries the gates that run <em>before</em> research output leaves
your hands. Reconciling after publication tells you where the mistake went; a
gate before it tells you not to make it. Both halves are the same tool because
they are the same question asked at two different times.</p>
<h2>What it will not do</h2>
<p>It reads public sources only, and it does not treat a citation count as a
signal &mdash; a count reflects how long a corpus has been indexed at least as
much as it reflects anything about the work.</p>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/authorecon/" rel="noopener">PyPI</a>
  <a class="btn" href="https://github.com/vince-gonzalez/apriori" rel="noopener">Source</a>
</div>"""),

"legible": dict(
  title="legible", tagline="Three gates a linter will not give you.",
  facts=[("Install","pip install legible"),("Licence","MIT"),
         ("Commands","typefloor, contrast-gate, deadname-gate"),
         ("Actions","typefloor, contrast-gate, deadname-gate, cvd-palette"),
         ("Source","vince-gonzalez/f-keys")],
  body="""
<h2>What it does</h2>
<p>Three build gates for defects a linter has no opinion about, because none of
them is a syntax error. Each one exists because a person read something and
could not.</p>
<pre><b>pip install legible</b>
typefloor ./src                  type below a readable floor
contrast-gate ./src              colour that cannot be read on its surface
deadname-gate ./src              a name that should be gone</pre>
<h2>The rename gate is the unusual one</h2>
<p>It fails a build when a retired name reaches a title, a footer, a byline,
alt text or a comment &mdash; while leaving machine identifiers alone, because
renaming a repository path or a published artifact breaks working links or
contradicts a deposited record. Both halves matter. A gate that cannot tell
those apart gets switched off within a week.</p>
<p>Written for a company rename. It is the same shape as the problem of a
person changing their name and finding it in three hundred places, which is the
harder version and the one worth getting right.</p>
<h2>It will not tell you it passed when it did not</h2>
<p>All three once reported <code>OK</code> on a directory they had never
opened, because a bare path argument was ignored and each scanned itself
instead. <code>deadname-gate</code> exits <b>2</b> rather than <b>0</b> when
nothing is configured, and <code>contrast-gate --require-pairs</code> fails
rather than passing a stylesheet that declares no colours at all.</p>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/legible/" rel="noopener">PyPI</a>
  <a class="btn" href="https://github.com/vince-gonzalez/typefloor" rel="noopener">typefloor action</a>
  <a class="btn" href="https://github.com/vince-gonzalez/cvd-palette" rel="noopener">cvd-palette action</a>
</div>"""),

 "openapi-drift": dict(
  title="openapi-drift", tagline="Does the service still do what the spec says?",
  facts=[("Install","pip install openapi-drift"),("Licence","MIT"),
         ("Action","vince-gonzalez/openapi-drift"),
         ("Source","vince-gonzalez/openapi-drift")],
  body="""
<h2>What it does</h2>
<p>An OpenAPI document is a promise about a service, and nothing keeps the two
together. It quietly becomes a description of what the service used to do, and
every consumer finds out one failed call at a time.</p>
<pre><b>pip install openapi-drift</b>
openapi-drift openapi.json
openapi-drift https://example.com/openapi.json --live</pre>
<h2>The check nobody else runs</h2>
<p>A response schema behind a <code>$ref</code> is correct, valid, and useless
to the tools that turn an operation into a function signature, because they do
not dereference. A validator sees a schema; a converter sees an argument with
no type. The document passes everything and cannot be used.</p>
<p>That is not hypothetical. It cost a week on a specification that passed
every other check.</p>
<h2>What it is not</h2>
<p>Not a fuzzer &mdash; it calls what you documented rather than generating
traffic hunting for crashes. Not a syntax validator &mdash; a perfectly
well-formed document can be unreadable by a machine.</p>
<h2>Only safe calls</h2>
<p><code>--live</code> calls parameterless GETs only. A path with a placeholder
or a required parameter is skipped rather than guessed at, because a guessed
value reports drift that is the checker's fault. Nothing is ever written.</p>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/openapi-drift/" rel="noopener">PyPI</a>
  <a class="btn" href="https://github.com/vince-gonzalez/openapi-drift" rel="noopener">Source</a>
</div>"""),

 "changewatch": dict(
  title="changewatch", tagline="A doorbell, not a dashboard.",
  facts=[("Install","pip install changewatch"),("Licence","MIT"),
         ("Needs","GITHUB_TOKEN for the GitHub half"),
         ("Source","vince-gonzalez/changewatch")],
  body="""
<h2>What it does</h2>
<p>You can already see what you did. What you cannot see is whether anyone else
did anything about it &mdash; the first citation, the first star from a
stranger, the first time your name appears somewhere you did not put it.</p>
<pre><b>pip install changewatch</b>
changewatch init
changewatch check</pre>
<p>Almost every run says nothing happened and exits. That is the design.</p>
<h2>Why it only reports other people</h2>
<p>The first ORCID this was pointed at reported six citations. All six were the
author citing himself, doubled because Zenodo mints a DOI per version. Six is a
number that feels like an audience; the real figure was zero.</p>
<p>A tool that cannot tell your own activity from a stranger's rings on your own
deposits, gets muted inside a week, and is then silent on the day something real
happens. So every source checks your ORCID, your names and your logins.</p>
<h2>It does not trust the search engine</h2>
<p>Asked for the exact phrase <code>"openapi-drift"</code>, Hacker News returned
a five-month-old thread titled &ldquo;How do you catch OpenAPI drift before the
UI breaks?&rdquo; &mdash; two words, and not about anybody's package. Every hit
is checked against the text locally, because a search engine's idea of a phrase
is not yours.</p>
<h2>The first run is silent</h2>
<p>It has nothing to compare against, so everything looks new. A doorbell that
announces months of history the moment it is plugged in gets unplugged. The
first run learns; the second one rings.</p>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/changewatch/" rel="noopener">PyPI</a>
  <a class="btn" href="https://github.com/vince-gonzalez/changewatch" rel="noopener">Source</a>
</div>"""),

 "keyjockey": dict(
  title="keyjockey", tagline="Tablature in, notes out.",
  facts=[("Install","npm install keyjockey"),("Licence","MIT"),
         ("Tunings","8, with capo offsets"),
         ("Source","vince-gonzalez/f-keys")],
  body="""
<h2>What it does</h2>
<p>Reads guitar tablature and converts notes. Eight tunings, capo offsets, MIDI
and frequency.</p>
<pre><b>npm install keyjockey</b>
keyjockey.parseTab(tab, "Standard (EADGBe)", 0).notes;
keyjockey.parseTab(tab, "Drop D", 2).notes;      // capo 2
keyjockey.midiToName(60);                        // "C4"
keyjockey.nameToFreq("A4");                      // 440</pre>
<h2>Lifted, not rewritten</h2>
<p>This is the same reader <a href="/keyj/">Key-J</a> runs in the browser, and
the Python half is on PyPI as <code>keyj</code>. The npm package is generated
from <code>app.html</code> at build time rather than written a third time, and
the build fails if the app moves and the package does not.</p>
<p>Key-J has already shipped three defects that existed only because two copies
of one thing drifted. A third copy would have been a third chance.</p>
<h2>Errors come back, they are not thrown</h2>
<p>A tab in a tuning that does not exist returns <code>.error</code> and no
notes. Text that is not tablature returns zero notes rather than guessing at
one.</p>
<div class="btnrow">
  <a class="btn default" href="https://www.npmjs.com/package/keyjockey" rel="noopener">npm</a>
  <a class="btn" href="/keyj/">Key-J</a>
</div>"""),

"opticquiz": dict(
  title="OpticQuiz", tagline="See colour. Check colour. Correct colour.",
  facts=[("Where","opticquiz.com"),("Cost","Free, no account"),
         ("Runs","Entirely in the browser"),
         ("Packages","opticquiz-cvd, opticquiz-eye, opticquiz-cvd-mcp"),
         ("Research","Deposited, with DOIs")],
  body="""
<h2>What it is</h2>
<p>Sixteen vision tests that run in the browser &mdash; acuity charts, colour
vision, contrast &mdash; and a colour-accessibility toolkit for people building
things other people have to look at.</p>
<p>Nothing is uploaded. The tests run on your machine, which is the only
arrangement under which anyone should be typing what they can and cannot see
into a web page.</p>
<h2>Two audiences, one engine</h2>
<p>If you want to check your own eyes, open the site. If you are shipping a
design, the same simulation is installable: <code>npm i opticquiz-cvd</code> or
the PyPI package of the same name, so the check that runs in the browser also
runs in your build.</p>
<p>There is a <a href="https://github.com/vince-gonzalez/cvd-palette" rel="noopener">GitHub Action</a> too &mdash; it
fails a build when two colours in a palette become the same colour under
protanopia, deuteranopia or tritanopia. The default matplotlib red and green
are seventy-one apart to normal vision and five apart under deuteranopia.</p>
<h2>What it is not</h2>
<p>Screening, not diagnosis. These are the same plates and charts an optician
would recognise, rendered honestly, with their calibration limits published
rather than glossed. A screen is not a lightbox and the tests say so.</p>
<div class="btnrow">
  <a class="btn default" href="https://opticquiz.com" rel="noopener">Take a test</a>
  <a class="btn" href="https://www.npmjs.com/package/opticquiz-cvd" rel="noopener">npm</a>
  <a class="btn" href="/papers/">The research</a>
</div>"""),

 "trailer-load": dict(
  title="Trailer Load", tagline="Warehouse load training that plays like a game.",
  facts=[("Where","trailer-load.com"),("Cost","Free to play"),
         ("Licensing","Separately, for institutional training use"),
         ("Runs","In the browser")],
  body="""
<h2>What it is</h2>
<p>A loading simulator where weight distribution, axle limits and stack
integrity are the lesson rather than the scenery. You load a trailer, and the
trailer behaves like a trailer.</p>
<h2>Who it is for</h2>
<p>Anyone who has to teach loading and would rather the first mistake happened
on a screen. The cheapest way to learn what a badly distributed load does is to
crush one nobody paid for.</p>
<h2>Cost</h2>
<p>Free to play. Licensed separately to institutions that want it for training,
because a training department wants an invoice, a contact and something that
will still be there next year &mdash; and that is a different arrangement from
a free browser game.</p>
<div class="btnrow">
  <a class="btn default" href="https://trailer-load.com" rel="noopener">Play it</a>
  <a class="btn" href="/contact.html">Licensing</a>
</div>"""),

 "prompt": dict(
  title="PROMPT", tagline="A multiplayer word game, inside Discord.",
  facts=[("Where","prompt.f-keys.com"),("Runs","As a Discord Activity"),
         ("Install","None. No bot invite."),("Cost","Free")],
  body="""
<h2>What it is</h2>
<p>A word game that runs inside a Discord voice channel, in a 90s CRT shell.
Everyone in the room is looking at the same green screen at the same moment.</p>
<h2>Why it is an Activity</h2>
<p>No install, no bot to invite, no permissions to grant, nothing for a server
admin to approve. You start it from the voice channel and the people already
there are already playing. The friction of getting a group into a game is
usually larger than the game.</p>
<div class="btnrow">
  <a class="btn default" href="https://prompt.f-keys.com" rel="noopener">Open it</a>
</div>"""),

 "daisupop": dict(
  title="DaisuPop", tagline="Everyone sees the same roll at the same moment.",
  facts=[("Where","dp.f-keys.com"),("Runs","As a Discord Activity"),
         ("Install","None"),("Cost","Free")],
  body="""
<h2>What it is</h2>
<p>A dice popper for Discord. One roll, rendered to everyone in the voice
channel simultaneously.</p>
<h2>Why that matters</h2>
<p>Every remote dice game has the same argument in it: somebody rolled
somewhere nobody else could see. A shared roll removes the one excuse, and it
turns out that is most of what a dice tool needs to do.</p>
<div class="btnrow">
  <a class="btn default" href="https://dp.f-keys.com" rel="noopener">Open it</a>
</div>"""),

 "fytecraft": dict(
  title="FyteCraft", tagline="An RTS built around the fight, not the build order.",
  facts=[("Where","github.com/vince-gonzalez/fytecraft.com"),
         ("Status","Alpha, and openly so"),("Cost","Free")],
  body="""
<h2>What it is</h2>
<p>A real-time strategy game where combat is the game rather than the reward
for twenty minutes of economy. Most RTS makes you spend the opening building
something before anything happens; this starts at the part people stayed for.</p>
<h2>It is early</h2>
<p>Alpha, and said so on the front page rather than discovered on launch.
Things are missing, things will change, and the source is public while that is
true. If you want a finished game this is not one yet.</p>
<div class="btnrow">
  <a class="btn default" href="https://github.com/vince-gonzalez/fytecraft.com" rel="noopener">Source</a>
</div>"""),

 "modulign": dict(
  title="Modulign", tagline="A dimensional address grammar for observable reality.",
  facts=[("Where","modulign.org"),("Standard","DAG-OR v3"),
         ("Papers","Deposited, with DOIs"),("Cost","Free to read and use")],
  body="""
<h2>What it is</h2>
<p>A grammar for saying <em>where</em> a claim sits before arguing about whether
it is true. DAG-OR gives an observation an address across explicit dimensions,
so two people disagreeing can find out whether they are disagreeing about the
same thing.</p>
<h2>Why an address</h2>
<p>Most classification arguments are really arguments about which axis somebody
is standing on. Once the axes are named and an observation has coordinates on
each, the disagreement either resolves or becomes a specific one &mdash; and a
specific disagreement is worth having.</p>
<h2>Where the work is</h2>
<p>The standard, the classification decision protocol and the papers are all
deposited with DOIs, so a citation points at a version rather than a website
that may have changed.</p>
<div class="btnrow">
  <a class="btn default" href="https://modulign.org" rel="noopener">The standard</a>
  <a class="btn" href="/papers/">Papers</a>
</div>"""),

 "5best2buy": dict(
  title="5Best2Buy", tagline="A sourcing map for independent American food.",
  facts=[("Where","5best2buy.com"),("Cost","Free"),
         ("What it lists","Independent makers who ship")],
  body="""
<h2>What it is</h2>
<p>A map of small American food makers who will send you what they make.
Bakeries, smokehouses, dairies, single-product outfits that have been doing one
thing for forty years.</p>
<h2>Why it exists</h2>
<p>Most of the good stuff is made by people who never learned search engine
optimisation. They are findable if you already know their name, and invisible
if you do not, which is a bad arrangement for everyone involved. This is the
list you would want if you knew the list existed.</p>
<div class="btnrow">
  <a class="btn default" href="https://www.5best2buy.com" rel="noopener">Browse it</a>
</div>"""),

 "poticas": dict(
  title="Poticas", tagline="The home of potica.",
  facts=[("Where","poticas.com"),("Cost","Free"),
         ("Covers","History, method, and who still ships one")],
  body="""
<h2>What it is</h2>
<p>Potica is a Slovenian rolled nut bread, and this is the reference for it:
where it comes from, how it is actually made, and the short list of people who
still ship one.</p>
<h2>The list is short for a reason</h2>
<p>It is a slow bread with a thin dough and a filling heavy enough to tear it,
so the people who make it well are mostly the people who learned it from
somebody. That is a smaller group every year, and writing down what they do is
most of the point of the site.</p>
<div class="btnrow">
  <a class="btn default" href="https://poticas.com" rel="noopener">Read it</a>
</div>"""),

 "tipstreams": dict(
  title="TipStreams", tagline="Get tipped directly.",
  facts=[("Where","tipstreams.com"),("Cost","Free"),
         ("Package","@f-keys/tip-widget"),
         ("Money","Goes to your wallet, never through ours")],
  body="""
<h2>What it is</h2>
<p>Branded tip pages and OBS overlays for streamers. A multi-payment QR router,
crypto and the usual platforms, pointed at your accounts.</p>
<h2>The only sentence that matters in this category</h2>
<p><b>The widget never touches the money.</b> It routes a viewer to your payment
method and gets out of the way. Nothing is held, nothing is forwarded, there is
no balance, and there is no point at which a decision of ours affects whether
you get paid.</p>
<p>Every other tipping product in this space is a custodian, and a custodian can
freeze you. This one cannot, because it never has anything to freeze.</p>
<h2>In your own page</h2>
<p><code>npm i &#64;f-keys/tip-widget</code> if you would rather embed it than
use the hosted page.</p>
<div class="btnrow">
  <a class="btn default" href="https://tipstreams.com" rel="noopener">Set one up</a>
  <a class="btn" href="https://www.npmjs.com/package/@f-keys/tip-widget" rel="noopener">npm</a>
</div>"""),

 "fundoge": dict(
  title="FunDoge", tagline="The mini-golf game you build yourself.",
  facts=[("Where","dogefundme.com"),("Cost","Free"),
         ("Install","None. It runs in the browser."),
         ("Also","Design holes and share them")],
  body="""
<h2>What it is</h2>
<p>Free isometric mini-golf in the browser. No install, no account, no launcher.
You can design your own holes, share them, and play the ones other people
built.</p>
<h2>The domain</h2>
<p>It is on dogefundme.com, which was bought in a different mood for a different
idea. The game is better than the address and the address is staying, because
moving a live thing to a tidier name is a cost with no benefit to anyone
currently playing it.</p>
<div class="btnrow">
  <a class="btn default" href="https://dogefundme.com" rel="noopener">Play it</a>
</div>"""),

 "keyj": dict(
  title="Key-J", tagline="Every keystroke plays a note, in any application.",
  facts=[("Version","1.6.0"),("Licence","Proprietary"),("Platforms","Browser, Windows, Linux"),
         ("Source","vince-gonzalez/f-keys")],
  body="""
<h2>What it does</h2>
<p>Your keyboard becomes an instrument. Every keystroke plays a note, the notes land
on a staff as you go, and the session exports as a WAV. With global capture on it
hears your keys in any application.</p>
<h2>Tablature import</h2>
<p>Paste guitar tablature, choose a tuning, and Key-J converts the frets to notes.
Sequence mode then plays that run one note per keystroke, so the pitches are handled
and what is left to you is timing and feel.</p>
<p>Eight tunings including drop D, Eb, DADGAD, seven-string and bass, with a capo
offset. Hammer-ons, slides and bends are read as the notes they land on. A block with
the wrong number of strings produces no notes and says how many it found, rather than
guessing a tuning silently.</p>
<h2>The keyboard</h2>
<p>An on-screen keyboard shows which computer key plays which note, printed on the
key it triggers, so a wrong binding is visible rather than something you find by
ear. Keys light as they sound, from a keystroke or from a sequence.</p>
<p>Turn Build on and click keys to enter a run without typing a single note name -
which is the part that made entering a sequence miserable.</p>
<h2>Also</h2>
<p>Seven tone presets from clean guitar to shred. MIDI import. Six play styles, four
waveforms, remappable keys and scale switching.</p>
<h2>On the command line</h2>
<p>Once a song is in, the workbench is in the way. <code>pip install keyj</code> gives you
the same converter and the same player without the window.</p>
<pre><b>pip install keyj</b>
keyj tab solo.txt -o song.txt    tablature in, note names out
keyj render song.txt out.wav     the sequence, at a tempo
keyj show song.txt               what is in a sequence
keyj play song.txt               any keystroke plays the next note</pre>
<p><code>tab</code>, <code>render</code> and <code>show</code> are standard library only and
never touch your keyboard. <code>play</code> is the one part that needs a global hook, so it
is a separate install: <code>pip install "keyj[play]"</code>. It runs in the foreground and
stops when you stop it &mdash; nothing is added to startup.</p>
<p>It never learns which key you pressed. In sequence mode any key advances, so the player
asks whether a key went down and discards everything else. There is no keystroke buffer in
it, which is the difference between an instrument and a keylogger.</p>
<p>The CLI is MIT. The desktop and browser apps are not &mdash; see
<a href="https://github.com/vince-gonzalez/f-keys/blob/main/keyj/LICENSE">the licence</a>.</p>
<div class="btnrow">
  <a class="btn default" href="/keyj/app.html">Open in browser</a>
  <a class="btn" href="https://github.com/vince-gonzalez/f-keys/releases/latest">Download</a>
  <a class="btn" href="/keyj/manual/">Manual</a>
  <a class="btn" href="https://pypi.org/project/keyj/">PyPI</a>
  <a class="btn" href="/keyj/privacy/">Privacy</a>
</div>"""),

 "pixelstaff": dict(
  title="Pixel Staff", tagline="An 8-bit composer with no DAW anywhere in it.",
  facts=[("Licence","MIT"),("Platform","Browser"),("Install","None"),("Exports","WAV, ringtone")],
  body="""
<h2>What it does</h2>
<p>Draw notes onto a 96-row piano roll, pick a waveform per channel, set the tempo and
press play. When it sounds right, take it away as a WAV or as a ringtone.</p>
<h2>Controls</h2>
<p>Draw and erase, play, stop and rewind, tempo in BPM, zoom from 1x to 8x, extend the
board and clear it. Square, saw, triangle and sine per channel.</p>
<p>One page, no dependencies. It opens and it works.</p>
<div class="btnrow"><a class="btn default" href="/pixelstaff/app.html">Open Pixel Staff</a></div>"""),

 "qv": dict(
  title="QV", tagline="One tap, one vote, live needle. The ballot comes to you.",
  facts=[("Version","0.5.0 \u2014 Ballot Box"),("Platform","Browser, PWA"),
         ("Accounts","None"),("Embeds","One script tag"),
         ("Source","vince-gonzalez/qv")],
  body="""
<h2>What it is</h2>
<p>A QV ballot is one question &mdash; yes or no, this or that &mdash; that anybody can
answer in a single tap. No account, no app, no sign-up. The result is a needle that moves
the moment anyone anywhere votes.</p>

<h2>The ballot comes to you</h2>
<p>Subscribe to channels &mdash; <code>#food</code>, <code>#politics</code>,
<code>#ohio</code>, whatever exists &mdash; and new ballots arrive as notifications. On
Chrome, Edge, Firefox and Android <b>you vote from the notification's own buttons without
opening anything</b>. That is the part that makes it different from a poll: answering costs
one tap from wherever you already were.</p>
<p>On iPhone it works through Add to Home Screen, which is Apple's requirement for web push
rather than a choice.</p>

<h2>Where a ballot can live</h2>
<table class="facts">
<tr><th>The feed</th><td>Vote in place, filter by channel, page through</td></tr>
<tr><th>Its own page</th><td>Vote, change your vote, watch the needle, copy the link</td></tr>
<tr><th>Any website</th><td>One script tag puts a live ballot on someone else's page</td></tr>
<tr><th>A notification</th><td>Vote from the buttons, without opening a page at all</td></tr>
</table>

<h2>For whoever is asking</h2>
<p>The creator terminal publishes and closes ballots and watches tallies live, behind a
creator key. Bulk seeding fills a channel from a question set, so a new channel does not
launch empty.</p>
<div class="btnrow">
  <a class="btn default" href="https://qv.f-keys.com/">Open QV</a>
  <a class="btn" href="https://github.com/vince-gonzalez/qv">Source</a>
</div>"""),

 "micdrop": dict(
  title="MICDROP", tagline="Grab the mic. Survive the room.",
  facts=[("Island code","1534-0440-5810"),("Creator","d00b"),
         ("Platform","Fortnite, built in UEFN"),("Players","Open lobby"),
         ("Support","hello@f-keys.com")],
  body="""
<h2>What it is</h2>
<p>A live open-mic arena inside Fortnite. One player takes the stage, the rest are the
room, and the room decides. Built in UEFN and playable from any Fortnite client with the
island code.</p>

<h2>How a set goes</h2>
<p>You get the stage and a clock. The crowd reacts while you are on it, and the reaction is
the score &mdash; there is no jury and no rubric, only whether the room stayed with you.
Then the mic moves and you are part of the crowd deciding somebody else's set.</p>

<h2>The real material is the voice chat</h2>
<p>MICDROP does not synthesise comedy or hand you prompts. The joke is whatever you say
into your own microphone, which means the island is scaffolding for a thing people were
already doing in party chat, with a stage and a scoreboard attached.</p>
<p>It also means the island cannot moderate what is said. Fortnite's own voice controls are
the only mute that exists, and that is Epic's layer rather than something a creator can
build. Play it with people you would already be in a call with.</p>

<h2>Playing it</h2>
<pre>Fortnite &rarr; Search by island code
<b>1534-0440-5810</b></pre>
<div class="btnrow">
  <a class="btn default" href="https://www.fortnite.com/@d00b/1534-0440-5810">Play now</a>
</div>"""),

 "wikipolish": dict(
  title="WikiPolish", tagline="Ten good edits is the hard part. This finds them.",
  facts=[("Status","Live"),("Platform","Browser"),("Install","None"),
         ("Reads","Wikipedia API"),("Account","Your own Wikipedia login")],
  body="""
<h2>The problem it solves</h2>
<p>A new Wikipedia account cannot do much. Ten edits and four days turns it into an
autoconfirmed one, which is when the encyclopedia starts trusting you. The barrier is not
the ten edits &mdash; it is finding ten changes you are genuinely sure are improvements,
in an encyclopedia where being wrong in public is the thing everyone fears.</p>

<h2>What it does</h2>
<p>Type an article, or press <b>Shuffle</b> and take whatever comes. WikiPolish pulls the
live text through the Wikipedia API and reads it back to you looking for the small,
defensible things: grammar, agreement, punctuation, the sentence that says the opposite of
what it meant.</p>
<p>Each finding links straight to the edit view for that article, so the fix happens on
Wikipedia in your own account, under your own name, with your own judgement. Nothing is
edited for you.</p>

<h2>It counts</h2>
<p><b>Log Edit</b> records the ones you actually made, so ten stops being a number you are
trying to remember and becomes a number you can see. <b>Next Article</b> keeps the queue
moving when one turns out to be already clean.</p>

<div class="btnrow">
  <a class="btn default" href="https://vince-gonzalez.github.io/wikiscout/">Open WikiPolish</a>
  <a class="btn" href="https://github.com/vince-gonzalez/wikiscout">Source</a>
</div>"""),

 "leadseer": dict(
  title="LeadSeer", tagline="Which businesses near you have no website at all?",
  facts=[("Status","Archived, working"),("Runtime","Node 18+, Electron"),
         ("Needs","A Google Places API key"),("Install","Run from source"),
         ("Source","vince-gonzalez/LeadSeer")],
  body="""
<h2>What it does</h2>
<p>Search a place and a trade &mdash; plumbers in Toledo, salons in Sarasota &mdash; and
LeadSeer asks the Google Places API for every match, then keeps only the ones whose record
has no website on it.</p>
<p>That absence is the whole qualification. A business with no website cannot already have
a web designer, which makes it the shortest possible answer to "who would actually take
this call". Everything else about lead lists is guessing; this is a field that is either
empty or not.</p>

<h2>What comes back</h2>
<p>Name, phone, address and a Google Maps link for each result, with the ones missing a
website surfaced first. Searches are kept in a local history so you can return to a town
without paying for the same lookups twice, and the list exports to a file.</p>

<h2>The key is yours</h2>
<p>LeadSeer has no server and no account. It calls Google Places with <b>your</b> API key,
stored in a local config, so the quota and the billing are yours and nothing routes through
anyone else. That is also the catch: without a key it cannot search at all.</p>

<h2>Archived, and honest about it</h2>
<p>It works and it is not being developed. There has never been a packaged installer &mdash;
it runs from source with Node and Electron. The code stays readable because a tool that
answers a real question is worth keeping.</p>
<div class="btnrow">
  <a class="btn default" href="https://github.com/vince-gonzalez/LeadSeer">Get the source</a>
</div>"""),

 "plumhud": dict(
  title="PlumHUD", tagline="Watch the fleet, not the screen.",
  facts=[("Name","Personal Ledger Utility Monitor, Heads-Up Display"),
         ("Version","4.1.0"),("Licence","MIT"),("Install","pip install plumhud"),
         ("Requires","Python 3.8+, Tk"),("Depends on","moonbeam-miner")],
  body="""
<h2>What it does</h2>
<p>A borderless overlay HUD that sits on top of whatever you are doing, with four display
modes, an opacity slider and five skins. A five-tab command center for miners, analytics,
alerts, skin and settings. Every poll is written to a local database with thirty-day
retention.</p>
<h2>Alerts</h2>
<p>Rules for offline, hashrate below a floor, temperature above a ceiling and reject
spikes, delivered to Discord or Telegram with a per-rule cooldown.</p>
<h2>What version 4 changed</h2>
<p>Nothing is invented any more. Version 3 filled missing readings with random numbers, so
a miner that answered without a hashrate displayed a believable figure you had no way to
identify as fake. A field the miner did not send is now shown as a dash and stored as
null, and alert rules stay quiet rather than reporting an absent measurement as a low one.</p>
<p>The config also stopped moving. It lives in one per-user directory, created owner-only,
because it holds a Discord webhook and a Telegram token.</p>
<pre><b>pip install plumhud</b>
plumhud          the overlay HUD
plumhud check    poll once, print, exit
plumhud where    where config and history live</pre>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/plumhud/">View on PyPI</a>
  <a class="btn" href="https://github.com/vince-gonzalez/f-keys/tree/main/plumhud">Source</a>
</div>"""),

 "streamsniper": dict(
  title="Stream Sniper", tagline="They go live. It is on the TV.",
  facts=[("Licence","MIT"),("Platform","Debian or Ubuntu"),
         ("Needs","Streamlink, VLC, pygame"),("Starts","systemd, on boot")],
  body="""
<h2>What it does</h2>
<p>Point a spare mini PC at the television and give it a list of Twitch channels. It shows
a clock until someone goes live, then puts them fullscreen with the ads out of the path.
When the stream ends, the clock comes back.</p>
<h2>How it behaves</h2>
<p>One username per line in a text file, and order is priority: if two are live, the one
nearer the top gets the screen. A stream already playing runs to the end, so nobody higher
in the list can cut in halfway through. Edits apply at the next check, with no restart.</p>
<pre>bash install.sh
<b>sudo systemctl start streamsniper@USER</b></pre>
<div class="btnrow"><a class="btn default" href="https://github.com/vince-gonzalez/f-keys/tree/main/streamsniper">Get the source</a></div>"""),

 "moonbeam": dict(
  title="Moonbeam", tagline="Find the NerdMiners on your network.",
  facts=[("Version","1.0.0"),("Licence","MIT"),("Install","pip install moonbeam-miner"),
         ("Requires","Python 3.8+"),("Dependencies","None")],
  body="""
<h2>What it does</h2>
<p>Sweeps your subnet for ESP-Miner and AxeOS devices, NerdMiner and Bitaxe and relatives,
and reads their vitals in a terminal. Whatever answers is remembered, so the next run just
polls them.</p>
<pre><b>pip install moonbeam-miner</b>
moonbeam            the miners it knows, polled now
moonbeam scan       sweep the subnet
moonbeam watch      refresh until you stop it
moonbeam show ip    everything one miner reported</pre>
<h2>A dash means the miner did not say</h2>
<p>It does not mean zero, and it is never a plausible number standing in for one that never
arrived. The summary counts how many devices declined to report rather than quietly
averaging them in.</p>
<p>Standard library only, so the install cannot fail on someone else's package.</p>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/moonbeam-miner/">View on PyPI</a>
  <a class="btn" href="https://github.com/vince-gonzalez/f-keys/tree/main/moonbeam">Source</a>
</div>"""),

 "remapwrap": dict(
  title="RemapWrap", tagline="Your phone is already the extra row of keys.",
  facts=[("Version","0.1.0 alpha"),("Runtime","Node.js 16+"),
         ("Phone needs","A browser"),("Install","None on the phone"),
         ("Source","vince-gonzalez/f-keys")],
  body="""
<p><img src="/remapwrap/assets/logo-256.png" alt="RemapWrap"
   style="width:132px;height:132px;float:right;margin:0 0 14px 20px"></p>
<h2>Zero to a deck in fifteen seconds</h2>
<p>Run the server, scan the QR code, and the phone in your hand is a control surface that
fires real OS-level keystrokes. The software you are driving never knows RemapWrap exists,
which is the point: it works with everything, because it is indistinguishable from a
keyboard.</p>
<p>A Stream Deck is a hundred and fifty dollars and a drawer you have to find it in. This
is the glass you are already holding.</p>

<h2>Then sixty seconds to make it yours</h2>
<p>The default layout is the fifteen-second answer. The real one is a mock screen you draw
on: drop a control anywhere, size it, colour it, and decide what it sends.</p>
<table class="facts">
<tr><th>Buttons</th><td>Any shape and size, from a single key to a full-width bar</td></tr>
<tr><th>Sliders</th><td>Continuous values &mdash; a volume, a zoom, an exposure</td></tr>
<tr><th>Dials</th><td>Rotary control, for the things a knob suits better than a bar</td></tr>
<tr><th>Scrollers</th><td>Wheel input, for timelines and long documents</td></tr>
<tr><th>Trackpad</th><td>An area that moves the pointer, because the phone already tracks a finger</td></tr>
</table>
<p>Every input a mouse has, on a surface with no fixed shape. A deck for editing does not
have to look anything like a deck for streaming, and neither has to look like a keyboard.</p>

<h2>Where it actually is</h2>
<p><b>The alpha is buttons.</b> The recovered v0.1.0 pairs over a QR code, serves a grid of
keys, fires them through the OS, and buzzes the phone on press. Layouts are JSON, edited
live in the dashboard. That much works today.</p>
<p>The sliders, dials, scrollers and trackpad above are the design and are not written yet.
They are on this page because they are what the product is for, and marked plainly so
nobody downloads the alpha expecting them.</p>

<h2>The company is named after this</h2>
<p>RemapWrap began as <b>F-Keys</b> &mdash; an extra row of keys, on glass you already own.
The name outgrew the product and became the company. The product then went missing for five
months, surviving in a single zip file in a folder called "zip to sort".</p>

<h2>Running it</h2>
<pre>npm install
<b>npm start</b>
scan the QR with your phone</pre>
<p>Both devices on the same network. Ports 7331 and 7332 open locally. Keystroke injection
via <code>@nut-tree-fork/nut-js</code>.</p>
<div class="btnrow">
  <a class="btn default" href="https://github.com/vince-gonzalez/f-keys/tree/main/remapwrap">Get the source</a>
</div>"""),

}


# ── the counts in the prose are counted ──────────────────────
# The homepage said "Twenty-two products are live" when there were
# twenty-six. Nothing was broken and every gate passed, because no gate
# had any opinion about a number spelled out in a sentence. It is the
# only thing on the page a client can catch being wrong without knowing
# anything about the work, which makes it the most expensive kind of
# stale there is.
WORDS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
         "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
         "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
        "Eighty", "Ninety"]


def count_word(n):
    """Twenty-six, not 26. The prose is written out and stays written out."""
    if n < 20:
        return WORDS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return TENS[tens] + ("-" + WORDS[ones].lower() if ones else "")
    return str(n)


def live_count():
    """Live means live: an Alpha or Needs-setup badge is not a live
    product, and the prose must not count it as one."""
    return sum(1 for c in CATALOGUE if c[4] not in (ALPHA, SETUP))


def counted(text):
    """Fill the tokens no gate could previously check."""
    return (text.replace("%%PRODUCTS%%", count_word(len(CATALOGUE)))
                .replace("%%LIVE%%", count_word(live_count()).lower())
                .replace("%%SHELVES%%", count_word(len(CATEGORIES)).lower()))


ABOUT_DOC = """
<div class="doc"><h1>About F-Keys</h1>
<p class="sub">Independent products built by Vincent Gonzalez.</p>
<table class="facts">
<tr><th>Entity</th><td>F-Keys Creative LLC (Florida)</td></tr>
<tr><th>Trading as</th><td>F-Keys</td></tr>
<tr><th>ORCID</th><td>0009-0005-3640-014X</td></tr>
<tr><th>Contact</th><td>hello@f-keys.com</td></tr>
</table>
<h2>What this is</h2>
<p>F-Keys is Vince Gonzalez, working alone. %%PRODUCTS%% products are on the
shelves &mdash; %%LIVE%% of them live today, the rest labeled alpha or
needs-setup, because a badge is cheaper than a broken promise &mdash; from
browser games to formal proof tooling, and each is built end to end by the same
person: architecture, both ends, database, deployment, documentation.</p>
<h2>The recurring interest</h2>
<p>Provenance - what a result actually rests on. gonzalgo reads a compiled Lean 4
or Metamath library and reports which axioms a theorem spends rather than quietly
inherits. OpticQuiz runs one colour-vision engine across eight distribution
channels, with its JavaScript and Python implementations verified identical to six
decimal places, and publishes the calibration limits that keep its own results
honest.</p>
<p>More than thirty works are deposited with DOIs. The packages are installed
several hundred times a week. Six pull requests to
<a href="https://github.com/metamath/set.mm" rel="noopener">metamath/set.mm</a>
carry the measurements back upstream &mdash; reviewed and merged by that
library's own maintainers.</p>
<h2>Current interests</h2>
<p>Accessibility &middot; hardware interfaces &middot; creator tools &middot; gaming
&middot; formal methods &middot; the open web.</p>
<div class="btnrow">
  <a class="btn default" href="/papers/">Read the papers</a>
  <a class="btn" href="/log/">Working log</a>
  <a class="btn" href="/status/">Status</a>
</div>
</div>
"""

# -- the homepage document ------------------------------------
# An agent was asked what F-Keys is and had to visit eight pages to
# assemble an answer, because the homepage was a bare table with no
# heading and no prose. This is the answer in one place: what the
# catalogue is, who each shelf is for, and what any of it costs.
HOME_DOC = """
<div class="doc" style="padding-bottom:6px">
<h1>F-Keys</h1>
<p class="sub">Hardware. Software. Ideas brought to life.</p>
<p>F-Keys is the working catalogue of <b>Vincent Gonzalez</b>, an independent
builder trading as F-Keys Creative LLC in Punta Gorda, Florida. %%PRODUCTS%%
products are on the shelves, %%LIVE%% of them live today, and each one was
designed, written, deployed and documented
by the same person &mdash; architecture, both ends, database, release notes. The
table below is the whole company.</p>
<p>The name came from a product. <a href="/remapwrap/">RemapWrap</a> was called
F-Keys first &mdash; an extra row of function keys, on glass you already own
&mdash; and the name outgrew it. The product then went missing for five months
and survives because it was in a zip file in a folder called &ldquo;zip to
sort&rdquo;.</p>

<h2>What is on the shelves</h2>
<p>%%SHELVES%% of them, sorted the way a file manager would sort them.
<a href="/apps.html">Apps</a> are things you run: a keyboard that plays notes in
any program, an 8-bit composer, colour-vision tests, live ballots for a room.
<a href="/games.html">Games</a> holds a warehouse-loading simulator, two Discord
activities and a Fortnite island. <a href="/tools.html">Tools</a> are small
single-purpose programs for people who already know what they want.
<a href="/hardware.html">Hardware</a> turns a spare machine into an appliance.
<a href="/research.html">Research</a> is the formal-methods work &mdash; papers
with DOIs and the tooling the measurements run on.
<a href="/properties.html">Properties</a> lists the standalone sites.</p>

<h2>Who it is for</h2>
<p>There is no single customer, because these are not one product line. A Lean 4
axiom auditor, a colour-vision test and a Discord word game share no market at
all. In practice the people who end up here are <b>developers and proof
engineers</b> who need to know what a theorem actually rests on, <b>designers and
accessibility teams</b> checking colour against a real engine rather than a
guess, <b>musicians and typists</b> who want a keyboard to make sound,
<b>streamers and Discord communities</b> looking for something to run in a room
full of people, and <b>trainers</b> who want load planning to behave like the
physical thing.</p>

<p>Each product page carries its own terms, licence and price. Nothing is assumed
to match the last one. <a href="/contact.html">Contact</a> for licensing, or
<a href="/privacy.html">Privacy</a> for what this site does and does not collect.</p>
</div>
"""

# -- contact --------------------------------------------------
# One of the three pages an agent checks before it will describe a
# business as real. The filing details are here rather than in prose so
# that a reader and a parser get the identical facts.
CONTACT_DOC = """
<div class="doc"><h1>Contact</h1>
<p class="sub">One person reads this. There is no support queue and no ticket
number.</p>
<table class="facts">
<tr><th>Email</th><td><a href="mailto:hello@f-keys.com">hello@f-keys.com</a></td></tr>
<tr><th>Entity</th><td>F-Keys Creative LLC, a Florida limited liability company</td></tr>
<tr><th>Document number</th><td>L26000436157, filed 18 August 2026, status active</td></tr>
<tr><th>Based in</th><td>Punta Gorda, Florida, United States</td></tr>
<tr><th>Registered agent</th><td>Vincent Gonzalez. The registered address is
on file with the
<a href="https://search.sunbiz.org/Inquiry/CorporationSearch/ByName" rel="noopener">Florida
Division of Corporations</a> under the document number above.</td></tr>
<tr><th>ORCID</th><td><a href="https://orcid.org/0009-0005-3640-014X" rel="noopener">0009-0005-3640-014X</a></td></tr>
<tr><th>Source code</th><td><a href="https://github.com/vince-gonzalez" rel="noopener">github.com/vince-gonzalez</a></td></tr>
</table>

<h2>What to write about</h2>
<p><b>A bug, or something that will not run.</b> Say which product, which
operating system, and what you saw instead. Every product page lists what it
needs; if the answer is on that page the reply will just point at it, which is
faster for both of us.</p>
<p><b>Licensing.</b> Trailer Load is licensed to institutions for training use.
Anything else you want to use commercially, ask &mdash; the published source is
MIT and the answer is usually yes and costs nothing.</p>
<p><b>The research.</b> Questions about the axiom-provenance work, the papers, or
a measurement you want reproduced are welcome and get a real answer. The tooling
is public, so you can check the numbers without asking.</p>
<p><b>Press, or a correction.</b> If something on this site is wrong, saying so
is the fastest way to get it fixed. Corrections go in the
<a href="/log/">working log</a> with a date.</p>

<h2>What not to expect</h2>
<p>There is no phone line, because there is no one to answer it. Replies come
from one person between builds, so a few days is normal and a week is not
unusual. Nothing here is sold through a reseller, so an email offering to
represent F-Keys will not get a reply.</p>
<div class="btnrow">
  <a class="btn default" href="mailto:hello@f-keys.com">Send an email</a>
  <a class="btn" href="/about.html">About</a>
  <a class="btn" href="/privacy.html">Privacy</a>
</div>
</div>
"""

# -- privacy --------------------------------------------------
# Every claim on this page is a property of the source rather than a
# promise: the AdSense tag was removed from Docs.html so that "no
# advertising" is true, and tools/test_site.py fails the build if an ad
# tag, a tracker or a cookie write reappears anywhere in the tree.
PRIVACY_DOC = """
<div class="doc"><h1>Privacy</h1>
<p class="sub">This site does not want your data, and the shortest way to say so
is to describe every byte it does receive.</p>

<h2>The short version</h2>
<table class="facts">
<tr><th>Advertising</th><td>None. No ad network, no ad tags, no affiliate tracking.</td></tr>
<tr><th>Analytics</th><td>None. No Google Analytics, no tag manager, no pixel, and
no first-party analytics script of any kind.</td></tr>
<tr><th>Cookies</th><td>None. This site sets no cookies, so there is no consent
banner to dismiss.</td></tr>
<tr><th>Accounts</th><td>None. Nothing on f-keys.com asks you to sign up or sign in.</td></tr>
<tr><th>Third-party code</th><td>None. No page on this site loads anything from
another company's server &mdash; not a script, not a stylesheet, not a font.</td></tr>
</table>
<p>These are checkable rather than promised. The site is a folder of static files
in a public repository, and a test in that repository fails the build if an ad
tag, a tracking script or a cookie write appears anywhere in it.</p>

<h2>What the servers see anyway</h2>
<p>The pages are served by GitHub Pages through Cloudflare. Both keep ordinary
web-server logs, which means your IP address, the page you asked for, your
browser's user-agent string and the time are recorded by those companies as a
side effect of the request being delivered at all. F-Keys does not receive those
logs, cannot query them, and does not know who visited. Their handling is
governed by
<a href="https://docs.github.com/site-policy/privacy-policies/github-privacy-statement" rel="noopener">GitHub's privacy statement</a>
and
<a href="https://www.cloudflare.com/privacypolicy/" rel="noopener">Cloudflare's privacy policy</a>.</p>

<h2>The fonts are ours too</h2>
<p>The <a href="/Docs.html">Docs</a> page used to load two typefaces from Google
Fonts. A font request looks harmless and is not: it reports the IP address of
everyone who opens the page, on every visit, to a company whose business is
knowing things about people. Both faces are under the SIL Open Font License,
which permits hosting them, so they are served from this domain and that request
no longer leaves. Nothing else on this site loads from a third party either.</p>

<h2>The products are not this site</h2>
<p>Several products store their settings in your own browser or on your own
machine, where they never leave it and are not visible here. Where a product does
more than that it carries its own privacy document, and the strongest claims are
tested rather than asserted &mdash; <a href="/keyj/privacy/">Key-J</a> installs a
system-wide keyboard hook, so its page describes exactly what that hook can see,
and a test in the repository asserts that the function a keypress calls cannot
retain a key. Products hosted elsewhere, and the separate
<a href="/properties.html">properties</a>, are governed by their own policies
rather than this one.</p>

<h2>Your rights, and how little there is to exercise them on</h2>
<p>Rights of access, correction, deletion and portability under the GDPR, the
CCPA and similar laws attach to personal data held by the operator. F-Keys holds
none from this site: there is no database, no mailing list gathered here, and no
profile of you. If you send an email it exists in a mailbox until you ask for it
to be deleted, and asking is enough. This site is not directed at children and
collects nothing from anyone, of any age.</p>
<p>Questions, or a challenge to any claim above, go to
<a href="mailto:hello@f-keys.com">hello@f-keys.com</a>. If a claim here
ever stops being true, the page changes first and the change is dated in the
<a href="/log/">working log</a>.</p>
<div class="btnrow">
  <a class="btn default" href="/contact.html">Contact</a>
  <a class="btn" href="/about.html">About</a>
</div>
</div>
"""

# -- the 404 --------------------------------------------------
# A missing path already returned a real 404; what it did not return was
# anything to do next. An agent that follows a stale link gets the same
# recovery list a person would: where the map is, and where the machine-
# readable summary of the whole site lives.
NOT_FOUND_DOC = """
<div class="doc"><h1>404 &mdash; that page is not here</h1>
<p class="sub">The address is wrong, or the page moved and something still points
at where it used to be.</p>
<h2>Where to look next</h2>
<ul>
<li><b><a href="/">f-keys.com</a></b> &mdash; every product in one table.</li>
<li><b><a href="/sitemap.xml">/sitemap.xml</a></b> &mdash; every URL on this
site, for crawlers and agents.</li>
<li><b><a href="/llms.txt">/llms.txt</a></b> &mdash; the whole catalogue as plain
text, including what each product is for and when to reach for it.</li>
<li><b><a href="/Docs.html">/Docs.html</a></b> &mdash; setup, configuration and
troubleshooting.</li>
<li><b><a href="/contact.html">/contact.html</a></b> &mdash; a person, if the
link that sent you here was ours.</li>
</ul>
<h2>By shelf</h2>
<ul>
<li><a href="/apps.html">/apps.html</a> &mdash; things you run</li>
<li><a href="/games.html">/games.html</a> &mdash; games and simulators</li>
<li><a href="/tools.html">/tools.html</a> &mdash; single-purpose programs</li>
<li><a href="/hardware.html">/hardware.html</a> &mdash; appliances</li>
<li><a href="/research.html">/research.html</a> &mdash; papers and proof tooling</li>
<li><a href="/properties.html">/properties.html</a> &mdash; the standalone sites</li>
</ul>
<div class="btnrow">
  <a class="btn default" href="/">Back to the catalogue</a>
  <a class="btn" href="/llms.txt">llms.txt</a>
  <a class="btn" href="/sitemap.xml">sitemap.xml</a>
</div>
</div>
"""

# -- developer resources --------------------------------------
# An audit asked for a developer portal with API keys and a sandbox.
# There is no API to key, and inventing one would be a lie an agent
# could not detect until it tried a call. What there IS is a real
# developer surface - four packages, an Action, and 35 published JSON
# datasets - which was scattered across ten pages and named nowhere.
# This is that surface in one place, under the name someone would
# search for.
DEVELOPERS_DOC = """
<div class="doc"><h1>F-Keys developer resources</h1>
<p class="sub">Four command-line tools, six packages, and a shelf of published
JSON. Everything here is a thing you install or a file you fetch, and there is
nothing to sign up for.</p>

<h2>Start here</h2>
<table class="facts">
<tr><th>OpenAPI</th><td><a href="/openapi.json">/openapi.json</a> &mdash; every
published document, each with a typed schema naming its columns</td></tr>
<tr><th>For agents</th><td><a href="/llms.txt">/llms.txt</a> &mdash; the whole
catalogue as plain text, including when to reach for each thing</td></tr>
<tr><th>Site map</th><td><a href="/sitemap.xml">/sitemap.xml</a></td></tr>
<tr><th>Product docs</th><td><a href="/Docs.html">/Docs.html</a> &mdash; setup,
configuration and troubleshooting</td></tr>
<tr><th>Source</th><td><a href="https://github.com/vince-gonzalez" rel="noopener">github.com/vince-gonzalez</a></td></tr>
<tr><th>Questions</th><td><a href="mailto:hello@f-keys.com">hello@f-keys.com</a></td></tr>
</table>

<h2>Authentication</h2>
<p><b>There is none, and none is required.</b> No API key, no token, no OAuth
flow, no signup. Every request below works from a cold start with no
credentials and no headers:</p>
<pre>curl https://f-keys.com/gonzalgo/kernel-index/kernel-index.json</pre>
<p>This is not a free tier with a paid one behind it. Every F-Keys product runs
in your browser or installs on your machine, so nothing calls a server of ours
&mdash; this site is a folder of static files behind a CDN. There is nothing to
authenticate against because there is nothing running.</p>
<p>What that buys you: the packages work offline, they keep working if this site
goes away, and nothing you compute is reported back here. What it costs you:
there is no endpoint to POST to. If you need one, the source is public.</p>

<h2>Rate limits</h2>
<p><b>None.</b> No quota, no <code>429</code>, and deliberately no
<code>RateLimit</code> headers &mdash; publishing a limit nobody enforces would
tell you to throttle against a number that does not exist.</p>
<p>The CDN already sends <code>ETag</code> and <code>Last-Modified</code>, so
use them and a repeat fetch costs you a <code>304</code> and no body:</p>
<pre>curl -H "If-None-Match: &quot;&lt;etag&gt;&quot;" \\
     https://f-keys.com/status/latest.json</pre>

<h2>Versioning and deprecation</h2>
<p><b>The URLs are permanent; the data carries the version.</b> There is no
<code>/v1/</code> prefix because there is no server to route one.</p>
<p>Every document is served twice, byte for byte: at its bare path, and
under <code>/v1</code>. Integrate against whichever suits you.</p>
<pre># the same bytes, and the second carries a version stamp
curl https://f-keys.com/gonzalgo/kernel-index/kernel-index.json
curl -i https://f-keys.com/v1/gonzalgo/kernel-index/kernel-index.json | grep -i x-api-version</pre>
<table class="facts">
<tr><th>Under /v1</th><td>What is served there keeps the shape it has today.
A breaking change appears as <code>/v2</code> while <code>/v1</code> keeps
serving the old shape. Responses carry <code>X-API-Version: v1</code>, and a
version that does not exist answers <code>404</code> with the code
<code>unknown_version</code> rather than looking like a typo.</td></tr>
<tr><th>Pin to content</th><td>Every document carries a <code>version</code>
(the measurement date) and a <code>sha256</code>. Re-measuring republishes the
same URL with both changed, so comparing either tells you whether anything moved
under you.</td></tr>
<tr><th>Pin to a release</th><td>Each table carries a <code>seriesDoi</code>
resolving to an immutable Zenodo deposit. Cite that, not this page.</td></tr>
<tr><th>Breaking changes</th><td>Fields are added, never removed or retyped. A
field that has to go is announced in the <a href="/log/">working log</a> and
kept for at least <b>180 days</b> after that entry.</td></tr>
<tr><th>Deprecation signal</th><td>A path scheduled for removal is served with
the <code>Deprecation</code> and <code>Sunset</code> headers of RFC 8594 and RFC
9745, and listed under <code>x-versioning.deprecated</code> in
<a href="/openapi.json">openapi.json</a>. That list is currently empty.</td></tr>
</table>

<h2>The command line</h2>
<p>Four of these are real CLIs, not libraries with a script attached. Each does
its whole job from a terminal, which is the point: an agent can drive them
without an integration.</p>
<pre><b>pip install gonzalgo</b>
gonzalgo trust <i>path</i>              every theorem reaching a sorry
gonzalgo why <i>decl</i> <i>axiom</i>          shortest labelled path to an axiom
gonzalgo trust <i>path</i> --fail-on-trust  exit non-zero in CI</pre>
<pre><b>pip install keyj</b>
keyj tab solo.txt -o song.txt    tablature in, note names out
keyj render song.txt out.wav     the sequence, at a tempo
keyj show song.txt               what is in a sequence</pre>
<pre><b>pip install moonbeam-miner</b>
moonbeam scan                    find the NerdMiners on this network
moonbeam watch                   their vitals, live</pre>
<pre><b>pip install plumhud</b>
plumhud                          the overlay HUD
plumhud --history                what the fleet has been doing</pre>
<p>In a pipeline, the
<a href="https://github.com/marketplace/actions/gonzalgo-trust-audit" rel="noopener">gonzalgo-trust-audit</a>
Action is three lines of workflow and fails the build when a proof rests on
something unfinished.</p>

<h2>Packages</h2>
<table class="facts">
<tr><th>gonzalgo</th><td><code>pip install gonzalgo</code> &mdash; axiom
provenance for Lean 4 and Metamath. Apache-2.0.</td></tr>
<tr><th>keyj</th><td><code>pip install keyj</code> &mdash; tablature to notes,
render, and play.</td></tr>
<tr><th>plumhud</th><td><code>pip install plumhud</code> &mdash; miner fleet
monitor.</td></tr>
<tr><th>moonbeam-miner</th><td><code>pip install moonbeam-miner</code> &mdash;
NerdMiner discovery and vitals.</td></tr>
<tr><th>opticquiz-cvd</th><td><code>npm i opticquiz-cvd</code> &mdash;
colour-vision simulation and daltonisation.</td></tr>
<tr><th>&#64;f-keys/tip-widget</th><td><code>npm i &#64;f-keys/tip-widget</code>
&mdash; the TipStreams widget.</td></tr>
</table>

<h2>Upstream, merged</h2>
<p>The measurements feed back into the library they measure. Six pull requests
to <a href="https://github.com/metamath/set.mm" rel="noopener">metamath/set.mm</a>
&mdash; the Metamath Proof Explorer's canonical database, reviewed and merged by
its own maintainers &mdash; each remove an avoidable axiom-of-choice dependency
that the tooling on this page located:</p>
<table class="facts">
<tr><th><a href="https://github.com/metamath/set.mm/pull/5442" rel="noopener">#5442</a></th><td>Remove the ax-ac dependency from <code>difelsiga</code> &mdash; merged 2026-08-19</td></tr>
<tr><th><a href="https://github.com/metamath/set.mm/pull/5448" rel="noopener">#5448</a></th><td>Drop the ax-ac dependency from <code>omeiunle</code> &mdash; merged 2026-08-21</td></tr>
<tr><th><a href="https://github.com/metamath/set.mm/pull/5447" rel="noopener">#5447</a></th><td>Avoid ax-ac in <code>sigaclci</code> directly &mdash; merged 2026-08-21</td></tr>
<tr><th><a href="https://github.com/metamath/set.mm/pull/5445" rel="noopener">#5445</a></th><td>Shorten <code>madefi</code> and drop its ax-ac dependency &mdash; merged 2026-08-21</td></tr>
<tr><th><a href="https://github.com/metamath/set.mm/pull/5443" rel="noopener">#5443</a></th><td>Add <code>fnrndomnum</code>, and prove <code>fnrndomg</code> from it &mdash; merged 2026-08-24</td></tr>
<tr><th><a href="https://github.com/metamath/set.mm/pull/5458" rel="noopener">#5458</a></th><td>Drop the ax-ac dependency from <code>fnct</code>, <code>dmct</code> and <code>ffsrn</code> &mdash; merged 2026-08-26</td></tr>
</table>
<p>Three more set.mm pull requests are open in review, along with two
<a href="https://github.com/microsoft/winget-pkgs/pull/421552" rel="noopener">winget-pkgs</a>
package submissions. Open means open &mdash; nothing here is claimed merged
until its maintainers say so.</p>

<h2>The published data</h2>
<p>Every published document is described in
<a href="/openapi.json">openapi.json</a> with a typed schema that names its
columns &mdash; so a function-calling agent knows a table has a
<code>library</code> string and a <code>theorems</code> integer before it
fetches half a megabyte to find out.</p>
<table class="facts">
<tr><th>Measurement tables</th><td>Thirteen tables behind the papers &mdash; the
<a href="/gonzalgo/kernel-index/">Kernel Index</a>, the
<a href="/gonzalgo/dominator-table/">Dominator Table</a> and the rest. One
object each, carrying its <code>version</code>, <code>sha256</code>,
<code>license</code> and <code>seriesDoi</code> beside its <code>rows</code>.
CC BY 4.0.</td></tr>
<tr><th>Kernel Trust Profile</th><td>The
<a href="/gonzalgo/kernel-trust/kernel-trust-0.1.schema.json">0.1 schema</a> and
fourteen profiles conforming to it, one per library measured.</td></tr>
<tr><th>Status</th><td><a href="/status/latest.json">/status/latest.json</a>
&mdash; the daily snapshot behind the <a href="/status/">status page</a>.
Repository traffic is owner-only and is not in it.</td></tr>
</table>
<pre># the whole surface, as an agent would discover it
curl https://f-keys.com/openapi.json | jq '.paths | keys'

# one table, and the columns it declares
curl -s https://f-keys.com/gonzalgo/kernel-index/kernel-index.json | jq '.rows[0]'

# check whether it moved since you last looked
curl -s https://f-keys.com/gonzalgo/kernel-index/kernel-index.json | jq -r '.version, .sha256'</pre>

<h2>The site itself is machine-readable</h2>
<p>Every page here serves <b>Markdown</b> to anything that asks. Send
<code>Accept: text/markdown</code> and you get the content without the window
around it, per <a href="https://acceptmarkdown.com" rel="noopener">acceptmarkdown.com</a>,
with <code>Vary: Accept</code> set so a cache cannot hand you the wrong one.</p>
<pre>curl -H "Accept: text/markdown" https://f-keys.com/keyj/</pre>
<p>A path that does not exist returns a real <b>404</b> in the format you asked
for. Anything under a data path &mdash; a <code>.json</code> URL,
<code>/api</code>, <code>/v1</code> &mdash; errors as JSON even when the client
sends no <code>Accept</code> at all, because most of them do not:</p>
<pre>curl https://f-keys.com/gonzalgo/no-such-table.json

{
  "error": {
    "code": "not_found",
    "message": "No resource exists at /gonzalgo/no-such-table.json",
    "status": 404,
    "path": "/gonzalgo/no-such-table.json",
    "hints": [ "..." ]
  }
}</pre>
<p>The <code>code</code> is stable and machine-readable, the
<code>hints</code> name the three places a lost agent can recover from, and the
envelope is the one under <code>components.schemas.Error</code> in the
specification.</p>
<div class="btnrow">
  <a class="btn default" href="/openapi.json">openapi.json</a>
  <a class="btn" href="/llms.txt">llms.txt</a>
  <a class="btn" href="/Docs.html">Docs</a>
  <a class="btn" href="/contact.html">Contact</a>
</div>
</div>
"""

EXTRA_NODES = [("/about.html", "About"), ("/Docs.html", "Docs"), ("/developers.html", "Developers"),
               ("/log/", "Log"), ("/status/", "Status"), ("/papers/", "Papers"),
               ("/contact.html", "Contact"), ("/privacy.html", "Privacy")]

# ── the identity the machines read ───────────────────────────
# An agent asked what F-Keys is and had to assemble the answer from eight
# pages. These are the same facts as the About page, in the one shape a
# parser will take without reading prose: schema.org JSON-LD, emitted by
# shell() so no page can carry a different version of them.
SITE = "https://f-keys.com"
OG_IMAGE = SITE + "/assets/og.png"

# The mark a product actually has, or the house card. productart writes
# <slug>-og.png from a mark; until a product has one, every link to it
# unfurls as the F-Keys card, which is correct but tells a reader
# nothing about which of twenty-six things they are looking at.
def product_og(slug):
    if slug:
        name = slug + "-og.png"
        if os.path.isfile(os.path.join(ROOT, "assets", "products", name)):
            return SITE + "/assets/products/" + name
    return OG_IMAGE


def product_mark(slug):
    """The 256px mark, for the page itself. None when there is none."""
    if slug:
        name = slug + "-256.png"
        if os.path.isfile(os.path.join(ROOT, "assets", "products", name)):
            return "/assets/products/" + name
    return None


def _shot_dates():
    """When each screenshot was taken, from the capture manifest."""
    path = os.path.join(ROOT, "assets", "products", "shots.json")
    if not os.path.isfile(path):
        return {}
    try:
        with io.open(path, encoding="utf-8") as f:
            return dict((k, v.get("captured", ""))
                        for k, v in json.load(f).items())
    except (ValueError, AttributeError):
        return {}


SHOT_DATES = _shot_dates()


def product_shot(slug):
    """A picture of the product running, if one has been captured.

    A mark says a product has an identity; a screenshot says somebody
    can go and use it. Twenty-six pages of prose describing software is
    the format least able to prove the software exists, and prose is
    what a client has the least reason to believe.
    """
    if slug:
        name = slug + "-shot-800.png"
        if os.path.isfile(os.path.join(ROOT, "assets", "products", name)):
            return "/assets/products/" + name
    return None

LEGAL_NAME = "F-Keys Creative LLC"
FOUNDER = "Vincent Gonzalez"
EMAIL = "hello@f-keys.com"
ORCID = "https://orcid.org/0009-0005-3640-014X"
# The account that hosts this site's own source. Older products still
# live under github.com/zengineco until their repos migrate; their pages
# link them directly.
GH_ORG = "https://github.com/vince-gonzalez"

# Filed with the Florida Division of Corporations 2026-08-18,
# document L26000436157. Kept here so the schema and the Contact page
# cannot drift from the filing or from each other.
#
# The street line is deliberately absent. The filing is public record and
# names it, but the registered address is a home, and a website with
# schema.org markup is a different amount of reach than a state database
# nobody reads. Locality, region and country are enough to say where the
# company answers from and enough for the schema to validate; anyone who
# needs the full address can get it from the Division of Corporations or
# by asking.
ADDRESS = {
    "addressLocality": "Punta Gorda",
    "addressRegion": "FL",
    "postalCode": "33955",
    "addressCountry": "US",
}


def jsonld(obj):
    """One script tag, stable key order, no trailing whitespace."""
    return '''<script type="application/ld+json">
{}
</script>'''.format(json.dumps(obj, indent=2, ensure_ascii=False))


def organization():
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": SITE + "/#organization",
        "name": "F-Keys",
        "legalName": LEGAL_NAME,
        "alternateName": "F-Keys Creative LLC",
        "url": SITE,
        "logo": SITE + "/assets/fkeys-logo.png",
        "image": OG_IMAGE,
        "description": "Independent hardware, software and internet products "
                       "built by Vincent Gonzalez. Apps, games, tools, "
                       "hardware and research.",
        "email": EMAIL,
        "founder": {
            "@type": "Person",
            "name": FOUNDER,
            "identifier": ORCID,
            "sameAs": [ORCID, GH_ORG],
        },
        "foundingDate": "2026-08-18",
        "address": dict({"@type": "PostalAddress"}, **ADDRESS),
        "contactPoint": [{
            "@type": "ContactPoint",
            "contactType": "customer support",
            "email": EMAIL,
            "areaServed": "Worldwide",
            "availableLanguage": ["English"],
        }],
        "sameAs": [GH_ORG, ORCID],
    }


def esc(s):
    return html.escape(str(s), quote=True)


# ── the shell ────────────────────────────────────────────────

# The Key-J manual. Written because an FL Studio veteran needed a solid
# session of tinkering to find sequence mode, and a feature nobody can
# find is a feature nobody has.
KEYJ_MANUAL = """
<h2>Which Key-J are you holding</h2>
<p>There are two, and the difference decides what the app can do at all.</p>
<table class="facts">
<tr><th>In a browser</th><td>Notes play while the Key-J tab has focus. Nothing else.</td></tr>
<tr><th>The desktop app</th><td>Notes play while you type in any application, once
Global Capture is switched on.</td></tr>
</table>
<p>A browser cannot see keystrokes outside its own page, and it should not be able
to &mdash; a page that could read what you type into your bank would be a keylogger.
So the browser version is not a crippled desktop version, it is at its permanent
ceiling. The header tells you which one you have.</p>

<h2>Turning it on</h2>
<p><b>Browser:</b> click anywhere on the page and type. There is no switch, because
there is nothing to switch.</p>
<p><b>Desktop:</b> the titlebar carries a <b>Global Capture</b> toggle with a badge
beside it. The badge reads <b>Window only</b> until you flip it, then <b>Global</b>.
If it reads <b>Hook unavailable</b>, the native key hook did not load and only the
Key-J window will be heard &mdash; on Linux that usually means the app needs
permission to read input devices, on Windows that a security tool blocked it.</p>
<p>Closing the window does not quit the desktop app. It keeps running in the tray so
your keys keep playing. Quit from the tray menu.</p>

<h2>The three tools</h2>
<p>The centre of the window is tabbed, and one tool shows at a time. That is
deliberate: stacked, the three of them made the page four thousand pixels tall.</p>
<table class="facts">
<tr><th>Keyboard</th><td>Sixty-one keys, C2 to C7. Click them to hear them, or turn on
<b>Build</b> and click a run in.</td></tr>
<tr><th>Grid</th><td>A step grid with nine kits, drums among them. Draw a pattern, then
<b>Use as sequence</b>.</td></tr>
<tr><th>Tab &amp; Sequence</th><td>Paste guitar tablature, or type note names. This is
where a song gets in.</td></tr>
</table>

<h2>Sequence mode, which is the part people miss</h2>
<p>Normally each key holds a fixed pitch: Q is one note, W is the next. That is fine
for noise and useless for a song.</p>
<p><b>With a sequence loaded, every key plays the next note of it.</b> Which key you
press stops mattering. You are no longer playing pitches, you are playing
<em>rhythm</em>, and the melody is already handled. That is how typing an email
produces a solo.</p>
<p>The status line shows how many notes are loaded, where you are in them and what
comes next. <b>Restart</b> returns to the first note. <b>Sequence OFF</b> puts the
fixed bindings back.</p>

<h2>Getting a song in</h2>
<p><b>From tablature.</b> Paste it in, pick the tuning, set a capo if there is one,
press <b>Convert</b>. Eight tunings including drop D, E flat, DADGAD, seven string
and bass.</p>
<p>The importer states what it read: the tuning it used, how many strings it found,
how many notes it produced, and the name of anything it could not read. A block with
the wrong number of lines produces no notes and says so rather than guessing, because
a wrong note you cannot see is worse than a missing one you can.</p>
<p>What it cannot catch is a tab that is internally consistent and simply wrong. Bad
frets convert cleanly into bad notes, and nothing but your ear will find that.</p>
<p><b>From note names.</b> Type or paste them into the note box:
<code>E5 G5 B5 E6</code>. Sharps and flats both work.</p>
<p><b>From a file.</b> <b>Load .txt</b> takes a saved sequence, or any list of note
names. <b>Import MIDI</b> takes a MIDI file and uses its note order.</p>
<p><b>From the keyboard or the grid.</b> Click a run in, then <b>Use as sequence</b>.</p>

<h2>Saving what you built</h2>
<table class="facts">
<tr><th>Save .txt</th><td>The sequence as note names. The file pastes straight back
into the note box, so saving and loading are one format.</td></tr>
<tr><th>Export WAV</th><td>The sequence rendered one note per beat at the BPM you set,
through the tone you chose.</td></tr>
<tr><th>Export Session</th><td>A recording of what you actually typed, with your
timing. A different thing, and rarely the one you want.</td></tr>
</table>
<p>Export WAV renders the <em>sequence</em>. Export Session renders <em>your typing</em>.
If you imported a tab and want to hear the song, you want Export WAV.</p>

<h2>Updates</h2>
<p>Key-J does not check for updates on its own, and that is deliberate: it makes
no network requests at all, which is a promise worth more than the convenience.
The tray menu has <b>Check for updates</b>, which opens the releases page in your
browser when you ask it to.</p>

<h2>Sound</h2>
<p>Seven tone presets, four waveforms, and sliders for attack, release, volume, reverb
and pitch. Six play styles: normal, staccato, vibrato, tremolo, arpeggio, legato. The
tone you have set is the tone the WAV export uses.</p>

<h2>The staff</h2>
<p>Notes land on a treble staff as you play, scrolling to keep the newest in view.
Key-J spans C2 to C7, which no single treble staff shows at a readable size, so a note
outside the drawable range is pinned to the edge in orange with an arrow pointing the
way it went and its name beside it. A note that will not fit is reported, not dropped.</p>

<h2>When something is wrong</h2>
<table class="facts">
<tr><th>No sound at all</th><td>Browsers will not start audio until you interact with
the page. Click the page, then type.</td></tr>
<tr><th>Nothing plays outside the window</th><td>You are in the browser version, or
Global Capture is off. Check the badge in the header.</td></tr>
<tr><th>Every key plays the same run</th><td>Sequence mode is on, and that is what it
does. Press <b>Sequence OFF</b> for fixed pitches.</td></tr>
<tr><th>Notes cut off sharply</th><td>Release is low. Raise the Release slider, or pick
a tone with a longer tail such as Bell or Pad.</td></tr>
<tr><th>The tab imported nothing</th><td>The status line names what it skipped. Most
often the block has a different number of string lines than the tuning expects.</td></tr>
<tr><th>Two Key-J entries in Add/Remove Programs</th><td>Only if you installed
1.4.0. That build carried a different application identifier, which Windows uses
to recognise an upgrade, so anything newer installs beside it rather than over
it. Uninstall both, then install the current version once. Nothing installed
from 1.4.1 onward does this.</td></tr>
<tr><th>The installer says it cannot continue</th><td>Key-J is running. Close it
&mdash; including from the tray &mdash; and install again. It stops rather than
replacing the files it can reach and leaving the ones Windows has open, which
would give you half of each version.</td></tr>
</table>

<h2>What it can see</h2>
<p>With Global Capture on, Key-J receives a signal each time any key is pressed
anywhere. It holds which key is currently down so it can release the note, and
discards it. Nothing is written to disk, nothing is sent anywhere, and the
switch starts off every time the app launches. The
<a href="/keyj/privacy/">privacy page</a> says all of this in detail, including
how to check it rather than believe it.</p>

<h2>The key map</h2>
<p>The left rail lists every key and the note it plays, and <b>clicking a row rebinds
it</b>. Scale and octave sit underneath: pick a scale and the whole keyboard is
constrained to it, which makes playing something that sounds wrong difficult.</p>
"""


# Key-J installs a global keyboard hook. A product that does that owes
# its buyer a plain account of what it does with what it sees, and every
# app store requires one before it will list it.
KEYJ_PRIVACY = """
<h2>The short version</h2>
<p>Key-J does not collect anything. No account, no telemetry, no analytics, no
crash reports, no network calls of any kind while it runs. Nothing you type is
stored, and nothing leaves your machine.</p>
<p>That is worth stating in detail rather than in a sentence, because Key-J
installs a global keyboard hook, and you should not have to take that on
trust.</p>

<h2>What the desktop application can see</h2>
<p>With <b>Global Capture</b> switched on, Key-J receives a signal from the
operating system each time any key is pressed or released, in any application.
That is what makes it play while you type elsewhere, and there is no version of
that feature which sees less.</p>
<p>What it does with that signal is the part that matters:</p>
<table class="facts">
<tr><th>Held in memory</th><td>Which key is currently down, so the note can be
released when you let go. Discarded immediately after.</td></tr>
<tr><th>Written to disk</th><td>Nothing. No log, no history, no buffer of
keystrokes.</td></tr>
<tr><th>Sent anywhere</th><td>Nothing. The application makes no outbound network
requests.</td></tr>
</table>
<p><b>Global Capture starts switched off</b> every time the application launches,
and the header shows which state it is in: <b>Window only</b> or <b>Global</b>.
It is never enabled without you enabling it.</p>

<h2>Sequence mode does not need to know what you typed</h2>
<p>When a sequence is loaded, every key plays the next note of it, so which key
you pressed stops being information Key-J needs. The command line player takes
this further and never reads the key identity at all &mdash; it asks whether a
key went down and discards the rest. There is no keystroke buffer in it to
leak, subpoena or lose.</p>

<h2>What the browser version can see</h2>
<p>Only what you type into its own page. A web page cannot read keystrokes
outside itself; that is a boundary enforced by the browser, not a promise made
by us. Sequences and settings are kept in your browser's local storage on your
own machine.</p>

<h2>Files Key-J writes</h2>
<table class="facts">
<tr><th>Settings</th><td>Your tone, tuning and last-used tab, in the standard
per-user application data directory.</td></tr>
<tr><th>Exports</th><td>Only where you choose to save them.</td></tr>
</table>
<p>Uninstalling removes the application. Anything you exported is yours and stays
where you put it.</p>

<h2>Verifying this rather than believing it</h2>
<p>The Key-J source is published. It is not free to copy &mdash; see
<a href="https://github.com/vince-gonzalez/f-keys/blob/main/keyj/LICENSE">the
licence</a> &mdash; but it is readable precisely so that a program which installs
a keyboard hook can be audited by the people running it. The global hook lives in
<code>keyj/desktop/src/main.js</code>; the handler is a few lines long and you can
read every one of them.</p>
<p>You can also check from the outside: run Key-J with any network monitor and
watch it make no requests.</p>

<h2>Children</h2>
<p>Key-J is not directed at children under 13 and collects no information from
anyone, of any age.</p>

<h2>Changes and contact</h2>
<p>If this ever stops being true, this page changes before the behaviour does.
Questions: <a href="mailto:hello@f-keys.com">hello@f-keys.com</a>.</p>
<p class="sub">F-Keys Creative LLC &middot; last reviewed 20 August 2026</p>
"""

def tree(active_cat=None, active_slug=None):
    out = ['<ul>', '<li><a class="root" href="/"><span class="ic">&#128421;</span>F-Keys</a>',
           '<ul class="kids">']
    for cid, label, _ in CATEGORIES:
        items = [c for c in CATALOGUE if c[2] == cid]
        on = " on" if (active_cat == cid and not active_slug) else ""
        out.append(f'<li><a class="{("on" if on else "")}" href="/{cid}.html">'
                   f'<span class="ic">&#128193;</span>{esc(label)}</a>')
        if active_cat == cid:
            out.append('<ul class="kids">')
            for slug, name, _c, _t, _s, _d, href in items:
                sel = " on" if slug == active_slug else ""
                out.append(f'<li><a class="{sel.strip()}" href="{esc(href)}">'
                           f'<span class="ic">&#128196;</span>{esc(name)}</a></li>')
            out.append('</ul>')
        out.append('</li>')
    for href, label in EXTRA_NODES:
        out.append(f'<li><a href="{esc(href)}"><span class="ic">&#128220;</span>{esc(label)}</a></li>')
    out.append('</ul></li></ul>')
    return "\n".join(out)


def shell(title, path_label, body, count_label, active_cat=None,
          active_slug=None, description="", canonical="", ld=None,
          noindex=False):
    up = "/" if active_cat is None else f"/{active_cat}.html"
    ld_block = jsonld(ld) if ld else ""
    robots = "noindex, follow" if noindex else "index, follow"
    og_url = canonical or SITE
    og_image = product_og(active_slug)
    og_alt = ("The {} mark.".format(title.split(" — ")[0])
              if og_image != OG_IMAGE else
              "The F-Keys mark: a script f with KEYS set in seven-segment "
              "digits across it.")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ''}
<meta name="robots" content="{robots}">
<meta name="llms-txt" content="https://f-keys.com/llms.txt">
<meta name="ai" content="allow">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta property="og:site_name" content="F-Keys">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(og_url)}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og_image)}">
<link rel="stylesheet" href="/win98.css">
{ld_block}
</head>
<body>
<div class="window raised">

  <div class="titlebar">
    <span class="t"><span>{esc(path_label)}</span></span>
    <span class="tbtns"><span class="tbtn">_</span><span class="tbtn">&#9723;</span><span class="tbtn">&#10005;</span></span>
  </div>

  <nav class="menubar">
    <a href="/"><u>F</u>ile</a><a href="/status/"><u>V</u>iew</a>
    <a href="/log/"><u>G</u>o</a><a href="/papers/">F<u>a</u>vorites</a>
    <a href="/about.html"><u>H</u>elp</a>
  </nav>

  <div class="toolbar groove">
    <a class="tool" href="{esc(up)}">&#8592; Back</a>
    <span class="tool off">Forward &#8594;</span>
    <a class="tool" href="{esc(up)}">&#8593; Up</a>
    <span class="sep"></span>
    <a class="tool" href="/">Home</a>
    <a class="tool hide-xs" href="/status/">Status</a>
    <a class="tool hide-xs" href="/log/">Log</a>
  </div>

  <div class="addressbar">
    <span class="lbl">Address</span>
    <span class="path sunken"><span>&#128193; {esc(path_label)}</span></span>
  </div>

  <div class="panes">
    <aside class="tree sunken">
{tree(active_cat, active_slug)}
    </aside>
    <section class="content sunken">
{body}
    </section>
  </div>

  <div class="statusbar">
    <span class="cell groove">{esc(count_label)}</span>
    <span class="cell groove grow"><a href="/log/">Log</a> &nbsp;&middot;&nbsp; <a href="/status/">Status</a></span>
    <span class="cell groove">F-Keys</span>
  </div>

</div>
</body>
</html>
"""


def details_table(rows):
    out = ['<table class="details"><thead><tr>',
           '<th class="col-name">Name</th><th class="col-type">Type</th>',
           '<th class="col-status">Status</th><th>Description</th>',
           '</tr></thead><tbody>']
    for slug, name, cat, typ, (stext, scls), blurb, href in rows:
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        out.append(
            f'<tr><td><a class="row-name" href="{esc(href)}"{ext}>'
            f'<span class="ic">&#128196;</span>{esc(name)}</a></td>'
            f'<td class="col-type muted">{esc(typ)}</td>'
            f'<td class="col-status"><span class="st {scls}">{esc(stext)}</span></td>'
            f'<td class="muted">{esc(blurb)}</td></tr>')
    out.append('</tbody></table>')
    return "\n".join(out)


# schema.org wants a category from its own vocabulary rather than the
# word the catalogue uses in the Type column, so the two are mapped here
# instead of guessed at from the blurb.
APP_CATEGORY = {
    "keyj": "MultimediaApplication",
    "pixelstaff": "MultimediaApplication",
    "qv": "UtilitiesApplication",
    "micdrop": "GameApplication",
    "wikipolish": "UtilitiesApplication",
    "leadseer": "BusinessApplication",
    "plumhud": "UtilitiesApplication",
    "streamsniper": "MultimediaApplication",
    "moonbeam": "DeveloperApplication",
    "remapwrap": "UtilitiesApplication",
}


# ── what the page can actually support about price ───────────
# "price": "0" used to be hardcoded into every SoftwareApplication
# block: twenty-four machine-readable assertions that a thing is free,
# derived from nothing on the page. Google renders that as "Free" in a
# rich result, and trailer-load's own page says it is licensed
# separately to institutions while Key-J is proprietary.
#
# An Offer is only emitted when the page states a basis for it. Where
# there is none the block is left out - schema.org does not require an
# offer, and saying nothing is not a claim, whereas saying zero is.
OSS_LICENCES = ("mit", "apache", "bsd", "gpl", "mpl", "isc", "unlicense")


def free_basis(facts):
    """The fact that makes 'free' true, or None."""
    for key in ("Cost", "Price"):
        v = (facts.get(key) or "").lower()
        if "free" in v:
            return facts[key]
        if v and ("$" in v or "licen" in v or "paid" in v):
            return None                 # it states a price. Not free.
    lic = (facts.get("Licence") or facts.get("License") or "").lower()
    if any(x in lic for x in OSS_LICENCES):
        return facts.get("Licence") or facts.get("License")
    inst = (facts.get("Install") or "").lower()
    if inst.startswith("pip install") or inst.startswith("npm install"):
        return facts.get("Install")
    return None


def software(slug, page, row):
    """A product page, as the thing a parser is looking for.

    Every field is lifted from the facts table the page already shows, so
    the schema cannot claim a version or a licence the page contradicts.
    """
    facts = dict(page["facts"])
    obj = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": page["title"],
        "url": "{}/{}/".format(SITE, slug),
        "description": page["tagline"],
        "applicationCategory": APP_CATEGORY.get(slug, "UtilitiesApplication"),
        "image": product_og(slug),
        "author": {"@type": "Person", "name": FOUNDER, "sameAs": [ORCID]},
        "publisher": {"@id": SITE + "/#organization"},
    }
    basis = free_basis(facts)
    if basis:
        obj["offers"] = {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
        }
    if facts.get("Platforms"):
        obj["operatingSystem"] = facts["Platforms"]
    if facts.get("Version"):
        obj["softwareVersion"] = facts["Version"]
    if facts.get("Licence"):
        obj["license"] = facts["Licence"]
    return obj


def main():
    written = []

    # index: everything, grouped by category heading rows
    body = [counted(HOME_DOC), details_table(CATALOGUE)]
    written.append(("index.html", shell(
        "F-Keys — Hardware. Software. Ideas Brought to Life.",
        "F-Keys", "\n".join(body), f"{len(CATALOGUE)} object(s)",
        description="Independent hardware, software and internet products built by "
                    "Vincent Gonzalez. Apps, games, tools, hardware and research.",
        canonical="https://f-keys.com", ld=organization())))

    # one page per category
    for cid, label, hint in CATEGORIES:
        rows = [c for c in CATALOGUE if c[2] == cid]
        body = (f'<div class="doc" style="padding-bottom:6px"><h1>{esc(label)}</h1>'
                f'<p class="sub">{esc(hint)}</p></div>' + details_table(rows))
        written.append((f"{cid}.html", shell(
            f"{label} — F-Keys", f"F-Keys\\{label}", body,
            f"{len(rows)} object(s)", active_cat=cid,
            description=hint, canonical=f"https://f-keys.com/{cid}.html")))


    written.append(("about.html", shell(
        "About \u2014 F-Keys", "F-Keys\\About", counted(ABOUT_DOC), "1 item",
        description=counted(
            "F-Keys is Vince Gonzalez, working alone, with %%LIVE%% live "
            "products and more than thirty deposited works."),
        canonical="https://f-keys.com/about.html", ld=organization())))

    written.append(("contact.html", shell(
        "Contact \u2014 F-Keys", "F-Keys\\Contact", CONTACT_DOC, "1 item",
        description="Reach F-Keys Creative LLC: email, the Florida filing, the "
                    "principal address, and what is worth writing about.",
        canonical="https://f-keys.com/contact.html", ld=organization())))

    written.append(("developers.html", shell(
        "F-Keys Developer Resources \u2014 API, CLI, and published data",
        "F-Keys\\Developers",
        DEVELOPERS_DOC, "1 item",
        description="F-Keys developer resources: the OpenAPI description of "
                    "35 published datasets, the PyPI and npm packages, the "
                    "gonzalgo GitHub Action, llms.txt, and Markdown and JSON "
                    "content negotiation. No API keys, because there is no "
                    "hosted API.",
        canonical="https://f-keys.com/developers.html", ld=organization())))

    written.append(("privacy.html", shell(
        "Privacy \u2014 F-Keys", "F-Keys\\Privacy", PRIVACY_DOC, "1 item",
        description="No advertising, no analytics, no cookies and no accounts. "
                    "What the servers log anyway, and the one third-party request.",
        canonical="https://f-keys.com/privacy.html")))

    # GitHub Pages serves this file with a real 404 status. It is excluded
    # from the index because a soft 404 in search results is worse than no
    # result at all.
    written.append(("404.html", shell(
        "404 \u2014 F-Keys", "F-Keys\\Not found", NOT_FOUND_DOC, "0 objects",
        description="That page is not here. The sitemap, llms.txt and every "
                    "category page, so an agent can recover the path it wanted.",
        noindex=True)))

    # one document per product that has long-form detail
    for slug, page in PAGES.items():
        row = next((c for c in CATALOGUE if c[0] == slug), None)
        cat = row[2] if row else None
        facts = "".join(
            "<tr><th>{}</th><td>{}</td></tr>".format(esc(k), esc(v))
            for k, v in page["facts"])
        # The mark, when the product has one. Nothing is emitted when it
        # does not: a broken image or a placeholder box is worse than a
        # heading on its own, and twenty-one of these have no mark yet.
        mark = product_mark(slug)
        head = ('<img class="mark" src="{}" width="72" height="72" alt="" '
                'loading="lazy" decoding="async">').format(mark) if mark else ""

        # The screenshot carries a caption naming what it is a picture
        # of and when. An undated screenshot of a live site is a claim
        # with no expiry on it, and the reader cannot tell whether they
        # are looking at this morning or two years ago.
        shot = product_shot(slug)
        figure = ""
        if shot:
            where = dict(page["facts"]).get("Where", "")
            when = SHOT_DATES.get(slug, "")
            # The sizing is inline on purpose, not left to win98.css.
            # HTML and CSS deploy together and cache SEPARATELY: the
            # stylesheet carries max-age=14400, so for four hours every
            # returning visitor gets this new markup with the old
            # stylesheet. Without the inline rule they see an 800px
            # image clipped inside a 720px column. Anything load-bearing
            # for the layout of new markup cannot depend on new CSS.
            figure = (
                '<figure class="shot">'
                '<img src="{}" alt="{} running in a browser." '
                'width="800" style="max-width:100%;height:auto" '
                'loading="lazy" decoding="async">'
                '<figcaption>{}{}</figcaption></figure>').format(
                    shot, esc(page["title"]),
                    esc(where) if where else esc(page["title"]),
                    ", " + esc(when) if when else "")

        doc = ('<div class="doc">{}<h1>{}</h1><p class="sub">{}</p>'
               '<table class="facts">{}</table>{}{}</div>').format(
                   head, esc(page["title"]), esc(page["tagline"]),
                   facts, figure, page["body"])
        label = dict((c[0], c[1]) for c in CATEGORIES) if False else None
        catname = next((c[1] for c in CATEGORIES if c[0] == cat), "")
        written.append((os.path.join(slug, "index.html"), shell(
            page["title"] + " \u2014 F-Keys",
            "F-Keys\\{}\\{}".format(catname, page["title"]),
            doc, "1 item", active_cat=cat, active_slug=slug,
            description=page["tagline"],
            canonical="https://f-keys.com/{}/".format(slug),
            ld=software(slug, page, row))))

    written.append((os.path.join("keyj", "privacy", "index.html"), shell(
        "Key-J Privacy \u2014 F-Keys",
        "F-Keys\\Apps\\Key-J\\Privacy",
        '<div class="doc"><h1>Key-J Privacy</h1>'
        '<p class="sub">What a program with a global keyboard hook does '
        'with what it can see.</p>' + KEYJ_PRIVACY +
        '<div class="btnrow"><a class="btn default" href="/keyj/">Key-J</a>'
        '<a class="btn" href="/keyj/manual/">Manual</a></div></div>',
        "1 item", active_cat="apps", active_slug="keyj",
        description="Key-J collects nothing. What the global keyboard hook "
                    "sees, what is kept, and how to verify it.",
        canonical="https://f-keys.com/keyj/privacy/")))

    # the manual, one level under the Key-J document
    written.append((os.path.join("keyj", "manual", "index.html"), shell(
        "Key-J Manual \u2014 F-Keys",
        "F-Keys\\Apps\\Key-J\\Manual",
        '<div class="doc"><h1>Key-J Manual</h1>'
        '<p class="sub">What it does, how to switch it on, and what to check '
        'when it does not.</p>' + KEYJ_MANUAL +
        '<div class="btnrow"><a class="btn default" href="/keyj/app.html">'
        'Open Key-J</a><a class="btn" href="/keyj/">Product page</a></div></div>',
        "1 item", active_cat="apps", active_slug="keyj",
        description="How to use Key-J: sequence mode, tablature import, global "
                    "capture, and what to check when something is not working.",
        canonical="https://f-keys.com/keyj/manual/")))

    # A README per generated directory, and never over a real one.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import readme as house
    readmes = 0
    for slug, page in PAGES.items():
        target = os.path.join(ROOT, slug, "README.md")
        if not house.is_generated(target):
            continue                  # somebody wrote a real one. Leave it.
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(house.product_readme(
                slug, page["title"], page["tagline"], page["facts"]))
        readmes += 1

    for name, content in written:
        target = os.path.join(ROOT, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"buildsite: {len(written)} pages, {readmes} READMEs")
    for n, _ in written:
        print("  ", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
