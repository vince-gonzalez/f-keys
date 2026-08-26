#!/usr/bin/env python3
"""
============================================================
productart - one mark per product, everything else derived
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Three products had a mark and they were in three places for
three reasons: an Electron build icon, a folder of web assets,
and data packaged inside a Python wheel. All correct, none of
them the mark for a product PAGE, and nineteen products had
nothing at all.

So there is one place a mark is DROPPED and one place each
derivative is WRITTEN, and nobody has to remember a size.

  assets/products/<slug>.png     <- you put this here
  assets/products/<slug>-512.png <- generated
  assets/products/<slug>-256.png <- generated
  assets/products/<slug>-64.png  <- generated
  assets/products/<slug>.ico     <- generated
  assets/products/<slug>-og.png  <- generated, 1200x630

The source is never edited by this tool and never overwritten.
Drop a better one in and rerun; the derivatives are rebuilt.

The og card is the point. Twenty-two products currently share
one share image, so twenty-two links unfurl identically.

WORKFLOW STACK
  1. slugs()    - the catalogue is the list, not a hard-coded one
  2. derive()   - the five sizes, from the one source
  3. --report   - what is still missing, by name
  4. --verify   - every derivative matches its source (CI)

Run:  python tools/productart.py            (build what exists)
      python tools/productart.py --report   (what is missing)
      python tools/productart.py --verify   (CI)
============================================================
"""

import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "assets", "products")
MANIFEST = os.path.join(ART, "sources.json")

SIZES = (512, 256, 64)
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (256, 256)]
OG = (1200, 630)
MIN_SOURCE = 256          # smaller than this and 512 is an upscale

BG = (0, 0, 0)
INK = (255, 255, 255)


def catalogue():
    import buildsite
    return [(slug, name) for slug, name, *_rest in buildsite.CATALOGUE]


# One mark, several products. epistemend.png is the authorecon family's
# mark, so anything in that family draws on it rather than waiting for a
# drawing of its own that would only have to match. Recorded here rather
# than by copying the file, because two copies of one mark is two things
# to update and one of them gets missed.
ALIASES = {
    "authorecon": "epistemend",
    "epistemend": "epistemend",
}


def source_for(slug):
    """Whatever was dropped in, in whichever of the sane formats."""
    for candidate in (slug, ALIASES.get(slug)):
        if not candidate:
            continue
        for ext in (".png", ".webp", ".jpg", ".jpeg"):
            path = os.path.join(ART, candidate + ext)
            if os.path.exists(path):
                return path
    return None


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def derive(slug, source, name):
    from PIL import Image
    im = Image.open(source).convert("RGBA")
    if min(im.size) < MIN_SOURCE:
        return None, "source is {}x{}; needs at least {}px square".format(
            im.size[0], im.size[1], MIN_SOURCE)
    if im.size[0] != im.size[1]:
        return None, "source is {}x{}; a mark has to be square".format(*im.size)

    written = []
    for px in SIZES:
        out = os.path.join(ART, "{}-{}.png".format(slug, px))
        im.resize((px, px), Image.LANCZOS).save(out, "PNG", optimize=True)
        written.append(out)

    ico = os.path.join(ART, slug + ".ico")
    im.resize((256, 256), Image.LANCZOS).save(ico, "ICO", sizes=ICO_SIZES)
    written.append(ico)

    written.append(og_card(slug, im, name))
    return written, None


TODO = os.path.join(ART, "todo")


def why_unusable(path):
    """The reason, or None if the file is fine."""
    from PIL import Image
    try:
        w, h = Image.open(path).size
    except Exception as e:                      # noqa: BLE001
        return "cannot be opened: %s" % e
    # Order matters. A 220x229 image is not square AND is under the
    # floor, and telling someone only to crop it square sends them back
    # with a 220x220 that is still refused.
    if w != h and min(w, h) < MIN_SOURCE:
        return ("%dx%d - needs a square crop AND a bigger source; "
                "cropping this gives %dpx, under the %dpx floor"
                % (w, h, min(w, h), MIN_SOURCE))
    if w != h:
        return "%dx%d - needs a square crop" % (w, h)
    if min(w, h) < MIN_SOURCE:
        return "%dx%d - square, but under the %dpx floor" % (w, h, MIN_SOURCE)
    return None


