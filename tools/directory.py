# The f-keys.com directory: the homepage body, built from the directory map
# (fkeys-beatdown\DIRECTORY-MAP.md). buildsite.py wraps it in shell().
# Every row names a real piece of my work. A row without a link has no public home yet,
# so it shows its status and no link. I never point a row at a page I have not checked.
import html

GH = "https://github.com/vince-gonzalez/"

# status keys -> label shown on the chip
CHIP = {
    "live": "Live", "alpha": "Alpha", "paid": "For sale", "early": "Early orders",
    "coming": "Coming", "work": "Needs work", "spec": "Specced", "dev": "In development",
    "moving": "Moving here", "home": "Getting a page", "pkg": "Package", "pub": "Published",
    "merged": "Merged", "test": "In testing", "proto": "Prototype", "device": "Appliance",
}

# (wing id, F-key, title, one line, groups[(group title or "", compact?, rows)])
# row = (name, line, status, href or None)
WINGS = [
  ("services", "F1", "Services", "What you can buy today, and what it costs.", [
    ("", False, [
      ("Lotfile", "A Florida listing checked against the public record: permits, flood zone, sales, what is owed. Every fact sourced and dated. $29.99.", "paid", "https://lotfile.f-keys.com"),
      ("Websites", "A site built and kept running. Site $100 + $75 a month; one page $40 + $20 a month.", "paid", "/intake/"),
      ("Website audit", "A written report: what is broken on your site, what it costs you, what I would fix. $50, three business days.", "paid", "/audit/"),
      ("Authorecon reports", "One ORCID in, one document out: a published record checked against where the work lives. $1.99 / $9.99.", "paid", "https://authorecon.f-keys.com"),
      ("Epistemend reference checks", "Paste a bibliography: which references are real, which cannot be found, which were retracted. $5 / $25.", "paid", "https://epistemend.org"),
      ("Color palette check", "The written version of the free palette check, read by a person. $25.", "paid", "/shop/"),
      ("Trailer Load licence", "Warehouse load training for the institutions that teach it.", "paid", "https://trailer-load.com"),
      ("Security Check", "Security headers read against the OWASP standard, with the fix applied.", "early", "/securitycheck/"),
      ("Prompt Check", "A system prompt run against a live model: which rules hold, which break, and the rewrite.", "early", "/promptcheck/"),
      ("Custom engineering", "Quoted per job.", "paid", "/contact.html"),
      ("Pre-publish gate", "A check that runs before anything is published.", "coming", None),
    ]),
  ]),
  ("software", "F2", "Software", "Applications and the packages behind them.", [
    ("", False, [
      ("Key-J", "Every keystroke plays a note, in any application. Live staff, WAV export.", "live", "/keyj/"),
      ("Pixel Staff", "An 8-bit composer. Piano roll, waveform per channel, WAV or ringtone out.", "live", "/pixelstaff/"),
      ("RemapWrap", "Any smartphone becomes a programmable macro pad. No app, no dongle.", "alpha", "/remapwrap/"),
      ("QV", "Live ballots. Put a question to a room and watch the count move.", "live", "/qv/"),
      ("OpticQuiz", "Color-vision and acuity tests that run entirely in the browser.", "live", "https://opticquiz.com"),
      ("OpticQuiz Corrector", "The correction app, listed in the Windows package manager.", "live", "/opticquiz/"),
      ("Color tools for developers", "Fail a build when colors collapse for color-blind viewers: a CI check, a palette gate, two local servers.", "pkg", GH + "cvd-action"),
      ("coldHat", "Your rules on any chat. Type one line and the assistant works your way.", "live", "https://coldhat.f-keys.com"),
      ("WikiPolish", "Grammar scout for Wikipedia. Finds a first edit nobody will revert.", "live", "/wikipolish/"),
      ("Tip widget", "An embeddable tip QR. One script tag; nothing leaves the browser.", "pkg", "https://tipstreams.com/widget/"),
      ("keyjockey", "Guitar tablature to notes: eight tunings, capo offsets, MIDI and frequency.", "pkg", "/keyjockey/"),
      ("LeadSeer", "Finds the local businesses that still have no website.", "work", "/leadseer/"),
    ]),
  ]),
  ("hardware", "F3", "Hardware", "Devices, and the software that runs them.", [
    ("", False, [
      ("RemapWrap Bridge", "A small device that drives a computer with nothing installed on it.", "spec", None),
      ("Moonbeam miner", "ESP32 firmware, hardware design, web dashboard and a printable enclosure.", "live", GH + "Moonbeam-NerdMiner"),
      ("Moonbeam scanner", "Finds the miners on your network and reads their vitals.", "pkg", "/moonbeam/"),
      ("PlumHUD", "Miner fleet monitor. Overlay HUD, alerts and local history.", "pkg", "/plumhud/"),
      ("Stream Sniper", "A spare mini PC shows a channel fullscreen the moment it goes live.", "device", "/streamsniper/"),
    ]),
  ]),
  ("engineering", "F4", "Engineering", "Formal mathematics, measurement, and the checks this work ships through.", [
    ("Research tools", False, [
      ("gonzalgo", "Which axioms a Lean 4 or Metamath theorem spends rather than inherits. With the Kernel Index tables.", "pub", "/gonzalgo/"),
      ("mmforge", "Finds avoidable axiom dependencies in Metamath and builds the proofs that remove them.", "pkg", "/mmforge/"),
      ("axsent", "What a formal library assumes, measured from source: Rocq, Agda and Isabelle.", "pkg", "/axsent/"),
      ("rocqaxioms", "Source-only axiom readers that separate mathematical assumptions from interface obligations.", "pub", GH + "rocqaxioms"),
      ("mmrewrap", "Rewraps Metamath comments byte-exact, and names every case it refuses.", "pub", GH + "mmrewrap"),
      ("loadbearing", "What a claim asserts, separated from what its derivation consumed.", "pkg", "/loadbearing/"),
      ("certivl", "Certified interval arithmetic: an enclosure that turns a computed inequality into a proof.", "pkg", "/certivl/"),
      ("certified-covers", "Certified computation for the Lebesgue universal cover and related problems.", "pub", GH + "certified-covers"),
      ("plateaudit", "Measures color-vision plates from the stimulus a browser actually delivers.", "pub", GH + "plateaudit"),
      ("ishihara", "Generates color-vision plates, reproducible from a seed.", "pkg", "/ishihara/"),
      ("Modulign", "A dimensional address grammar for observable reality.", "pub", "https://modulign.org"),
      ("the-record", "Modulign's hash-chained legal ledger.", "pub", GH + "the-record"),
      ("Prompt Atoms", "Instruction atoms and measured conflicts mined from public prompt libraries. CC BY 4.0.", "pub", "/prompt-atoms/"),
      ("Independent US food makers", "Open datasets of independent makers, certifications recorded with their certifying body. CC BY 4.0.", "pub", "https://www.5best2buy.com/data/"),
    ]),
    ("Build checks", False, [
      ("a11yhat", "An open WCAG 2.2 accessibility machine.", "pub", GH + "a11yhat"),
      ("hardHats", "Crews of checkers, each an instruction or a deterministic gate.", "pub", GH + "hardhats"),
      ("legible", "Three build gates: unreadable type, unreadable color, a retired name.", "pkg", "/legible/"),
      ("contrast-gate", "Fails a build when a declared color cannot be read on its surface.", "pub", GH + "contrast-gate"),
      ("typefloor", "Fails a build when type is declared below a readable floor.", "pub", GH + "typefloor"),
      ("deadname-gate", "Fails a build when a name that should be gone reaches a reader.", "pub", GH + "deadname-gate"),
      ("openapi-drift", "Has your API drifted from its spec, and can a machine still read it?", "pkg", "/openapi-drift/"),
      ("changewatch", "A doorbell for your published work. Silent until somebody else acts.", "pkg", "/changewatch/"),
      ("authorecon", "Reconciles published work against every place it lives, for any ORCID.", "pkg", "/authorecon/"),
      ("promptcheck-action", "Prompt Check as a CI step.", "pub", GH + "promptcheck-action"),
    ]),
    ("Measurements", False, [
      ("d1bench", "Which Cloudflare D1 write strategy wins, and which limit stops you first.", "pub", "/d1bench/"),
      ("kv-bench", "Read-after-write and cross-region staleness for Cloudflare Workers KV.", "pub", GH + "kv-bench"),
      ("d1-replica-bench", "Cloudflare D1 read-replica lag, with a reproducible harness.", "pub", GH + "d1-replica-bench"),
      ("locationhint-bench", "Where each Durable Objects location hint actually lands.", "pub", GH + "locationhint-bench"),
    ]),
    ("Accepted by maintainers", False, [
      ("set.mm proofs", "Proofs merged into the Metamath set.mm library.", "merged", "/about.html"),
      ("metamath-exe fix", "A fix merged into the Metamath program.", "merged", "/about.html"),
      ("curl and Caddy websites", "Accessibility fixes merged into both projects' sites.", "merged", "/about.html"),
      ("Windows package manager", "Key-J and OpticQuiz Corrector listings.", "merged", "/about.html"),
      ("Documentation and lists", "Two documentation fixes, a data-science list, two server lists.", "merged", "/about.html"),
    ]),
    ("Published", False, [
      ("Papers", "Full text with DOIs, listed on ORCID.", "pub", "https://orcid.org/0009-0005-3640-014X"),
      ("OEIS A398262", "An integer sequence in the On-Line Encyclopedia.", "pub", "https://oeis.org/A398262"),
    ]),
  ]),
  ("sites", "F5", "Sites", "Standalone sites, built and operated.", [
    ("", False, [
      ("opticquiz.com", "Color-vision and acuity tests.", "live", "https://opticquiz.com"),
      ("5best2buy.com", "A sourcing map for independent American food.", "live", "https://www.5best2buy.com"),
      ("poticas.com", "The home of potica: history, method, and who still ships one.", "live", "https://poticas.com"),
      ("tipstreams.com", "Branded tip pages and stream overlays. The widget never touches money.", "live", "https://tipstreams.com"),
      ("dogefundme.com", "FunDoge: free isometric mini-golf in the browser.", "live", "https://dogefundme.com"),
      ("epistemend.org", "Reference checks for published papers.", "live", "https://epistemend.org"),
      ("modulign.org", "The Modulign standard.", "live", "https://modulign.org"),
      ("trailer-load.com", "Warehouse load training and LOCK IN.", "live", "https://trailer-load.com"),
      ("Lotfile", "House checks against the public record.", "live", "https://lotfile.f-keys.com"),
      ("sympolar.com", "Home checks and websites for Southwest Florida.", "coming", None),
    ]),
  ]),
  ("arcade", "F6", "Arcade", "Games. Each one gets its own page.", [
    ("Fortnite islands", True, [
      ("MicDrop", "1534-0440-5810", "live", "/micdrop/"),
      ("TAG", "8134-9047-4850", "live", "/tag/"),
      ("TAG PRO", "5571-1708-8987", "live", "/tagpro/"),
      ("Box Lacrosse", "", "test", None),
      ("Golf Kicks", "", "home", None),
      ("Barrel Hammer", "", "proto", None),
    ]),
    ("Discord", True, [
      ("PROMPT", "", "live", "https://prompt.f-keys.com"),
      ("DaisuPop", "", "live", "https://dp.f-keys.com"),
    ]),
    ("In the browser", True, [
      ("LOCK IN", "", "live", "https://trailer-load.com/lock-in.html"),
      ("FunDoge mini-golf", "", "live", "https://dogefundme.com/game.html"),
      ("Word Forge", "", "live", "https://vince-gonzalez.github.io/word-forge/"),
      ("Who Wants to Know a Million Brands?", "", "live", "https://www.5best2buy.com/game/"),
    ]),
    ("The Stables", True, [
      ("Steed Trek", "", "home", None),
      ("Off to the Races", "", "home", None),
      ("Knightfall", "", "home", None),
    ]),
    ("The arcade, moving here", True, [(n, "", "moving", None) for n in [
      "Zen Orbits", "Astro Trap", "Iron Serpent", "Zen Stonks", "Sk8 Tide", "Windsurf", "Wavy",
      "MotoPipe", "Mini Links", "FoosFriends", "Zen Strikers", "Knight Sprint", "Zen Travels",
      "Showdown Saloon"]]),
    ("Built, getting pages", True, [(n, "", "home", None) for n in [
      "Smalls Sort", "ForkLift", "Discord Craps", "Halls of History", "Asterisk Billiards",
      "RPS Revolution", "GlideFury", "Wiki-Clicker", "Vandalism Hunter", "Wiki-Ancestry",
      "Wiki-Liar", "Wiki-Battle", "Mini-Pool", "vchess", "Knight's Tour Dungeon Quest",
      "Chess Royale"]]),
    ("In development", True, [
      ("FyteCraft", "", "dev", GH + "fytecraft.com"),
      ("Bumper Blader", "", "dev", None),
      ("Pick-Pull", "", "dev", None),
      ("Nerdball", "", "dev", None),
    ]),
  ]),
  ("company", "F7", "Company", "F-Keys Creative LLC.", [
    ("", True, [
      ("Record", "", "live", "/about.html"),
      ("Capability statement", "", "coming", None),
      ("CV", "", "live", "/cv/"),
      ("Contact", "", "live", "/contact.html"),
      ("Status", "", "live", "/status/"),
      ("Log", "", "live", "/log/"),
      ("Developers", "", "live", "/developers.html"),
      ("Docs", "", "live", "/Docs.html"),
      ("Stack", "", "live", "/stack/"),
      ("Privacy", "", "live", "/privacy.html"),
    ]),
  ]),
]

