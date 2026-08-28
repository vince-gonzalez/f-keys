#!/usr/bin/env python3
"""
============================================================
shots - a picture of the thing actually running
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Twenty-six product pages and not one image of any product
working. Every page was prose describing software, which is
the format least able to prove that software exists.

A mark says a product has an identity. A screenshot says
somebody can go and use it. Those are different claims, and
the second is the one a client is actually asking about.

HOW IT CAPTURES
Headless Chrome, which is already on this machine. No pip
install, no npm install, no browser downloaded into anyone's
environment - the flag has been in Chrome for a decade and it
writes a PNG.

WHAT IT WILL NOT DO
Capture in CI. The runner has no Chrome, the sites are on the
public internet, and a build that fails because somebody
else's DNS blinked is a build nobody trusts. --verify only
checks what was already captured.

It also refuses to record a capture of an error page. A
screenshot of a 502 is a valid PNG of the right size and
passes every check a file can pass, right up until a person
reads it - and by then it is on the product page.

WORKFLOW STACK
  1. SHOTS      - slug -> the URL that shows the product
  2. capture    - headless Chrome, one PNG per product
  3. derive     - an 800px copy for the page
  4. --verify   - every recorded shot is still on disk (CI)
  5. --report   - what has no picture yet

Run:  python tools/shots.py                 (capture all)
      python tools/shots.py opticquiz qv    (capture some)
      python tools/shots.py --report
      python tools/shots.py --verify
============================================================
"""

import io
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "assets", "products")
MANIFEST = os.path.join(ART, "shots.json")

WIDTH, HEIGHT = 1280, 800
THUMB = 800

# The URL that shows the product doing its job. Not the repository and
# not a marketing page - the thing running. A product with no such URL
# is absent from this map rather than pointed at something that would
# make a reader feel lied to.
SHOTS = {
    "opticquiz":    "https://opticquiz.com",
    "trailer-load": "https://trailer-load.com",
    "modulign":     "https://modulign.org",
    "5best2buy":    "https://www.5best2buy.com",
    "poticas":      "https://poticas.com",
    "tipstreams":   "https://tipstreams.com",
    "fundoge":      "https://dogefundme.com",
    "qv":           "https://qv.f-keys.com",
    "keyj":         "https://f-keys.com/keyj/app.html",
}

CHROMES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_chrome():
    for p in CHROMES:
        if os.path.exists(p):
            return p
    return None


def load():
    if not os.path.exists(MANIFEST):
        return {}
    try:
        with io.open(MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    except ValueError:
        return {}


def looks_like_a_failure(path):
    """Is this a picture of the product, or a picture of an error?

    A capture of a 502 is a valid PNG of the right size and passes every
    check a file can pass. The cheapest tell is that error pages and
    failed loads are nearly blank - almost one colour, edge to edge.
    """
    from PIL import Image
    im = Image.open(path).convert("RGB")
    small = im.resize((64, 64))
    colours = small.getcolors(64 * 64) or []
    if not colours:
        return None
    top = max(colours)[0]
    if top / float(64 * 64) > 0.97:
        return "97% one colour - an error page or a load that never finished"
    return None


def capture(slug, url, chrome):
    out = os.path.join(ART, slug + "-shot.png")
    # The temp name has to END in .png. Chrome silently refuses to write
    # --screenshot to any other extension, so a ".part" suffix produced
    # nine identical "is the site up?" failures against nine sites that
    # were all up.
    tmp = os.path.join(ART, "_capturing-" + slug + ".png")
    cmd = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
           "--force-device-scale-factor=1",
           "--window-size={},{}".format(WIDTH, HEIGHT),
           "--virtual-time-budget=9000",
           "--screenshot=" + tmp.replace("\\", "/"), url]
    try:
        subprocess.run(cmd, timeout=90, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except (subprocess.TimeoutExpired, OSError) as e:
        return None, "chrome failed: %s" % e
    if not os.path.exists(tmp):
        return None, "chrome wrote nothing (is the site up?)"

    bad = looks_like_a_failure(tmp)
    if bad:
        os.remove(tmp)
        return None, bad

    if os.path.exists(out):
        os.remove(out)
    os.rename(tmp, out)

    from PIL import Image
    im = Image.open(out).convert("RGB")
    w, h = im.size
    thumb = os.path.join(ART, slug + "-shot-800.png")
    im.resize((THUMB, int(h * THUMB / float(w))), Image.LANCZOS).save(
        thumb, "PNG", optimize=True)
    return [out, thumb], None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    report = "--report" in sys.argv
    verify = "--verify" in sys.argv
    state = load()

    if verify:
        problems = []
        for slug, rec in sorted(state.items()):
            for suffix in ("-shot.png", "-shot-800.png"):
                if not os.path.exists(os.path.join(ART, slug + suffix)):
                    problems.append("%s: %s%s was recorded and is not here"
                                    % (slug, slug, suffix))
            if rec.get("url") != SHOTS.get(slug):
                problems.append("%s: captured %s, the map now says %s"
                                % (slug, rec.get("url"), SHOTS.get(slug)))
        for p in problems:
            print("  shots: " + p)
        print("shots: %s" % ("%d FAILED" % len(problems) if problems
                             else "ok - %d captured" % len(state)))
        return 1 if problems else 0

    if report:
        print()
        print("  %d of %d products with a live URL have a screenshot"
              % (len(state), len(SHOTS)))
        for slug in sorted(SHOTS):
            print("   %-14s %-34s %s" % (
                slug, SHOTS[slug],
                state.get(slug, {}).get("captured", "NOT CAPTURED")))
        return 0

    chrome = find_chrome()
    if not chrome:
        print("shots: no Chrome or Edge found. Looked in:")
        for p in CHROMES:
            print("   " + p)
        return 2

    import datetime
    todo = args or sorted(SHOTS)
    ok = 0
    for slug in todo:
        if slug not in SHOTS:
            print("  %-14s no URL in SHOTS - skipped" % slug)
            continue
        written, err = capture(slug, SHOTS[slug], chrome)
        if err:
            print("  %-14s REFUSED: %s" % (slug, err))
            continue
        state[slug] = {
            "url": SHOTS[slug],
            "captured": datetime.date.today().isoformat(),
            "size": "%dx%d" % (WIDTH, HEIGHT),
        }
        ok += 1
        print("  %-14s %s -> %d files" % (slug, SHOTS[slug], len(written)))

    with io.open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=1, sort_keys=True)
    print()
    print("shots: %d captured, %d of %d products with a URL have one"
          % (ok, len(state), len(SHOTS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
