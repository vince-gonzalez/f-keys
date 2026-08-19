"""
============================================================
plumhud.cli — entry point
F-Keys | www.f-keys.com
------------------------------------------------------------
    plumhud            the overlay HUD and command center
    plumhud check      poll once, print, exit (no window)
    plumhud where      where config and history are kept

`check` exists so the fleet can be read over SSH, from a cron
job, or on a machine with no display - and so the polling path
can be tested without a GUI, which is the part a test can
actually reach.
============================================================
"""

import argparse
import sys

__all__ = ["main"]


def _check(args):
    """Poll the saved fleet once and print it. Shares moonbeam's renderer."""
    from moonbeam import cli as mcli
    from . import app as A

    cfg = A.load_config()
    miners = cfg.get("miners") or []
    if not miners:
        print("  No miners configured yet.")
        print("  Run `moonbeam scan` to find them, or add them in the HUD.")
        return 1

    stats = A.poll_fleet([m["ip"] for m in miners])
    rows = []
    for m, st in zip(miners, stats):
        rows.append({
            "ip": st["ip"],
            "alias": st.get("alias") or m.get("alias") or st["ip"],
            "hashrate": st.get("hash"),
            "temp": st.get("temp"),
            "accepted": st.get("shares"),
            "uptime_s": st.get("uptime"),
            "offline": st.get("status") == "Offline",
        })
    mcli.print_table(rows)
    return 0


def _where(_args):
    from . import paths
    print("  config   {}".format(paths.CONFIG_FILE))
    print("  history  {}".format(paths.DB_FILE))
    print("  log      {}".format(paths.LOG_FILE))
    return 0


def _gui(_args):
    try:
        from . import app as A
    except ImportError as e:
        print("  Could not start the interface: {}".format(e))
        print("  On Linux, tkinter is often a separate package "
              "(apt install python3-tk).")
        return 1
    application = A.PlumHUDApp()
    application.mainloop()
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="plumhud",
        description="Miner fleet monitor - overlay HUD, alerts, and history.")
    p.add_argument("command", nargs="?", default="hud",
                   choices=["hud", "check", "where"])
    args = p.parse_args(argv)

    if args.command == "check":
        return _check(args)
    if args.command == "where":
        return _where(args)
    return _gui(args)


if __name__ == "__main__":
    sys.exit(main())
