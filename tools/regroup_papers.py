# -*- coding: utf-8 -*-
"""
Restructure papers/index.html.

Two problems this fixes:
  1. Every paper title was an <h2> -- the same level as the group headers -- so
     the page had no real hierarchy. A crawler or screen reader saw one flat
     list of 40 sibling headings. Titles are now <h3> under their group's <h2>.
  2. The taxonomy was lopsided: 11 / 3 / 18 / 3, with Modulign alone holding
     half the page and "Applied work" acting as a junk drawer. Now 8 groups,
     none larger than seven, and the three project documents are pulled out of
     the paper count.

Idempotent: rebuilds the whole main block from the parsed entries each run.
"""
from __future__ import print_function
import io, re, sys, collections

SRC = 'papers/index.html'

# Paper slug -> group key.
#
# Keyed on the slug, NOT on document position: this script REORDERS the page,
# so a position-keyed map reassigns every paper to the wrong group on the
# second run. Slugs are stable across rebuilds.
GROUP_OF = {
    'eligibility-discriminates-among-theorems-not-among': 'axioms',
    'which-constant-responsible-dominator-analysis-classical': 'axioms',
    'why-tactic-level-rates-cannot-attribute': 'axioms',
    'where-formal-libraries-spend-their-axioms': 'axioms',

    'certified-upper-bounds-fejes-t-th': 'geometry',
    'maximality-added-vector-codes-cohn-li': 'geometry',
    'rigorous-areas-classical-lebesgue-universal-covering': 'geometry',
    'certified-opaque-barrier-unit-disc-length': 'geometry',
    'machine-checked-proof-opacity-faber-mycielski': 'geometry',
    'added-vector-code-odd-sign-construction': 'geometry',
    'first-return-walks-vertex-transitive-graphs': 'geometry',

    'competitive-context-jailbreak-accelerant-inter-model': 'epistem',
    'record-formal-epistemology-journalistic-attestation': 'epistem',
    'structural-dissolution-gettier-problem-address-theoretic': 'epistem',
    'epistemology-observation-formal-certification-framework-human': 'epistem',

    'federated-classification-infrastructure-registry-governance-node': 'standard',
    'modulign-architecture-implementation-applications-dimensional-address': 'standard',
    'dimensional-address-rigid-designation-dag-or': 'standard',
    'modulign-standard-automated-classifier-certification-framework': 'standard',
    'modulign-standard-dimensional-address-grammar-observable': 'standard',
    'formal-logic-modulign': 'standard',

    'human-attestation-protocol-confrontation-clause-compliance': 'evidence',
    'ai-generated-evidence-admissibility-formal-classification': 'evidence',
    'chain-custody-formalisation-digital-forensics-modulign': 'evidence',
    'classification-deficit-article-50-eu-ai': 'evidence',
    'modulign-evidence': 'evidence',
    'synthetic-content-epistemic-category': 'evidence',

    'modulign-correction-protocol-formal-specification-append': 'protocol',
    'architecture-epistemic-enforcement-empirical-implementation-universal': 'protocol',
    'inter-rater-reliability-automated-modulign-standard': 'protocol',

    'pseudoisochromatic-plate-design-type-recoverable-from': 'colour',
    'procedural-method-generating-pseudoisochromatic-plates-browser': 'colour',

    'potica-america-naming-transmission-printed-record': 'food',

    'version-3-1-amendment-document': 'docs',
    'public-commitment-document': 'docs',
    'MEASUREMENTS': 'docs',          # the gonzalgo pointer, no paper link
}

