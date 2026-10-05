"""Four targeted CVs from one fact base.

Maintaining four separate documents guarantees they diverge; a promotion or a
new deposit gets updated in one and not the others. Facts live once here and
each variant selects and orders them.

Dates are years only, everywhere.

All four pages are unlisted: noindex/nofollow/noarchive, absent from the
sitemap, linked from nothing. Contact details are redacted unless SHOW_CONTACT
is set, because an unlisted page is not a private one.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
import buildsite as B   # noqa: E402  the one window every page uses

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SITE = Path(__file__).resolve().parent
SHOW_CONTACT = False


def deposits() -> int:
    """Deposited works, read rather than typed.

    The figure was written out in four places in this file and all four had
    fallen behind the record. tools/snapshot.py counts the deposits against
    the Zenodo API; this reads that count, so the number is measured once and
    every page below quotes the same one.
    """
    snap = SITE / "status" / "latest.json"
    try:
        summary = json.loads(snap.read_text(encoding="utf-8"))["summary"]
        n = summary["zenodo_records"]
    except (OSError, ValueError, KeyError) as e:
        raise SystemExit(f"buildcv: no deposit count in {snap} ({e}); "
                         "run tools/snapshot.py first")
    if not isinstance(n, int) or n < 1:
        raise SystemExit(f"buildcv: deposit count in {snap} is {n!r}")
    return n


DEPOSITS = deposits()

NAME = "VINCE GONZALEZ"
LOC = "Punta Gorda, FL"
PHONE = "614.216.4709"
EMAIL = "vg188705@gmail.com"
LINKS = "f-keys.com · github.com/vince-gonzalez · orcid.org/0009-0005-3640-014X"

# ---------------------------------------------------------------- facts
FEDEX = [
    ("Operations Supervisor · Columbus, OH, then Punta Gorda, FL · "
     "2020–present", [
        "Supervise a sort operation of up to 30 people against a fixed "
        "dispatch time; own the written compliance record.",
        "Promoted to Operations Supervisor in May 2023. Lateral transfer to "
        "Punta Gorda in 2025.",
        "New hire facilitator for the outbound sort. Coach new hires into "
        "leadership pipelines and develop trainers.",
        "Manage linehaul, dispatch Express and Ground, and cover VSA duties as "
        "needed.",
        "Field package handler injuries by following protocol and providing "
        "post-injury guidance.",
        "Hub Certification FY25, the first in the history of COLO/432. Bravo "
        "Zulu 2025 · Purple Promise of the Month 2024.",
    ]),
]

EARLIER = [
    ("Spirits & Wine Sales · Ohio · 2014–2020", [
        "Ranked 15th of more than 400 representatives across 17 control "
        "states, carrying the Diageo and Moët Hennessy portfolios.",
        "Golden Bar 2016 and 2017 · Three-Year Consistency 2018, Ohio market.",
        "Scouted and executed Ohio's #2 Belvedere flagship program, 2017–2018.",
        "Managed 100+ on- and off-premise accounts, including 50+ wholesale "
        "B2B, and wrote the B2B communications and activation reports.",
        "Allocated a promotional budget on a company card; verified monthly "
        "and quarterly expense reports across multiple portfolios.",
        "Designed a formal request-documentation procedure at Giant Eagle's "
        "State Liquor Agency that Ohio later standardized statewide as its "
        "lottery system.",
        "Hosted consumer sampling events; produced event documentation and "
        "demographic reporting.",
    ]),
]

PRODUCTS = [
    ("OpticQuiz · opticquiz.com",
     "Color-vision accessibility platform. One engine. Machado 2009 "
     "simulation, Brettel 1997 cone projection, CIE ΔE2000 conflict detection, "
     "shipped across eight distribution channels with no duplicated logic: npm, "
     "PyPI, REST API, VS Code extension, Open VSX, Chrome MV3 extension and a "
     "GitHub Action. JavaScript and Python implementations verified "
     "byte-identical to six decimal places."),
    ("gonzalgo · f-keys.com/gonzalgo",
     "Axiom provenance for Lean 4 and Metamath. Separates a theorem's statement "
     "dependencies from its proof dependencies across a whole library and "
     "reports where an axiom is spent rather than inherited. On PyPI and "
     "Reservoir. Apache-2.0."),
    ("Trailer Load / LOCK IN · trailer-load.com",
     "A trailer-loading simulator built because he had loaded the trailers. "
     "Free for workers. Institutional licensing for schools and employers is "
     "priced and offered, with a pilot program and an instructor dashboard."),
    ("Also live",
     "poticas.com · 5best2buy.com · RemapWrap · TipStreams · DogeFundMe · "
     "PROMPT · QV. Full lifecycle solo across all properties: architecture, "
     "front and back end, database design, deployment, documentation, "
     "technical SEO."),
]

RESEARCH = [
    "Where Formal Libraries Spend Their Axioms. Axiom use measured across six "
    "libraries and two proof systems by one program. Located an avoidable "
    "classical dependency in Lean's `omega` and computed a 13.1% ceiling on "
    "removable classical dependence in Mathlib.",
    "Which Constant Is Responsible?. Dominator analysis over 766,564 constants "
    "showing that reachability overstates responsibility by 58×, and that 60.1% "
    "of classically dependent theorems have no responsible constant at all.",
    "Why Tactic-Level Rates Cannot Attribute Classical Dependencies. A negative "
    "methodological result with known-negative calibration across four libraries.",
    "Eligibility Discriminates Among Theorems and Not Among the Constants They "
    "Rest On. Where the statement/proof measure stops working, and why.",
    "A Procedural Method for Generating Pseudoisochromatic Plates. DOI "
    "10.5281/zenodo.21310578. Reported the tritan palette's ~53° off-axis "
    "deviation as a limitation rather than correcting it silently.",
    "Potica in America. Argues from community cookbooks, fraternal "
    "publications and bakery archives.",
    "Modulign / DAG-OR series. A dimensional address grammar for observable "
    "reality, including The Classification Deficit on Article 50 of the EU AI Act.",
]

WRITING = [
    "Writing samples, with the source of each one linked: "
    "f-keys.com/writing.",
    "Shift reports, compliance documentation, incident logs and contractor "
    "correspondence carrying legal and regulatory weight.",
    "SOP development and a state-adopted request-documentation procedure.",
    "User manuals and technical manuals; several hundred documented corporate "
    "training hours delivered across leadership development, orientation "
    "facilitation and dangerous goods handling.",
    "Academic writing in mathematics, philosophy and history, published with DOIs.",
    "Taxonomy and metadata design, Schema.org structured data, technical SEO and "
    "generative-engine optimization.",
    "Documentation for every property listed above, written as part of delivery "
    "rather than after it.",
]

TECH = [
    ("Languages", "JavaScript (ES5–ES2022), Python, C#/.NET, SQL, GLSL, HTML, CSS"),
    ("Backend", "Node.js, Supabase (PostgreSQL, RLS, auth, edge functions), REST "
                "APIs, JSON and CSV pipelines"),
    ("Infrastructure", "Git/GitHub, GitHub Actions, GitHub Pages, Cloudflare "
                       "(DNS, CDN, Pages, Workers, D1), Linux, Raspberry Pi, SSH"),
    ("AI & formal", "Local LLM deployment (Ollama, Open WebUI), prompt and "
                    "context engineering, evaluation pipelines, Lean 4 proof "
                    "auditing"),
    ("Frontend", "WCAG 2.1 AA, responsive design, progressive enhancement, "
                 "WebGL, Canvas 2D, Manifest V3 extensions, VS Code extension API"),
    ("Docs & search", "Technical SEO, Schema.org, SOP development, compliance "
                      "documentation, DOI publication"),
]

CERTS = [
    "First Aid / CPR. American Heart Association, current through 2028.",
    "Responsive Web Design and JavaScript. FreeCodeCamp, 2022.",
    "Google verified publisher · Microsoft verified publisher.",
    "Several hundred documented corporate training hours across leadership "
    "development, orientation facilitation and dangerous goods handling.",
]

EDU = ("Ohio University. BA Pre-Law Philosophy, Minor in History, 2012. "
       "Gateway Scholarship Award.")

# ---------------------------------------------------------------- variants
V = {
    "operations": dict(
        slug="operations",
        tag="Operations · quality and process",
        profile="Operations Supervisor at FedEx Ground since May 2023; "
                "Outbound, Sorter and Mentor from October 2020. Coaches "
                "entry-level teams and trainers. Wrote a "
                "request-documentation procedure adopted statewide in Ohio. "
                "Took a hub to a certification it had not previously held.",
        order=["fedex", "process", "earlier", "certs", "products_brief",
               "edu", "tech"]),
    "founder": dict(
        slug="founder",
        tag="Founder, F-Keys Creative LLC · systems and research",
        profile="Founder, F-Keys Creative LLC. Live products include an "
                "accessibility platform distributed across eight channels, an "
                "axiom-provenance tool for two proof assistants, and a "
                "trailer-loading simulator built from the floor he loaded "
                "trailers on. "
                "Architecture, both ends, database, deployment, documentation "
                "and technical SEO.",
        order=["products", "research_brief", "tech", "fedex_brief", "edu"]),
    "research": dict(
        slug="research",
        tag="Formal methods · measurement",
        profile="Formal verification, color science and epistemology. Built "
                "the tooling the measurements run on. Reports what the data "
                "does not support alongside what it does: a published "
                "limitation on an off-axis palette, a 58× gap between two "
                "plausible measures, and negative results published as "
                "negative results.",
        order=["research", "products_brief", "tech", "writing_brief", "edu",
               "fedex_brief"]),
    "writing": dict(
        slug="writing",
        tag="Technical writing · documentation",
        profile="Documentation that carries consequences: compliance records "
                "in a safety-intensive operation, a procedure adopted "
                "statewide, SOPs, user manuals, and academic work published "
                "with DOIs. Also builds the systems being documented.",
        order=["writing", "process", "research_brief", "tech", "fedex_brief",
               "certs", "edu"]),
}

# The PDF beside each page is the one he actually sends, built from the
# same .txt source by resume-kit/build_web_resumes.py, with the phone
# number and personal address swapped for f-keys.com/contact. These pages
# have always redacted contact details and publishing the originals here
# would have undone that quietly.
PDFS = {
    "founder":    ("VG-Resume-Master.pdf", "general"),
    "operations": ("VG-Resume-Sales.pdf", "sales and operations"),
    "research":   ("VG-Resume-Formal-Methods.pdf", "formal methods"),
    "writing":    ("VG-Resume-Writing.pdf", "writing"),
}

SECTION_TITLES = {
    "fedex": "Professional Experience",
    "fedex_brief": "Professional Experience",
    "process": "Selected Process & Quality Work",
    "earlier": "Earlier Experience",
    "certs": "Certifications & Recognition",
    "products": "Independent Products. F-Keys LLC",
    "products_brief": "Independent Products",
    "research": "Published Research",
    "research_brief": "Published Research",
    "writing": "Writing & Documentation",
    "writing_brief": "Writing & Documentation",
    "tech": "Technical",
    "edu": "Education",
}

PROCESS = [
    "**State-adopted procedure.** Designed a formal request-documentation "
    "procedure at Giant Eagle's State Liquor Agency that Ohio later "
    "standardized statewide as its lottery system.",
    "**Hub Certification.** First achieved in the history of COLO/432, FY25. A "
    "standard the hub had never previously met.",
    "**LOCK IN (trailer-load.com).** Turned trailer-loading rules that normally "
    "live as undocumented dock knowledge into a scored training simulator with "
    "logins, an institutional dashboard and a defined pilot program.",
    "**Technical and professional content.** User manuals, SOPs, academic "
    "writing in mathematics, philosophy and history, and full websites and "
    "applications.",
]


def md_section(key: str) -> list[str]:
    t = SECTION_TITLES[key]
    o = [f"## {t}", ""]
    if key == "fedex":
        o.append("**Federal Express Corporation** · 2020–present")
        o.append("")
        for head, bullets in FEDEX:
            o += [f"### {head}", ""] + [f"- {b}" for b in bullets] + [""]
    elif key == "fedex_brief":
        o.append("**Federal Express Corporation** · 2020–present")
        o.append("")
        o += ["- Operations Supervisor, Columbus OH then Punta Gorda FL. "
              "Supervise a sort operation of up to 30 people against a fixed "
              "dispatch time; own the written compliance record.",
              "- Promoted to Operations Supervisor in May 2023. New hire "
              "facilitator for the outbound sort.",
              "- Hub Certification first in the history of COLO/432, FY25. "
              "Bravo Zulu 2025, Purple Promise of the Month 2024.", ""]
    elif key == "process":
        o += [f"- {p}" for p in PROCESS] + [""]
    elif key == "earlier":
        for head, bullets in EARLIER:
            o += [f"### {head}", ""] + [f"- {b}" for b in bullets] + [""]
    elif key == "certs":
        o += [f"- {c}" for c in CERTS] + [""]
    elif key == "products":
        for head, body in PRODUCTS:
            o += [f"### {head}", "", body, ""]
    elif key == "products_brief":
        for head, body in PRODUCTS[:3]:
            o += [f"- **{head}**: {body.split('.')[0]}."]
        o += ["- **Also live**: " + PRODUCTS[3][1].split(".")[0] + ".", ""]
    elif key == "research":
        o += [f"{DEPOSITS} deposited works · ORCID 0009-0005-3640-014X · "
              "all open access", ""]
        o += [f"- {r}" for r in RESEARCH] + [""]
    elif key == "research_brief":
        o += [f"{DEPOSITS} deposited works · ORCID 0009-0005-3640-014X", ""]
        o += [f"- {r.split('. ')[0]}" for r in RESEARCH[:5]] + [""]
    elif key == "writing":
        o += [f"- {w}" for w in WRITING] + [""]
    elif key == "writing_brief":
        o += [f"- {w}" for w in WRITING[:3]] + [""]
    elif key == "tech":
        for label, body in TECH:
            o.append(f"- **{label}**: {body}")
        o.append("")
    elif key == "edu":
        o += [EDU, ""]
    return o


def build_md(cfg: dict) -> str:
    contact = (f"{LOC} · {PHONE} · {EMAIL}" if SHOW_CONTACT
               else f"{LOC} · contact on request")
    pdf, lane = PDFS[cfg["slug"]]
    out = [f"# {NAME}", "", cfg["tag"], "", contact, "", LINKS, "",
           f"[Download this as a PDF](/cv/{pdf}) · "
           f"[all four](/cv/) · [writing samples](/writing/)",
           "", "---", "", "## Profile", "", cfg["profile"], ""]
    for key in cfg["order"]:
        out += md_section(key)
    return "\n".join(out)


# ---------------------------------------------------------------- render
def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    # `<` must be excluded from the trailing run: bold has already been turned
    # into tags by this point, and a greedy match swallowed the closing
    # </strong> into the href on every product line.
    s = re.sub(r"\b((?:f-keys\.com|opticquiz\.com|trailer-load\.com|poticas\.com|"
               r"5best2buy\.com|github\.com/vince-gonzalez|orcid\.org/[\w-]+)[^\s·,)<]*)",
               r'<a href="https://\1">\1</a>', s)
    return s


CSS = """:root{--bg:#0a0e0a;--panel:#0f150f;--border:#1f351f;--green:#39ff14;
--text:#c3dcc3;--dim:#7d9c7d;--cyan:#00ffcc}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'Share Tech Mono',monospace;line-height:1.65}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:9000;
background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.07) 2px,rgba(0,0,0,.07) 4px)}
main{max-width:820px;margin:0 auto;padding:3rem 1.5rem 5rem}
h1{font-family:'VT323',monospace;font-size:clamp(34px,7vw,58px);color:var(--green);
letter-spacing:4px;line-height:1;text-shadow:0 0 20px rgba(57,255,20,.25)}
.tag{color:var(--cyan);margin:.25rem 0 .9rem}
.meta{color:var(--dim);font-size:.86rem}
h2{font-family:'VT323',monospace;font-size:1.55rem;color:var(--green);letter-spacing:1px;
margin:2.1rem 0 .6rem;display:flex;align-items:center;gap:.9rem}
h2::after{content:'';flex:1;height:1px;background:var(--border)}
h3{font-size:.98rem;color:var(--cyan);margin:1.1rem 0 .35rem;font-weight:400}
p{margin-bottom:.6rem;color:var(--dim)}
ul{margin:.3rem 0 .8rem 1.05rem}
li{margin-bottom:.34rem;color:var(--dim)}
li strong,p strong{color:var(--text);font-weight:400}
code{color:var(--cyan)}
a{color:var(--green)}
hr{border:0;border-top:1px solid var(--border);margin:1.4rem 0}
.note{border:1px solid var(--border);background:var(--panel);padding:.7rem .95rem;
font-size:.76rem;color:var(--dim);margin-bottom:1.8rem}
.switch{font-size:.78rem;color:var(--dim);margin-bottom:1.6rem}
.switch a{margin-right:.9rem}
footer{border-top:1px solid var(--border);margin-top:2.6rem;padding-top:1.2rem;
font-size:.8rem;color:var(--dim)}"""


def md_to_html(md: str) -> str:
    out, ul = [], False
    for line in md.splitlines():
        s = line.rstrip()
        if ul and not s.startswith("- "):
            out.append("</ul>")
            ul = False
        if not s.strip():
            continue
        if s.startswith("---"):
            out.append("<hr>")
        elif s.startswith("### "):
            out.append(f"<h3>{inline(s[4:])}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("# "):
            out.append(f"<h1>{inline(s[2:])}</h1>")
        elif s.startswith("- "):
            if not ul:
                out.append("<ul>")
                ul = True
            out.append(f"<li>{inline(s[2:])}</li>")
        else:
            out.append(f"<p>{inline(s)}</p>")
    if ul:
        out.append("</ul>")
    return "\n".join(out)


others = lambda cur: " ".join(
    f'<a href="/cv/{k}/">{k}</a>' for k in V if k != cur)

made = []
for key, cfg in V.items():
    md = build_md(cfg)
    body = md_to_html(md)
    # first three blocks become the header
    body = body.replace("<p>" + html.escape(cfg["tag"], quote=False) + "</p>",
                        f'<p class="tag">{html.escape(cfg["tag"])}</p>', 1)
    body = re.sub(r"<p>(Punta Gorda[^<]*)</p>", r'<p class="meta">\1</p>', body, 1)
    # A CV is a document, so it opens in the word processor like the
    # papers do, in the same window as everything else on the site.
    # The old template was a fourth visual identity of its own.
    #
    # The banner used to read "Not indexed, not in the sitemap, linked
    # from nowhere." Two thirds of that stopped being true when /cv/
    # got an index and the four pages were added to sitemap.xml, so it
    # now says only what is still the case.
    inner = f"""<div class="doc">