e = html.escape


def chip(status):
    return '<span class="chip c-%s">%s</span>' % (status, CHIP[status])


def row(name, line, status, href, compact):
    ext = href and href.startswith("http")
    label = e(name)
    if href:
        rel = ' rel="noopener"' if ext else ""
        label = '<a href="%s"%s>%s</a>' % (e(href), rel, label)
    terms = e((name + " " + line + " " + CHIP[status]).lower())
    if compact:
        sub = ' <span class="code">%s</span>' % e(line) if line else ""
        return '<li class="pill" data-q="%s">%s%s %s</li>' % (terms, label, sub, chip(status))
    return ('<li class="item" data-q="%s"><div class="nm">%s</div>%s'
            '<p class="ln">%s</p></li>') % (terms, label, chip(status), e(line))


def wing(wid, key, title, line, groups):
    out = ['<section class="wing" id="%s" aria-labelledby="h-%s">' % (wid, wid),
           '<div class="wh"><span class="k" aria-hidden="true">%s</span>'
           '<h2 id="h-%s">%s</h2><p>%s</p></div>' % (key, wid, title, e(line))]
    for gtitle, compact, rows in groups:
        if gtitle:
            out.append('<h3>%s</h3>' % e(gtitle))
        cls = "pills" if compact else "grid"
        out.append('<ul class="%s">' % cls)
        out.extend(row(*r, compact=compact) for r in rows)
        out.append('</ul>')
    out.append('</section>')
    return "\n".join(out)


