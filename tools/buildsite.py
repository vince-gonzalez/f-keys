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
     "Any smartphone becomes a programmable macro pad. No app, no dongle.", "/remapwrap"),

    ("trailer-load", "Trailer Load", "games", "Simulator", READY,
     "Warehouse load training that plays like a game. Institutional licensing.", "https://trailer-load.com"),
    ("prompt", "PROMPT", "games", "Discord activity", DISCORD,
     "A multiplayer word game inside Discord, in a 90s CRT shell.", "https://prompt.f-keys.com"),
    ("daisupop", "DaisuPop", "games", "Discord activity", DISCORD,
     "A dice popper. Everyone in the room sees the same roll at the same moment.", "https://dp.f-keys.com"),
    ("micdrop", "MICDROP", "games", "Fortnite island", FORTNITE,
     "A live open-mic arena. 120 seconds to win the crowd. Code 1534-0440-5810.", "/micdrop/"),
    ("fytecraft", "FyteCraft", "games", "Game", ALPHA,
     "An RTS built around combat rather than base-building. Early, and openly so.", "https://github.com/zengineco/fytecraft.com"),

    ("wikipolish", "WikiPolish", "tools", "Web tool", READY,
     "Grammar scout for Wikipedia. Finds a first edit nobody will revert.", "/wikipolish/"),
    ("leadseer", "LeadSeer", "tools", "Desktop tool", SETUP,
     "Finds the local businesses that still have no website.", "/leadseer/"),
    ("plumhud", "PlumHUD", "tools", "Python package", PIP,
     "Miner fleet monitor. Overlay HUD, alerts, and local history.", "/plumhud/"),

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

EXTRA_NODES = [("/log/", "Log"), ("/status/", "Status"), ("/papers/", "Papers")]


def esc(s):
    return html.escape(str(s), quote=True)


# ── the shell ────────────────────────────────────────────────
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
          active_slug=None, description="", canonical=""):
    up = "/" if active_cat is None else f"/{active_cat}.html"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ''}
<meta name="robots" content="index, follow">
<meta name="llms-txt" content="https://f-keys.com/llms.txt">
<meta name="ai" content="allow">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="/win98.css">
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
    <a href="/#about"><u>H</u>elp</a>
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


def main():
    written = []

    # index: everything, grouped by category heading rows
    body = [details_table(CATALOGUE)]
    written.append(("index.html", shell(
        "F-Keys — Hardware. Software. Ideas Brought to Life.",
        "F-Keys", "\n".join(body), f"{len(CATALOGUE)} object(s)",
        description="Independent hardware, software and internet products built by "
                    "Vincent Gonzalez. Apps, games, tools, hardware and research.",
        canonical="https://f-keys.com")))

    # one page per category
    for cid, label, hint in CATEGORIES:
        rows = [c for c in CATALOGUE if c[2] == cid]
        body = (f'<div class="doc" style="padding-bottom:6px"><h1>{esc(label)}</h1>'
                f'<p class="sub">{esc(hint)}</p></div>' + details_table(rows))
        written.append((f"{cid}.html", shell(
            f"{label} — F-Keys", f"F-Keys\\{label}", body,
            f"{len(rows)} object(s)", active_cat=cid,
            description=hint, canonical=f"https://f-keys.com/{cid}.html")))

    for name, content in written:
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(content)

    print(f"buildsite: {len(written)} pages")
    for n, _ in written:
        print("  ", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
