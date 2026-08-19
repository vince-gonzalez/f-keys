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

# Entry index (1-based, document order) -> group key.
GROUP_OF = {
    1: 'axioms', 2: 'axioms', 3: 'axioms', 4: 'axioms',
    5: 'geometry', 6: 'geometry', 7: 'geometry', 8: 'geometry',
    9: 'geometry', 10: 'geometry', 11: 'geometry',
    12: 'epistem', 13: 'epistem', 14: 'epistem', 17: 'epistem',
    15: 'standard', 16: 'standard', 26: 'standard',
    27: 'standard', 29: 'standard', 32: 'standard',
    18: 'evidence', 20: 'evidence', 22: 'evidence',
    25: 'evidence', 30: 'evidence', 31: 'evidence',
    19: 'protocol', 21: 'protocol', 23: 'protocol',
    33: 'colour', 34: 'colour',
    35: 'food',
    24: 'docs', 28: 'docs', 36: 'docs',
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
        key = GROUP_OF.get(i)
        if key is None:
            unassigned.append(i)
        else:
            buckets[key].append(html)
    if unassigned:
        print('ERROR: entries with no group: %s' % unassigned)
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
        out.append('<h2 id="%s">%s <span style="color:var(--dim);font-size:1rem;">(%d)</span></h2>'
                   % (gid, head, len(items)))
        out.append('<p class="group-note">%s</p>' % blurb)
        out.extend(items)
        out.append('')

    body = '\n'.join(out)

    # splice between <main> and </main>
    new = re.sub(r'(<main>)[\s\S]*?(</main>)',
                 lambda m: m.group(1) + '\n\n' + body + '\n' + m.group(2),
                 s, count=1)

    # CSS: entry titles are h3 now; add the group note style
    new = new.replace('.entry h2 { margin:0 0 .3rem; font-size:1.5rem; }',
                      '.entry h3 { font-family:\'VT323\',monospace; font-weight:400; color:var(--green);\n'
                      '            letter-spacing:1px; margin:0 0 .3rem; font-size:1.5rem; }')
    new = new.replace('.entry h2 a { text-decoration:none; }',
                      '.entry h3 a { text-decoration:none; color:var(--green); }\n'
                      '.group-note { color:var(--dim); font-size:.9rem; margin:0 0 .4rem; }')

    io.open(SRC, 'w', encoding='utf-8').write(new)

    print('rebuilt %s' % SRC)
    print('  papers: %d   project documents: %d   with DOI: %d' % (paper_count, doc_count, doi_count))
    for _, gid, head, _ in GROUPS:
        print('  %-38s %d' % (head, len(buckets[gid])))
    print('  %-38s %d' % (DOCS[2], doc_count))
    return 0


if __name__ == '__main__':
    sys.exit(main())
