# The f-keys.com front page. One idea: every claim rests on something, and
# each product here shows what. Everything else is one click in, at /directory/.
#
# Every example on this page is real. The house rows come from the Lotfile
# sample report for parcel 114523C1017300120 (owner removed, listing entry
# marked as a sample); the proof row is the published omega finding
# (10.5281/zenodo.21769846); the bibliography scene shows Epistemend's three
# outcomes with no invented reference in it.
import html

e = html.escape

# (tab id, tab label, panel title, rows, footnote)
# row = (what, claimed, found, verdict key, source)
SCENES = [
    ("house", "House", "A listing, against the public record", [
        ("Bedrooms", "3", "3", "match", "county parcel record"),
        ("Year built", "2005", "2005", "match", "county parcel record"),
        ("Living area", "2,000 sq ft", "1,594 sq ft heated", "mismatch", "property record card"),
        ("Open permits", "none stated", "A/C change-out, issued 02/24/2026", "open", "city permit records"),
    ], "Sample report, Lee County. Owner removed; records read 10/30/2026."),
    ("papers", "Papers", "A bibliography, against the literature", [
        ("Reference", "cited", "found, as cited", "match", "the publisher's record"),
        ("Reference", "cited", "no record anywhere", "missing", "every index searched"),
        ("Reference", "cited", "retracted", "retracted", "the retraction notice"),
    ], "The three answers an Epistemend check gives, shown without a real bibliography."),
    ("proofs", "Proofs", "A theorem, against what it spends", [
        ("omega, Lean 4", "an arithmetic tactic", "spends a classical axiom", "mismatch", "measured from source"),
        ("That dependency", "taken as given", "avoidable", "found", "the published measurement"),
    ], "Published 2026-08-10, DOI 10.5281/zenodo.21769846."),
]

VERDICT = {"match": "MATCH", "mismatch": "MISMATCH", "open": "OPEN", "missing": "NOT FOUND",
           "retracted": "RETRACTED", "found": "FOUND"}

CHECKS = [
    ("House", "Lotfile", "Before you make an offer.",
     "The listing, line by line, against the public record: permits, flood zone, sales, "
     "what is owed. Charlotte, Lee and Sarasota (North Port) counties.",
     "$29.99 a report", "https://lotfile.f-keys.com", "Check a house"),
    ("Papers", "Epistemend", "Before you submit.",
     "Paste a bibliography. Find out which references are real, which cannot be found, "
     "and which were retracted, with a corrected list back.",
     "From $5", "/shop/", "Check references"),
    ("Proofs", "gonzalgo", "Before you build on a theorem.",
     "Which axioms a Lean 4 or Metamath result spends rather than inherits, measured "
     "from the source and published with the data.",
     "Open source", "/gonzalgo/", "Read the method"),
]

MERGED = [
    ("curl", "Alt text for the project's home page, merged 2026-11-02."),
    ("Caddy", "Alt text and a language attribute for the web server's site, merged 2026-11-04."),
    ("Metamath", "Proofs that remove avoidable uses of the axiom of choice, merged into set.mm."),
    ("metamath-exe", "A memory-layout fix in the reference proof verifier, merged 2026-10-24."),
]


def scene(sid, label, title, rows, foot, first):
    out = ['<div class="sc" id="sc-%s" role="tabpanel" aria-labelledby="tab-%s"%s>'
           % (sid, sid, "" if first else " data-later")]
    out.append('<p class="sc-t">%s</p>' % e(title))
    out.append('<ol class="trace">')
    for i, (what, claimed, found, v, src) in enumerate(rows):
        out.append(
            '<li style="--i:%d"><span class="w">%s</span>'
            '<span class="c"><i>claimed</i> %s</span>'
            '<span class="f"><i>record</i> %s</span>'
            '<span class="s">%s</span>'
            '<b class="v v-%s">%s</b></li>'
            % (i, e(what), e(claimed), e(found), e(src), v, VERDICT[v]))
    out.append('</ol><p class="sc-f">%s</p></div>' % e(foot))
    return "".join(out)


def instrument():
    tabs = "".join(
        '<button type="button" role="tab" id="tab-%s" aria-controls="sc-%s" aria-selected="%s">%s</button>'
        % (s[0], s[0], "true" if i == 0 else "false", e(s[1])) for i, s in enumerate(SCENES))
    scenes = "".join(scene(*s, first=(i == 0)) for i, s in enumerate(SCENES))
    return ('<div class="inst" aria-label="Three checks, as they read">'
            '<div class="inst-bar"><span class="dot" aria-hidden="true"></span>'
            '<span class="inst-n">PROVENANCE CHECK</span>'
            '<div class="tabs" role="tablist">%s</div></div>%s</div>' % (tabs, scenes))


