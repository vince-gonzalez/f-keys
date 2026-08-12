"""Render the submitted resume into an unlisted page in the site theme.

Unlisted means noindex/nofollow/noarchive, absent from the sitemap, and linked
from nothing. The URL works when handed out; nothing finds it otherwise.

SOURCE is the variant to publish. Four exist and they are targeted at different
roles, so this is a deliberate choice rather than "the newest file wins".

Two gates before anything is written: bracketed placeholders, and personal
contact details. An unlisted page is not a private one -- noindex asks crawlers
not to index, it does not stop anyone who has the URL and it does not stop
scrapers. Contact lines are therefore redacted unless SHOW_CONTACT is set.
"""
from __future__ import annotations

import html
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCE = Path(r"C:\Users\Admin\Downloads\VinceGonzalez.docx")
SHOW_CONTACT = False          # set True to publish phone and personal email
OUT = Path(__file__).resolve().parent / "cv" / "index.html"

PHONE = re.compile(r"\b\d{3}[.\-\s]\d{3}[.\-\s]\d{4}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")


def paragraphs(p: Path) -> list[tuple[str, str]]:
    """(style, text) per paragraph."""
    xml = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8", "replace")
    out = []
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        style = ""
        m = re.search(r'<w:pStyle w:val="([^"]+)"', para)
        if m:
            style = m.group(1)
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, re.S))
        for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                     ("&quot;", '"'), ("&apos;", "'")):
            t = t.replace(a, b)
        t = re.sub(r"\s+", " ", t).strip()
        if t and not t.startswith("<w:"):
            out.append((style, t))
    return out


ps = paragraphs(SOURCE)
full = " ".join(t for _, t in ps)

holes = sorted(set(re.findall(r"\[[A-Za-z][^\]]{2,}\]", full)))
if holes:
    print(f"placeholders in {SOURCE.name} — nothing written: {holes}")
    sys.exit(1)

redacted = 0
body = []
for i, (style, t) in enumerate(ps):
    if not SHOW_CONTACT and (PHONE.search(t) or EMAIL.search(t)):
        t2 = PHONE.sub("[phone on request]", t)
        t2 = EMAIL.sub("[email on request]", t2)
        if t2 != t:
            redacted += 1
        t = t2
    e = html.escape(t, quote=False)
    e = re.sub(r"\b((?:f-keys\.com|github\.com/\S+|orcid\.org/\S+|opticquiz\.com|trailer-load\.com)[^\s·]*)",
               r'<a href="https://\1">\1</a>', e)
    if i == 0:
        body.append(f"<h1>{e}</h1>")
    elif i == 1:
        body.append(f'<p class="tagline">{e}</p>')
    elif style.startswith("Heading1") or (len(t) < 46 and t == t.title()
                                          and not t.startswith("–")):
        body.append(f"<h2>{e}</h2>")
    elif t.startswith("–") or t.startswith("-"):
        body.append(f'<p class="item">{e}</p>')
    else:
        body.append(f"<p>{e}</p>")

CSS = """:root{--bg:#0a0e0a;--panel:#0f150f;--border:#1f351f;--green:#39ff14;
--text:#c3dcc3;--dim:#7d9c7d;--cyan:#00ffcc}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'Share Tech Mono',monospace;line-height:1.65}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:9000;
background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.07) 2px,rgba(0,0,0,.07) 4px)}
main{max-width:800px;margin:0 auto;padding:3.5rem 1.5rem 5rem}
h1{font-family:'VT323',monospace;font-size:clamp(36px,7vw,62px);color:var(--green);
letter-spacing:4px;line-height:1;text-shadow:0 0 20px rgba(57,255,20,.25)}
.tagline{color:var(--cyan);margin:.3rem 0 1.4rem;font-size:.95rem}
h2{font-family:'VT323',monospace;font-size:1.6rem;color:var(--green);letter-spacing:1px;
margin:2.2rem 0 .7rem;display:flex;align-items:center;gap:.9rem}
h2::after{content:'';flex:1;height:1px;background:var(--border)}
p{margin-bottom:.6rem;color:var(--dim)}
p.item{padding-left:1rem;border-left:1px solid var(--border);margin-bottom:.75rem}
a{color:var(--green)}
.note{border:1px solid var(--border);background:var(--panel);padding:.75rem 1rem;
font-size:.78rem;color:var(--dim);margin-bottom:2rem}
footer{border-top:1px solid var(--border);margin-top:3rem;padding-top:1.3rem;
font-size:.8rem;color:var(--dim)}"""

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<meta name="googlebot" content="noindex, nofollow">
<title>V. Gonzalez — CV</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<main>
<div class="note">Unlisted — not indexed, not in the sitemap, linked from nowhere.
Share the URL directly.</div>
{chr(10).join(body)}
<footer>
  <a href="/">f-keys.com</a> · <a href="/papers/">papers</a> ·
  <a href="/portfolio.html">work</a> ·
  <a href="https://orcid.org/0009-0005-3640-014X">ORCID</a>
</footer>
</main>
</body>
</html>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8", newline="\n")
print(f"wrote {OUT}  ({len(page):,} bytes) from {SOURCE.name}")
print(f"  {len(ps)} paragraphs · {redacted} contact line(s) redacted "
      f"(SHOW_CONTACT={SHOW_CONTACT})")
print("  noindex/nofollow/noarchive · not in sitemap · not linked from nav")
