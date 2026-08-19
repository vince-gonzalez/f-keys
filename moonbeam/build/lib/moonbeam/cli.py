"""
============================================================
moonbeam.cli — the terminal front end
F-Keys | www.f-keys.com
------------------------------------------------------------
    moonbeam            saved miners, or offer to scan
    moonbeam scan       sweep this subnet and remember what answered
    moonbeam watch      refresh until interrupted
    moonbeam show <n>   everything one miner reported

DESIGN RULE
  A dash means the miner did not report that field. It never
  means zero and it is never a stand-in for a number we did
  not receive.
============================================================
"""

import argparse
import sys
import time

from . import miners as M

__all__ = ["main"]

GREEN, CYAN, DIM, AMBER, RED, OFF = (
    "\033[92m", "\033[96m", "\033[90m", "\033[93m", "\033[91m", "\033[0m")


def _supports_colour():
    if not sys.stdout.isatty():
        return False
    if sys.platform == "win32":
        try:                                    # modern Windows terminals do
            import colorama                     # noqa: F401
            return True
        except ImportError:
            import os
            return os.environ.get("WT_SESSION") or os.environ.get("TERM")
    return True


if not _supports_colour():
    GREEN = CYAN = DIM = AMBER = RED = OFF = ""


def _console_handles(ch):
    """Windows consoles often run a codepage that cannot encode an em dash
    or a degree sign, and they print a replacement blob instead. Check
    rather than assume, and fall back to ASCII when it would not survive."""
    enc = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        ch.encode(enc)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


DASH = "—" if _console_handles("—") else "-"
DEG = "°C" if _console_handles("°") else "C"
MID = " · " if _console_handles("·") else " | "


def fmt_hash(v):
    if v is None:
        return DASH
    try:
        v = float(v)
    except (TypeError, ValueError):
        return DASH
    return "{:.0f} GH/s".format(v) if v < 1000 else "{:.2f} TH/s".format(v / 1000)


def fmt_temp(v):
    if v is None:
        return DASH
    try:
        v = float(v)
    except (TypeError, ValueError):
        return DASH
    colour = GREEN if v < 60 else (AMBER if v < 75 else RED)
    return "{}{:.0f}{}{}".format(colour, v, DEG, OFF)


