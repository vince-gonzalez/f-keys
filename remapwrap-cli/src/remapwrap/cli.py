#!/usr/bin/env python3
"""
============================================================
remapwrap - build and check control surfaces
F-Keys | www.f-keys.com
------------------------------------------------------------
  remapwrap check layout.json
  remapwrap describe layout.json
  remapwrap soundboard ./samples -o board.json
  remapwrap mixer Discord Spotify chrome -o mix.json
  remapwrap deck "Copy:ctrl+c" "Paste:ctrl+v" -o keys.json

A layout written here is imported by the RemapWrap dashboard
and pushed to a phone. Nothing here talks to a phone itself;
it writes the document the surface is made of.

No dependencies. Standard library only.
============================================================
"""

from __future__ import annotations

import argparse
import sys

from . import elgato, generate
from .layout import LayoutError, check, describe, load, save

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


def _write(lay, out, log=print):
    problems = check(lay)
    if problems:
        # Refusing to write a broken layout is the point of having the
        # rules in the first place.
        log("  This layout would not work:")
        for p in problems:
            log("    {}".format(p))
        return 1
    if out:
        save(lay, out)
        log("  wrote {}".format(out))
        log("  " + describe(lay).replace("\n", "\n  "))
    else:
        import json
        print(json.dumps(lay, indent=1, ensure_ascii=False))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="remapwrap",
        description="Build and check RemapWrap control surfaces.")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("check", help="is this layout usable")
    p.add_argument("file")

    p = sub.add_parser("describe", help="what is in this layout")
    p.add_argument("file")

    p = sub.add_parser("soundboard", help="a pad per sound file in a folder")
    p.add_argument("folder")
    p.add_argument("-o", "--out")

    p = sub.add_parser("mixer", help="a slider per application")
    p.add_argument("apps", nargs="*")
    p.add_argument("--no-master", action="store_true")
    p.add_argument("--no-mic", action="store_true")
    p.add_argument("-o", "--out")

    p = sub.add_parser("elgato", help="import a Stream Deck profile")
    p.add_argument("profile", help=".streamDeckProfile, a folder, or a manifest.json")
    p.add_argument("-o", "--out")
    p.add_argument("--name")

    p = sub.add_parser("deck", help="a key per label:keystroke")
    p.add_argument("pairs", nargs="+", metavar="LABEL:KEYS")
    p.add_argument("-o", "--out")

    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 2

    try:
        if args.cmd == "check":
            problems = check(load(args.file))
            if not problems:
                print("  {}: usable".format(args.file))
                return 0
            print("  {}: {} problem(s)\n".format(args.file, len(problems)))
            for p in problems:
                print("    {}".format(p))
            return 1

        if args.cmd == "describe":
            print("  " + describe(load(args.file)).replace("\n", "\n  "))
            return 0

        if args.cmd == "soundboard":
            return _write(generate.soundboard(args.folder), args.out)

        if args.cmd == "mixer":
            return _write(generate.mixer(args.apps,
                                         master=not args.no_master,
                                         mic=not args.no_mic), args.out)

        if args.cmd == "elgato":
            profile, report = elgato.read(args.profile, args.name)
            # The report is printed before anything is written, because the
            # thing somebody most needs to know is what did NOT come across.
            for line in report:
                print("  {}".format(line))
            print("")
            problems = check(profile["pages"][0] and
                             {"cols": profile["pages"][0]["cols"],
                              "rows": profile["pages"][0]["rows"],
                              "keys": profile["pages"][0]["keys"]})
            if problems:
                print("  The first page would not work:")
                for pr in problems:
                    print("    {}".format(pr))
                return 1
            if args.out:
                save(profile, args.out)
                print("  wrote {}".format(args.out))
                print("  {} page(s), {} key(s)".format(
                    len(profile["pages"]),
                    sum(len(pg["keys"]) for pg in profile["pages"])))
            else:
                import json as _json
                print(_json.dumps(profile, indent=1, ensure_ascii=False))
            return 0

        if args.cmd == "deck":
            pairs = []
            for raw in args.pairs:
                if ":" not in raw:
                    print("  {!r} is not LABEL:KEYS".format(raw))
                    return 2
                label, keys = raw.split(":", 1)
                pairs.append((label, keys))
            return _write(generate.deck(pairs), args.out)

    except LayoutError as err:
        print("  {}".format(err))
        return 2
    except OSError as err:
        print("  {}".format(err))
        return 2

    return 2


if __name__ == "__main__":
    sys.exit(main())