JS = """
(function(){var i=document.getElementById('q'),s=document.getElementById('said');
i.addEventListener('input',function(){var v=i.value.trim().toLowerCase(),any=false;
document.querySelectorAll('[data-q]').forEach(function(li){var m=!v||li.dataset.q.indexOf(v)>-1;li.hidden=!m;if(m)any=true});
document.querySelectorAll('.wing ul').forEach(function(u){var h=!u.querySelector('[data-q]:not([hidden])');u.hidden=h;
var p=u.previousElementSibling;if(p&&p.tagName==='H3')p.hidden=h});
document.querySelectorAll('.wing').forEach(function(w){w.hidden=!w.querySelector('ul:not([hidden])')});
s.textContent=!v?'':(any?'Showing matches for “'+i.value.trim()+'”.':'Nothing matches “'+i.value.trim()+'”.')});})();
"""

NL = chr(10)


def keys_nav():
    return "".join('<li><a href="#%s"><span>%s</span><b>%s</b></a></li>' % (w[0], w[1], w[2]) for w in WINGS)


def home_body():
    """The homepage: who the company is in one line, the wing keys, a
    search over every row, the mall's door, then every wing."""
    return """<div class="dir">
<div class="intro"><h1>Directory</h1>
<p class="lede">Software. Hardware. Engineering.</p>
<p>Everything F-Keys Creative has made, by wing: what is for sale, what is live, and what is still being built.</p></div>
<nav class="keys" aria-label="Wings"><ul>%s</ul></nav>
<div class="find" role="search"><label for="q">Find</label><input id="q" type="search" autocomplete="off" placeholder="a name, a tool, a status"></div>
<p id="said" aria-live="polite"></p>
<aside class="mall" aria-labelledby="h-mall"><div><h2 id="h-mall">The Mall</h2><p>The same directory as a place to walk through, with a shop for each wing. Works on a phone.</p></div><span class="door">OPENING SOON</span></aside>
%s
</div>
<script>%s</script>""" % (keys_nav(), NL.join(wing(*w) for w in WINGS), JS)


def rows():
    return sum(len(g[2]) for w in WINGS for g in w[4])