def slug_of(filename):
    """The product a dropped file is for, allowing for how files arrive.

    Windows renames a file that collides on copy, so a fixed mark comes
    back as 'pixelstaff (2).png'. That slug is in no catalogue, so the
    file would be treated as somebody else's stray and ignored forever
    - the one failure mode worse than a loud refusal.
    """
    import re
    stem = os.path.splitext(filename)[0]
    return re.sub(r"\s*\(\d+\)$", "", stem).strip()


def promote_fixed(slugs):
    """Take anything in todo/ that is now usable back upstairs.

    The README told people to fix a file and move it up. They fix it
    where it is, which is the reasonable thing to do, and then nothing
    happens and the tool looks broken. Meeting that halfway costs
    nothing and removes the only step that was ever manual.
    """
    if not os.path.isdir(TODO):
        return []
    moved = []
    for f in sorted(os.listdir(TODO)):
        if not f.lower().endswith((".png", ".webp", ".jpg", ".jpeg")):
            continue
        here = os.path.join(TODO, f)
        slug = slug_of(f)
        if slug not in slugs or why_unusable(here):
            continue
        dest = os.path.join(ART, slug + os.path.splitext(f)[1].lower())
        if os.path.exists(dest):
            os.remove(dest)
        os.rename(here, dest)
        moved.append((f, os.path.basename(dest)))
    return moved


def park(slug, source):
    """Move a source that cannot be used out of the way.

    It is not deleted and it is not left where it was. Left in place it
    fails the build for everybody until somebody re-crops it, and a gate
    that blocks unrelated work is a gate somebody switches off.
    """
    if not os.path.isdir(TODO):
        os.makedirs(TODO)
    dest = os.path.join(TODO, os.path.basename(source))
    if os.path.exists(dest):
        os.remove(dest)
    os.rename(source, dest)
    return dest


def write_todo(names):
    """Rebuild the worklist from what is actually parked.

    The first version of this file was a table written by hand. Within
    an hour it listed a crop that had already been fixed, which is the
    failure mode of every hand-kept list: it is right once.
    """
    if not os.path.isdir(TODO):
        return
    rows = []
    for f in sorted(os.listdir(TODO)):
        if not f.lower().endswith((".png", ".webp", ".jpg", ".jpeg")):
            continue
        slug = os.path.splitext(f)[0]
        # Superseded: a usable source for this slug now sits upstairs.
        up = source_for(slug)
        if up and not why_unusable(up):
            os.remove(os.path.join(TODO, f))
            print("  {:<14} replaced upstairs - removed the parked copy"
                  .format(slug))
            continue
        rows.append((f, why_unusable(os.path.join(TODO, f)) or "unknown",
                     names.get(slug)))

    lines = ["# Marks that are not marks yet", "",
             "Generated by `tools/productart.py`. Do not edit - it is",
             "rewritten from what is actually in this directory, because a",
             "hand-kept list of things to fix is right exactly once.", "",
             "A mark has to be **square** and at least **%dpx**. Not"
             % MIN_SOURCE,
             "fussiness: the smallest derivative is a 32px favicon, and a",
             "1900x828 banner squeezed into 32x32 is a smear. These are",
             "banner and screenshot crops, which is a different picture",
             "with a different job.", ""]
    if rows:
        lines += ["| file | problem | product |", "|---|---|---|"]
        for f, why, name in rows:
            lines.append("| `%s` | %s | %s |"
                         % (f, why, name or "**not in the catalogue**"))
        lines += ["", "Fix one **in place** and run the tool. It takes anything",
                  "here that has become usable back upstairs by itself, so",
                  "there is nothing to move and nothing to rename - a file",
                  "that came back as `name (2).png` is matched too.", "",
                  "    python tools/productart.py", ""]
    else:
        lines += ["Nothing is parked. Every dropped-in source is usable.", ""]
    io.open(os.path.join(TODO, "README.md"), "w",
            encoding="utf-8", newline="\n").write("\n".join(lines))