def checks():
    out = []
    for kind, name, when, what, price, href, cta in CHECKS:
        rel = ' rel="noopener"' if href.startswith("http") else ""
        out.append(
            '<article class="ck"><p class="ck-k">%s</p><h3>%s</h3><p class="ck-w">%s</p>'
            '<p>%s</p><p class="ck-p">%s</p><a class="ck-a" href="%s"%s>%s</a></article>'
            % (e(kind), e(name), e(when), e(what), e(price), e(href), rel, e(cta)))
    return "".join(out)


def merged():
    return "".join('<li><b>%s</b> %s</li>' % (e(n), e(t)) for n, t in MERGED)


JS = """
(function(){var tabs=[].slice.call(document.querySelectorAll('.inst [role=tab]'));
if(!tabs.length)return;var root=document.querySelector('.inst');root.classList.add('js');
var cur=0,timer=null,calm=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function show(n){cur=n;tabs.forEach(function(t,i){var on=i===n;t.setAttribute('aria-selected',on?'true':'false');
t.tabIndex=on?0:-1;var p=document.getElementById(t.getAttribute('aria-controls'));p.hidden=!on;
if(on){p.classList.remove('run');void p.offsetWidth;p.classList.add('run')}})}
function next(){show((cur+1)%tabs.length)}
function go(){if(!calm&&!timer)timer=setInterval(next,7000)}function stop(){clearInterval(timer);timer=null}
tabs.forEach(function(t,i){t.addEventListener('click',function(){stop();show(i)});
t.addEventListener('keydown',function(ev){if(ev.key==='ArrowRight'||ev.key==='ArrowLeft'){stop();
var n=(i+(ev.key==='ArrowRight'?1:tabs.length-1))%tabs.length;show(n);tabs[n].focus()}})});
root.addEventListener('mouseenter',stop);root.addEventListener('focusin',stop);
show(0);go();})();
"""


def home_body():
    return """<div class="land">
<section class="hero">
  <div class="hero-copy">
    <h1 class="eyebrow">F-Keys Creative · Punta Gorda, Florida</h1>
    <p class="big">What does it actually rest&nbsp;on?</p>
    <p class="lede">Every claim comes from somewhere. F-Keys Creative builds the tools that trace it back: a home listing to the county record, a bibliography to the papers it cites, a proof to the axioms it spends. Every answer names its source and the date it was read.</p>
    <p class="ctas"><a class="go" href="https://lotfile.f-keys.com" rel="noopener">Check a house</a><a class="go2" href="/directory/">Browse the work</a></p>
  </div>
  %s
</section>

<section class="three" aria-labelledby="h-three">
  <h2 id="h-three">Three checks, one habit</h2>
  <div class="cks">%s</div>
</section>

<section class="kept" aria-labelledby="h-kept">
  <div>
    <h2 id="h-kept">The same habit, in other people's code</h2>
    <p>Fixes sent to projects the world depends on, reviewed and merged by the people who maintain them.</p>
  </div>
  <ul class="merged">%s</ul>
  <p class="more"><a href="/about.html">The full record, with every link</a></p>
</section>

<section class="reg" aria-labelledby="h-reg">
  <h2 id="h-reg">Registered to do the work</h2>
  <dl>
    <div><dt>Company</dt><dd>F-Keys Creative LLC, Florida</dd></div>
    <div><dt>Federal registration</dt><dd>SAM.gov active, all awards</dd></div>
    <div><dt>UEI</dt><dd>VX5TBUJSHAS5</dd></div>
    <div><dt>CAGE</dt><dd>25Y16</dd></div>
    <div><dt>Primary NAICS</dt><dd>541511, custom computer programming</dd></div>
    <div><dt>Size</dt><dd>Small business</dd></div>
  </dl>
  <p class="more"><a href="/contact.html">Ask for the capability statement</a></p>
</section>

<section class="door" aria-labelledby="h-door">
  <h2 id="h-door">Everything else is one door in</h2>
  <p>The software, the hardware, the research tools and the games, every one with its status, in the directory.</p>
  <p class="ctas"><a class="go" href="/directory/">Open the directory</a><span class="soon">The Mall · opening soon</span></p>
</section>
</div>
<script>%s</script>""" % (instrument(), checks(), merged(), JS)
