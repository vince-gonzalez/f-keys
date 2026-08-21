#!/usr/bin/env python3
"""
============================================================
ogimage - generates the share card and favicons
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Every page carried og:title and og:description and no
og:image, so a link to f-keys.com unfurled as a grey box.
The mark already exists as one square PNG; the card, the
favicon and the apple touch icon are all derivable from it,
so they are derived rather than hand-cut and re-cut every
time the mark changes.

WORKFLOW STACK
  1. SOURCE   - assets/fkeys-logo.png, the square mark
  2. card()   - 1200x630 OG card, mark left, wordmark right
  3. icons()  - favicon.ico (16/32/48) + apple-touch-icon
  4. main()   - writes them, then reports the sizes

Run:  python tools/ogimage.py
      python tools/ogimage.py --verify
============================================================
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
SOURCE = os.path.join(ASSETS, "fkeys-logo.png")

OG = os.path.join(ASSETS, "og.png")
ICO = os.path.join(ROOT, "favicon.ico")
TOUCH = os.path.join(ASSETS, "apple-touch-icon.png")

OG_SIZE = (1200, 630)
INK = (255, 255, 255)
DIM = (150, 150, 150)
BG = (0, 0, 0)
FLOOR = 8               # luminance at or below this is plate, not glyph

WORDMARK = "F-KEYS"
LINE = "Hardware. Software. Ideas Brought to Life."
FOOT = "f-keys.com"


def font(size, bold=False):
    """Tahoma is the face the site itself is set in."""
    for name in (("tahomabd.ttf", "segoeuib.ttf", "arialbd.ttf") if bold
                 else ("tahoma.ttf", "segoeui.ttf", "arial.ttf")):
        path = os.path.join("C:\\", "Windows", "Fonts", name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def glyph(side):
    """The mark is a white glyph on its own near-black square, and pasting
    that square onto a pure-black card leaves a visible box. Its own
    luminance is the mask, so the glyph composites and the square does
    not travel with it."""
    src = Image.open(SOURCE).convert("RGB").resize((side, side), Image.LANCZOS)
    # the plate is not quite zero - it sits one unit above black - and one
    # unit is enough to draw the outline of a square on a pure-black card
    mask = src.convert("L").point(lambda v: 0 if v <= FLOOR else v)
    out = Image.new("RGBA", (side, side), INK + (0,))
    out.putalpha(mask)
    return out


def card():
    """The mark on the left, the wordmark and the line on the right."""
    img = Image.new("RGB", OG_SIZE, BG)

    # 470px tall sits the mark on the same optical baseline as the text
    # block without crowding either edge
    side = 470
    mark = glyph(side)
    img.paste(mark, (72, (OG_SIZE[1] - side) // 2), mark)

    d = ImageDraw.Draw(img)
    x = 72 + side + 56

    d.text((x, 214), WORDMARK, font=font(96, bold=True), fill=INK)
    d.text((x, 330), LINE, font=font(30), fill=INK)
    d.text((x, 386), FOOT, font=font(26), fill=DIM)

    # a hairline under the text block, the one nod to the window chrome
    d.line([(x, 442), (OG_SIZE[0] - 72, 442)], fill=(60, 60, 60), width=2)
    return img


def icons():
    """The touch icon keeps its black plate - iOS composites it onto the
    home screen itself, and a transparent glyph there disappears."""
    plate = Image.new("RGB", (180, 180), BG)
    mark = glyph(180)
    plate.paste(mark, (0, 0), mark)
    return plate


def verify():
    """The card is only useful at the size the scrapers expect."""
    problems = []
    for path in (OG, ICO, TOUCH):
        if not os.path.exists(path):
            problems.append("missing: {}".format(os.path.relpath(path, ROOT)))
    if not problems:
        got = Image.open(OG).size
        if got != OG_SIZE:
            problems.append("og.png is {}x{}, expected {}x{}".format(
                got[0], got[1], OG_SIZE[0], OG_SIZE[1]))
        if Image.open(TOUCH).size != (180, 180):
            problems.append("apple-touch-icon.png is not 180x180")
    for p in problems:
        print("ogimage:", p)
    print("ogimage: ok" if not problems else "ogimage: FAILED")
    return 1 if problems else 0


def main():
    if "--verify" in sys.argv:
        return verify()

    os.makedirs(ASSETS, exist_ok=True)
    card().save(OG, "PNG", optimize=True)

    glyph(48).save(ICO, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    icons().save(TOUCH, "PNG", optimize=True)

    for path in (OG, ICO, TOUCH):
        print("  {:<34} {:>7,} bytes".format(
            os.path.relpath(path, ROOT).replace("\\", "/"),
            os.path.getsize(path)))
    print("ogimage: 3 files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