# Ordered: (key, anchor id, heading, one-line description)
GROUPS = [
    ('axioms', 'axioms', 'Axiom dependence in formal libraries',
     'What classical assumptions formal libraries actually rest on, and which constant is responsible.'),
    ('geometry', 'geometry', 'Certified bounds in discrete geometry',
     'Machine-checked upper and lower bounds for covering, packing and opacity problems.'),
    ('epistem', 'epistem', 'Epistemology',
     'Formal accounts of knowledge, attestation and testimony.'),
    ('standard', 'standard', 'The Modulign standard',
     'The dimensional address grammar itself: architecture, formal logic and certification.'),
    ('evidence', 'evidence', 'Modulign in evidence and law',
     'Applying the standard to admissibility, chain of custody and regulatory classification.'),
    ('protocol', 'protocol', 'Modulign validation and protocol',
     'Measuring and correcting the standard in practice.'),
    ('colour', 'colour', 'Colour vision and accessibility',
     'Pseudoisochromatic plate design, generation and recovery.'),
    ('food', 'food', 'Food history and diaspora',
     'Naming and transmission in the printed record.'),
]

DOCS = ('docs', 'docs', 'Project documents',
        'Amendments, commitments and continuously updated measurements. Not papers.')


# <details>/<summary>: no JavaScript needed to open and close, keyboard and
# screen-reader accessible by default, and collapsed content is still indexed.
# Collapsed, the nine summaries ARE the category tiles.
ENTRY_TITLE_CSS = (".entry h3 { font-family:'VT323',monospace; font-weight:400; color:var(--green);\n"
                   "            letter-spacing:1px; margin:0 0 .3rem; font-size:1.5rem; }")

ACCORDION_CSS = """.entry h3 a { text-decoration:none; color:var(--green); }

/* ---- collapsible groups ---- */
details.group { border:1px solid var(--border); background:#0d120d;
                margin:1rem 0; padding:0 1.1rem; }
details.group[open] { background:transparent; }
details.group > summary {
  cursor:pointer; list-style:none; padding:1.1rem 0; margin:0;
  display:block; position:relative;
}
details.group > summary::-webkit-details-marker { display:none; }
details.group > summary::after {
  content:'+'; position:absolute; right:.1rem; top:.9rem;
  font-family:'VT323',monospace; font-weight:400; font-size:2rem;
  color:var(--cyan); line-height:1;
}
details.group[open] > summary::after { content:'\\2212'; }
details.group > summary:focus-visible { outline:2px solid var(--cyan); outline-offset:3px; }
details.group > summary h2 {
  display:inline; margin:0; border:0; padding:0;
  font-size:1.9rem; letter-spacing:2px;
}
details.group > summary .count {
  color:var(--dim); font-size:1rem; font-family:'Share Tech Mono',monospace;
  margin-left:.5rem;
}
.group-note { color:var(--dim); font-size:.9rem; margin:.35rem 2.2rem .1rem 0; }
details.group > .entry:first-of-type { border-top:1px solid var(--border); }
details.group > .entry:last-of-type { padding-bottom:1.4rem; }
"""

ACCORDION_JS = """<script>
// Open a collapsed group when it is linked to, so the contents list and any
// shared #anchor still land the reader on an expanded section.
(function () {
  function openTargetGroup() {
    var id = location.hash.slice(1);
    if (!id) return;
    var el = document.getElementById(id);
    if (!el) return;
    if (el.tagName === 'DETAILS') el.open = true;
    var d = el.closest ? el.closest('details') : null;
    if (d) d.open = true;
    el.scrollIntoView();
  }
  window.addEventListener('hashchange', openTargetGroup);
  openTargetGroup();
})();
</script>"""


