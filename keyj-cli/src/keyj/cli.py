"""
============================================================
keyj — the command line
F-Keys | www.f-keys.com
------------------------------------------------------------
  keyj tab solo.txt > song.txt        tablature to notes
  keyj render song.txt out.wav        notes to audio
  keyj play song.txt                  notes, played by typing
  keyj show song.txt                  what is in a file

tab, render and show need nothing installed beyond the standard
library and never touch your keyboard. play is the only command
that installs a system-wide listener, and it is the only one
that needs the extra: pip install 'keyj[play]'.
============================================================
"""

import argparse
import sys

from . import render as rendermod
from . import sequence, tab
from .notes import Note

VERSION = "0.1.0"


def _out(msg=""):
    sys.stdout.write(msg + "\n")


def _err(msg):
    sys.stderr.write(msg + "\n")


def _read(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _load_notes(path):
    """A sequence file, or a bare list of note names. Reports what it skipped."""
    got = sequence.parse(_read(path))
    if got.skipped:
        _err("  skipped {} unreadable name(s): {}".format(
            len(got.skipped), " ".join(got.skipped[:8])))
    if not got.notes:
        _err("  no note names in {}".format(path))
        return None
    return got.notes


# ── commands ─────────────────────────────────────────────────

def cmd_tab(args):
    report = tab.parse(_read(args.file), tuning=args.tuning, capo=args.capo)
    if report.error:
        _err("  " + report.error)
        return 1
    # Everything it did, on stderr, so stdout stays a clean sequence to pipe.
    _err("  {} notes from {} block(s), {} strings, {}{}".format(
        len(report.notes), report.blocks, report.strings, report.tuning,
        ", capo " + str(report.capo) if report.capo else ""))
    for line in report.skipped:
        _err("  skipped: " + line)
    text = sequence.format(report.notes, "tab")
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        _err("  wrote " + args.output)
    else:
        sys.stdout.write(text)
    return 0


def cmd_render(args):
    notes = _load_notes(args.file)
    if not notes:
        return 1
    buf = rendermod.render(notes, bpm=args.bpm, tone=args.tone,
                           volume=args.volume, reverb=args.reverb)
    buf, peak = rendermod.normalise(buf)
    seconds = rendermod.write_wav(args.output, buf)
    _out("  {} notes at {} BPM, {}, {:.1f}s -> {}".format(
        len(notes), args.bpm, args.tone, seconds, args.output))
    if peak > 1.0:
        _out("  peak was {:.2f} before normalising, so it was scaled down".format(peak))
    return 0


def cmd_show(args):
    notes = _load_notes(args.file)
    if not notes:
        return 1
    _out("  {} notes".format(len(notes)))
    line = []
    for n in notes:
        line.append(n.name)
        if len(line) == 16:
            _out("  " + " ".join(line))
            line = []
    if line:
        _out("  " + " ".join(line))
    lo = min(notes, key=lambda n: n.freq)
    hi = max(notes, key=lambda n: n.freq)
    _out("  range {} to {}  ({:.1f} to {:.1f} Hz)".format(
        lo.name, hi.name, lo.freq, hi.freq))
    return 0


def cmd_play(args):
    from . import play as playmod
    notes = _load_notes(args.file)
    if not notes:
        return 1

    state = {"n": 0}

    def on_note(index, note):
        state["n"] += 1
        if not args.quiet:
            sys.stdout.write("\r  {} / {}   {:<5}".format(
                index + 1, len(notes), note.name))
            sys.stdout.flush()

    def on_ready():
        _out("  {} notes, {}, {}".format(
            len(notes), args.tone, "looping" if args.loop else "once through"))
        _out("  Press any key, anywhere. Ctrl-C to stop.")
        _out("  This never reads which key you pressed - only that one was.")

    try:
        played = playmod.run(notes, tone=args.tone, loop=args.loop,
                             hold=args.hold, on_note=on_note, on_ready=on_ready)
    except playmod.Missing as err:
        _err("  " + str(err))
        return 2
    except RuntimeError as err:
        _err("  " + str(err))
        return 3
    _out("")
    _out("  stopped after {} notes".format(state["n"] or played))
    return 0


# ── wiring ───────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(
        prog="keyj",
        description="Key-J on the command line: tablature in, notes out, "
                    "played by typing.",
        epilog="tab, render and show need no dependencies and never touch "
               "your keyboard. play needs: pip install 'keyj[play]'")
    p.add_argument("--version", action="version", version="keyj " + VERSION)
    sub = p.add_subparsers(dest="command")

    t = sub.add_parser("tab", help="convert guitar tablature to a sequence")
    t.add_argument("file", help="a tablature file, or - for stdin")
    t.add_argument("-t", "--tuning", default="standard",
                   help="standard, dropd, eb, d, dadgad, openg, 7string, bass")
    t.add_argument("-c", "--capo", type=int, default=0, help="capo fret")
    t.add_argument("-o", "--output", help="write here instead of stdout")
    t.set_defaults(func=cmd_tab)

    r = sub.add_parser("render", help="render a sequence to a WAV file")
    r.add_argument("file", help="a sequence file, or - for stdin")
    r.add_argument("output", help="the .wav to write")
    r.add_argument("-b", "--bpm", type=int, default=140, help="one note per beat")
    r.add_argument("-T", "--tone", default="clean",
                   choices=sorted(rendermod.TONES), help="which tone preset")
    r.add_argument("-v", "--volume", type=float, default=0.75)
    r.add_argument("--reverb", type=float, default=None,
                   help="override the tone's reverb, 0 to 1")
    r.set_defaults(func=cmd_render)

    s = sub.add_parser("show", help="print what is in a sequence file")
    s.add_argument("file")
    s.set_defaults(func=cmd_show)

    y = sub.add_parser("play", help="play the sequence as you type, anywhere")
    y.add_argument("file")
    y.add_argument("-T", "--tone", default="clean",
                   choices=sorted(rendermod.TONES))
    y.add_argument("--hold", type=float, default=0.55,
                   help="how long each note rings, in seconds")
    y.add_argument("--once", dest="loop", action="store_false",
                   help="stop at the end instead of looping")
    y.add_argument("-q", "--quiet", action="store_true",
                   help="do not print the position line")
    y.set_defaults(func=cmd_play, loop=True)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except FileNotFoundError as err:
        _err("  no such file: {}".format(err.filename))
        return 1
    except ValueError as err:
        _err("  " + str(err))
        return 1
    except KeyboardInterrupt:
        _err("")
        return 130


if __name__ == "__main__":
    sys.exit(main())