def og_card(slug, mark, name):
    """The share card. Same construction as the company card so a product
    link and an F-Keys link look like they came from the same place."""
    from PIL import Image, ImageDraw, ImageFont
    card = Image.new("RGB", OG, BG)
    side = 470
    art = mark.resize((side, side), Image.LANCZOS)
    card.paste(art, (72, (OG[1] - side) // 2), art)

    d = ImageDraw.Draw(card)
    x = 72 + side + 56
    d.text((x, 250), name, font=_font(84, True), fill=INK)
    d.text((x, 372), "f-keys.com", font=_font(26), fill=(150, 150, 150))
    d.line([(x, 430), (OG[0] - 72, 430)], fill=(60, 60, 60), width=2)

    out = os.path.join(ART, slug + "-og.png")
    card.save(out, "PNG", optimize=True)
    return out


def _font(size, bold=False):
    from PIL import ImageFont
    names = ("tahomabd.ttf", "segoeuib.ttf", "arialbd.ttf") if bold else \
            ("tahoma.ttf", "segoeui.ttf", "arial.ttf")
    for n in names:
        p = os.path.join("C:\\", "Windows", "Fonts", n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def load_manifest():
    if os.path.exists(MANIFEST):
        try:
            with io.open(MANIFEST, encoding="utf-8") as f:
                return json.load(f)
        except ValueError:
            pass
    return {}


def main():
    os.makedirs(ART, exist_ok=True)
    report = "--report" in sys.argv
    verify = "--verify" in sys.argv

    have, missing, problems = [], [], []
    manifest = {}
    old = load_manifest()

    # Anything parked that has since been fixed comes back up first, so
    # the loop below sees it as an ordinary source. --verify never moves
    # anything: a check that edits the tree is not a check.
    if not verify:
        for was, now in promote_fixed(set(s for s, _ in catalogue())):
            print("  {:<14} fixed - {} -> {}".format(
                slug_of(was), was, now))

    for slug, name in catalogue():
        source = source_for(slug)
        if not source:
            missing.append((slug, name))
            continue

        stamp = digest(source)
        manifest[slug] = {"source": os.path.basename(source), "sha256": stamp}

        if report:
            have.append((slug, name))
            continue

        if verify:
            if old.get(slug, {}).get("sha256") != stamp:
                problems.append("{}: derivatives are stale for {}".format(
                    slug, os.path.basename(source)))
            for suffix in ["-512.png", "-256.png", "-64.png", ".ico", "-og.png"]:
                if not os.path.exists(os.path.join(ART, slug + suffix)):
                    problems.append("{}: missing {}{}".format(slug, slug, suffix))
            have.append((slug, name))
            continue

        written, err = derive(slug, source, name)
        if err:
            dest = park(slug, source)
            print("  {:<14} {} -> parked: {}".format(
                slug, os.path.basename(source), err))
            problems.append("{}: {} (moved to {})".format(
                slug, err, os.path.relpath(dest, ROOT).replace("\\", "/")))
            # A parked source is still a product without a mark. Dropping
            # it from the count entirely would shrink the denominator and
            # quietly improve the score for failing.
            missing.append((slug, name))
            continue
        have.append((slug, name))
        print("  {:<14} {} -> {} files".format(
            slug, os.path.basename(source), len(written)))

    if not report and not verify:
        with io.open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        write_todo(dict(catalogue()))

    total = len(have) + len(missing)
    print()
    print("  {} of {} products have a mark".format(len(have), total))

    if missing and (report or not verify):
        print()
        print("  STILL NEEDED - drop each one at assets/products/<name>:")
        for slug, name in missing:
            print("     assets/products/{}.png      ({})".format(slug, name))

    for p in problems:
        print("  productart:", p)

    if verify:
        print("productart: ok" if not problems else
              "productart: {} FAILED".format(len(problems)))
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