def main():
    s = io.open(SRC, encoding='utf-8').read()

    entries = re.findall(r'<div class="entry">[\s\S]*?</div>', s)
    if len(entries) != 36:
        print('ERROR: expected 36 entries, found %d. Aborting -- the file changed.' % len(entries))
        return 1

    # Titles become h3 so the group heading is their parent.
    entries = [e.replace('<h2>', '<h3>').replace('</h2>', '</h3>') for e in entries]

    buckets = collections.OrderedDict((g[0], []) for g in GROUPS)
    buckets[DOCS[0]] = []
    unassigned = []
    for i, html in enumerate(entries, 1):
        m = re.search(r'href="/papers/([^/"]+)/?"', html)
        slug = m.group(1) if m else 'MEASUREMENTS'
        key = GROUP_OF.get(slug)
        if key is None:
            unassigned.append('#%d %s' % (i, slug))
        else:
            buckets[key].append(html)
    if unassigned:
        print('ERROR: entries with no group (add them to GROUP_OF):')
        for u in unassigned:
            print('   ', u)
        return 1

    paper_count = sum(len(buckets[g[0]]) for g in GROUPS)
    doc_count = len(buckets[DOCS[0]])
    doi_count = sum(1 for e in entries if 'doi.org' in e)

    # ---- table of contents ----
    toc = ' &middot; '.join(
        '<a href="#%s">%s</a>' % (gid, head) for _, gid, head, _ in GROUPS)

    # ---- body ----
    out = []
    out.append('<h1>Papers</h1>')
    out.append('<p class="kicker">%d papers &middot; %d project documents</p>' % (paper_count, doc_count))
    out.append('')
    out.append('<p>Everything below is open access and %d of the %d carry a DOI. Full '
               'texts are served from this domain; the rest resolve to Zenodo. Ordered '
               'most recent first within each group.</p>' % (doi_count, len(entries)))
    out.append('')
    out.append('<p>Vince Gonzalez &middot;\n'
               '<a href="https://orcid.org/0009-0005-3640-014X">ORCID 0009-0005-3640-014X</a> &middot;\n'
               'tooling at <a href="/gonzalgo/">gonzalgo</a></p>')
    out.append('')
    out.append('<p class="meta">%s</p>' % toc)
    out.append('')

    for key, gid, head, blurb in GROUPS + [DOCS]:
        items = buckets[key]
        if not items:
            continue
        out.append('<details class="group" id="%s"%s>' % (gid, ' open' if key == GROUPS[0][0] else ''))
        out.append('  <summary>')
        out.append('    <h2>%s <span class="count">%d</span></h2>' % (head, len(items)))
        out.append('    <p class="group-note">%s</p>' % blurb)
        out.append('  </summary>')
        out.extend('  ' + line for line in items)
        out.append('</details>')
        out.append('')

    body = '\n'.join(out)

    # splice between <main> and </main>
    new = re.sub(r'(<main>)[\s\S]*?(</main>)',
                 lambda m: m.group(1) + '\n\n' + body + '\n' + m.group(2),
                 s, count=1)

    # CSS. Must work on the ORIGINAL file (entry titles were h2) and on this
    # script's own previous output (already h3) -- otherwise a second run
    # silently drops the styles.
    new = new.replace('.entry h2 { margin:0 0 .3rem; font-size:1.5rem; }', ENTRY_TITLE_CSS)
    if 'font-family:\'VT323\',monospace; font-weight:400; color:var(--green);\n            letter-spacing' not in new:
        new = re.sub(r'\.entry h3 \{[^}]*\}', ENTRY_TITLE_CSS, new, count=1)

    # Everything from the title-link rule through the group note is ours to own.
    # Skip if already injected -- ACCORDION_CSS opens with a rule the regex
    # would otherwise match again, duplicating the whole block each run.
    if 'details.group' not in new:
        new = re.sub(r'\.entry h[23] a \{[^}]*\}(\s*\.group-note \{[^}]*\})?',
                     lambda m: ACCORDION_CSS.rstrip(), new, count=1)
    if 'details.group' not in new:
        print('ERROR: could not inject accordion CSS -- the stylesheet changed.')
        return 1

    # Open a collapsed group when it is the anchor target, so the contents
    # links (and any shared #anchor) still land on an expanded section.
    if 'openTargetGroup' not in new:
        new = new.replace('</body>', ACCORDION_JS + '\n</body>')

    io.open(SRC, 'w', encoding='utf-8').write(new)

    print('rebuilt %s' % SRC)
    print('  papers: %d   project documents: %d   with DOI: %d' % (paper_count, doc_count, doi_count))
    for _, gid, head, _ in GROUPS:
        print('  %-38s %d' % (head, len(buckets[gid])))
    print('  %-38s %d' % (DOCS[2], doc_count))
    return 0


if __name__ == '__main__':
    sys.exit(main())
