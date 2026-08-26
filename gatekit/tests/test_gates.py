#!/usr/bin/env python3
"""
============================================================
test_gates - each gate finds the thing it exists to find
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Every one of these three shipped a version that reported OK on
a directory it had never opened, because a bare path argument
was silently ignored and the tool scanned itself instead. A
gate that passes on a tree it did not read is worse than no
gate: it converts an unchecked project into a green tick.

So the fixtures below are known-bad, and a gate that does not
fail on them fails here instead. The last case is the one that
matters most - it asserts the gate is reading the directory it
was given.

Run:  python gatekit/tests/test_gates.py
============================================================
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
sys.path.insert(0, SRC)

failures = []


def check(name, got, want):
    if got != want:
        failures.append("{}\n      got:      {}\n      expected: {}"
                        .format(name, got, want))


def run(module, args, cwd):
    """Each gate as a subprocess, because the exit code is the contract."""
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC
    for key in ("TYPEFLOOR_CONFIG", "CONTRAST_CONFIG", "DEADNAME_CONFIG",
                "TYPEFLOOR_ROOT", "CONTRAST_ROOT", "DEADNAME_ROOT"):
        env.pop(key, None)
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; from gatekit.{} import main; sys.exit(main())".format(module)]
        + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=cwd, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


BAD_PAGE = """<style>
  .tiny { font-size: 7px; }
</style>
<div class="tiny">six point type nobody can read</div>
<p>Built by OldCorp</p>
"""

BAD_CSS = """:root {
  --bg: #ffffff;
  --ink-faint: #bbbbbb;
}
"""

GOOD_PAGE = """<style>
  .body { font-size: 16px; }
</style>
<div class="body">large enough</div>
<p>Built by F-Keys</p>
"""


def fixture(contents):
    d = tempfile.mkdtemp(prefix="gatekit-")
    for name, text in contents.items():
        with io.open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(text)
    return d


def main():
    bad = fixture({"page.html": BAD_PAGE, "theme.css": BAD_CSS})
    good = fixture({"page.html": GOOD_PAGE})
    elsewhere = tempfile.mkdtemp(prefix="gatekit-cwd-")

    try:
        # ── each gate finds its own defect ───────────────────────
        code, out = run("typefloor", [bad], cwd=elsewhere)
        check("typefloor fails on 7px", code, 1)
        check("typefloor names the size", "7px" in out, True)

        # The packaged default forbids nothing, so the test supplies the
        # name it is testing for - which is also how a consumer uses it.
        cfg = os.path.join(bad, "deadname.json")
        with io.open(cfg, "w", encoding="utf-8") as f:
            f.write('{"forbidden": ["oldcorp"], "allowed": [], "skip_paths": []}')

        code, out = run("deadname_gate", [bad, "--config", cfg], cwd=elsewhere)
        check("deadname-gate fails on a retired name", code, 1)

        code, out = run("contrast", [bad, "--require-pairs"], cwd=elsewhere)
        check("contrast fails on #bbbbbb over #ffffff", code, 1)

        # ── and passes what is fine ──────────────────────────────
        code, out = run("typefloor", [good], cwd=elsewhere)
        check("typefloor passes 16px", code, 0)

        code, out = run("deadname_gate", [good, "--config", cfg], cwd=elsewhere)
        check("deadname-gate passes a clean page", code, 0)

        # ── the defect this file was written for ─────────────────
        # Run from a directory that is clean, pointed at one that is not.
        # A gate that scans its own location instead of the path it was
        # given reports 0 here and is wrong.
        code, out = run("typefloor", [bad], cwd=good)
        check("typefloor reads the path it was given, not its cwd", code, 1)

        code, out = run("deadname_gate", [bad, "--config", cfg], cwd=good)
        check("deadname-gate reads the path it was given", code, 1)

        # ── a vacuous pass must be refusable ─────────────────────
        empty = fixture({"note.txt": "no styles here"})
        code, out = run("contrast", [empty], cwd=elsewhere)
        check("contrast exits 0 when there is nothing to check", code, 0)
        code, out = run("contrast", [empty, "--require-pairs"], cwd=elsewhere)
        check("--require-pairs turns that into a failure", code, 1)
        shutil.rmtree(empty, ignore_errors=True)
    finally:
        for d in (bad, good, elsewhere):
            shutil.rmtree(d, ignore_errors=True)

    if failures:
        print("test_gates: {} FAILED\n".format(len(failures)))
        for f in failures:
            print("  - " + f + "\n")
        return 1
    print("test_gates: 10 cases ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