def fmt_uptime(s):
    if s is None:
        return DASH
    try:
        s = int(s)
    except (TypeError, ValueError):
        return DASH
    d, rem = divmod(s, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return "{}d {}h".format(d, h)
    if h:
        return "{}h {}m".format(h, m)
    return "{}m".format(m)


def fmt_num(v):
    if v is None:
        return DASH
    try:
        return "{:,}".format(int(v))
    except (TypeError, ValueError):
        return str(v)


def print_table(found):
    if not found:
        print("  {}No miners answered.{}".format(DIM, OFF))
        return
    print()
    print("  {}{:<3} {:<16} {:<15} {:>12} {:>8} {:>10} {:>9}{}".format(
        DIM, "#", "NAME", "ADDRESS", "HASHRATE", "TEMP", "ACCEPTED", "UPTIME", OFF))
    print("  " + DIM + "-" * 78 + OFF)
    for i, m in enumerate(found, 1):
        if m.get("offline"):
            print("  {:<3} {:<16} {:<15} {}{:>12}{}".format(
                i, m["alias"][:16], m["ip"], RED, "offline", OFF))
            continue
        print("  {:<3} {}{:<16}{} {:<15} {:>12} {:>17} {:>10} {:>9}".format(
            i, GREEN, str(m["alias"])[:16], OFF, m["ip"],
            fmt_hash(m.get("hashrate")), fmt_temp(m.get("temp")),
            fmt_num(m.get("accepted")), fmt_uptime(m.get("uptime_s"))))

    live = [m for m in found if not m.get("offline")]
    rates = [m["hashrate"] for m in live if isinstance(m.get("hashrate"), (int, float))]
    print()
    line = "  {} miner{} answering".format(len(live), "" if len(live) == 1 else "s")
    if rates:
        line += "{}total {}".format(MID, fmt_hash(sum(rates)))
    if len(rates) != len(live):
        line += " {}({} did not report a hashrate){}".format(
            DIM, len(live) - len(rates), OFF)
    print(line)


def print_detail(m):
    print()
    print("  {}{}{}  {}".format(CYAN, m.get("alias", "?"), OFF, m.get("ip", "")))
    print("  " + DIM + "-" * 46 + OFF)
    rows = [
        ("Hashrate", fmt_hash(m.get("hashrate"))),
        ("Temperature", fmt_temp(m.get("temp"))),
        ("Shares accepted", fmt_num(m.get("accepted"))),
        ("Shares rejected", fmt_num(m.get("rejected"))),
        ("Uptime", fmt_uptime(m.get("uptime_s"))),
        ("Power", DASH if m.get("power") is None else "{:.1f} W".format(float(m["power"]))),
        ("Frequency", DASH if m.get("frequency") is None else "{} MHz".format(m["frequency"])),
        ("Best difficulty", m.get("best_diff") or DASH),
        ("Pool", m.get("pool") or DASH),
        ("Firmware", m.get("version") or DASH),
    ]
    for k, v in rows:
        print("  {:<18} {}".format(k, v))
    extra = len(m.get("raw") or {}) - 11
    if extra > 0:
        print("  {}{} further fields reported — moonbeam show {} --json{}".format(
            DIM, extra, m.get("ip"), OFF))
    print()


def do_scan(args):
    subnet = args.subnet or M.local_subnet()
    print("  scanning {}{}{} ...".format(CYAN, subnet, OFF))

    state = {"last": 0}

    def progress(done, total):
        pct = int(done * 100 / total)
        if pct != state["last"] and pct % 10 == 0:
            state["last"] = pct
            sys.stdout.write("\r  {}{}%{} ".format(DIM, pct, OFF))
            sys.stdout.flush()

    found = M.scan(subnet, timeout=args.timeout, progress=progress)
    sys.stdout.write("\r" + " " * 20 + "\r")
    print_table(found)
    if found:
        path = M.save_miners([m["ip"] for m in found])
        print("  {}remembered in {}{}".format(DIM, path, OFF))
    return found


def prompt_detail(found):
    """His ask: show the table, then offer to go deeper."""
    live = [m for m in found if not m.get("offline")]
    if not live or not sys.stdin.isatty():
        return
    try:
        ans = input("\n  More detail? [number / Enter to skip] ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not ans:
        return
    if ans.isdigit() and 1 <= int(ans) <= len(found):
        print_detail(found[int(ans) - 1])
    else:
        print("  {}Not a listed number.{}".format(DIM, OFF))


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="moonbeam",
        description="Find the NerdMiners on your network and read their vitals.")
    p.add_argument("command", nargs="?", default="status",
                   choices=["status", "scan", "watch", "show"])
    p.add_argument("target", nargs="?", help="address, for show")
    p.add_argument("--subnet", help="e.g. 192.168.1.0/24 (default: this machine's)")
    p.add_argument("--timeout", type=float, default=M.DEFAULT_TIMEOUT)
    p.add_argument("--interval", type=float, default=5.0, help="watch refresh seconds")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)

    if args.command == "scan":
        found = do_scan(args)
        if args.json:
            import json as _j
            print(_j.dumps(found, indent=2, default=str))
        else:
            prompt_detail(found)
        return 0 if found else 1

    if args.command == "show":
        if not args.target:
            print("  usage: moonbeam show <address>")
            return 2
        m = M.poll(args.target, timeout=args.timeout)
        if not m:
            print("  {}Nothing answered at {}{}".format(RED, args.target, OFF))
            return 1
        if args.json:
            import json as _j
            print(_j.dumps(m, indent=2, default=str))
        else:
            print_detail(m)
        return 0

    saved = M.load_saved()
    if not saved:
        print("  {}No saved miners yet.{}".format(DIM, OFF))
        found = do_scan(args)
        if not args.json:
            prompt_detail(found)
        return 0 if found else 1

    if args.command == "watch":
        try:
            while True:
                rows = M.poll_many(saved, timeout=args.timeout)
                print("\033[2J\033[H" if OFF else "")
                print("  {}moonbeam{} {} {}".format(
                    GREEN, OFF, DASH, time.strftime("%H:%M:%S")))
                print_table(rows)
                print("  {}refreshing every {:.0f}s — Ctrl-C to stop{}".format(
                    DIM, args.interval, OFF))
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n  stopped")
            return 0

    rows = M.poll_many(saved, timeout=args.timeout)
    if args.json:
        import json as _j
        print(_j.dumps(rows, indent=2, default=str))
        return 0
    print_table(rows)
    prompt_detail(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