<div class="note">Unlisted: these are not indexed, and search engines are
asked not to follow them. Share the URL directly.</div>
{body}
<p class="switch">other versions: {others(key)}</p>
<footer>
  <a href="/">f-keys.com</a> &middot; <a href="/papers/">papers</a> &middot;
  <a href="/writing/">writing samples</a> &middot;
  <a href="/portfolio.html">work</a> &middot;
  <a href="https://orcid.org/0009-0005-3640-014X">ORCID</a>
</footer>
</div>"""
    page = B.shell(
        f"V. Gonzalez, {key} CV",
        f"CV\\{key}",
        inner,
        f"{len(md.split())} words",
        description=cfg["tag"],
        canonical=f"https://f-keys.com/cv/{key}/",
        noindex=True,
        app="wordpad")
    d = SITE / "cv" / key
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page, encoding="utf-8", newline="\n")
    (SITE / "cv" / f"{key}.md").write_text(md, encoding="utf-8", newline="\n")
    made.append((key, len(md.split()), len(page)))

# ── the front door ───────────────────────────────────────────
# All four were live with zero inbound links, absent from the sitemap,
# and /cv/ itself returned 404 - so nobody could reach a resume from the
# site and no crawler knew they existed. This is the index that fixes it.
_rows = "\n".join(
    f'<li><a href="/cv/{k}/"><b>{k}</b></a>: {V[k]["tag"]}'
    f' &middot; <a href="/cv/{PDFS[k][0]}">PDF, {PDFS[k][1]}</a></li>'
    for k in ("founder", "operations", "research", "writing"))

# The index opens in the file manager, because that is what it is: a
# list of four documents. The documents themselves open in the word
# processor. Same desktop either way.
_index = B.shell(
    "CV. V. Gonzalez",
    "F-Keys\\CV",
    """<div class="doc">
<h1>CV</h1>
<p class="sub">Four records, one per lane. Same facts, different emphasis.
Each has a PDF beside it with the contact line pointing at
<a href="/contact.html">f-keys.com/contact</a>.</p>
<ul class="cvlist">
""" + _rows + """
</ul>
<p>Writing samples, each linked to its source, are at
<a href="/writing/">/writing/</a>.</p>
</div>""",
    "4 records",
    description=("Four CVs, one per lane: founder, operations, research, "
                 "writing. PDF beside each."),
    canonical="https://f-keys.com/cv/")

(SITE / "cv" / "index.html").write_text(_index, encoding="utf-8", newline="\n")

print(f"{len(made)} variants + /cv/ index, contact {'SHOWN' if SHOW_CONTACT else 'redacted'}")
for k, w, b in made:
    print(f"  /cv/{k:<11} {w:>4} words   {b:>6,} bytes   {V[k]['tag']}")
