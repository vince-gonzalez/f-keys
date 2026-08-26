#!/usr/bin/env python3
"""
============================================================
session_gate — the house rules, while the work is happening
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

typefloor and contrast are in CI, so a breach is caught after
a commit reaches GitHub. That is the wrong end of the work.
The 13px floor and the 4.5:1 rule have both been broken and
shipped in a single sitting, and both times the only thing
that caught it was somebody remembering to type the command.

This runs them the moment a file changes, from a PostToolUse
hook, and refuses the change loudly rather than logging it
quietly.

It reads the hook payload on stdin and does nothing at all
unless the file that changed is one these gates apply to, so
editing a Python file or a README costs nothing.

  echo '{"tool_input":{"file_path":"..."}}' | python tools/session_gate.py

Exit 0  nothing to check, or everything passed
Exit 2  a gate failed - the reason goes to stderr and is fed
        back so it can be fixed immediately rather than found
        by CI twenty minutes later
============================================================
"""

import io
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Only what these gates actually inspect. Running a whole-repo scan every
#: time a Python file is touched is how a useful gate becomes a thing people
#: switch off.
WATCHED = (".html", ".css")

GATES = [
    ("typefloor", ["python", os.path.join("tools", "typefloor.py")]),
    ("contrast", ["python", os.path.join("tools", "contrast.py")]),
]


def changed_file(payload):
    """The path the tool wrote, whichever shape the payload uses."""
    for where in (payload.get("tool_response") or {}, payload.get("tool_input") or {}):
        if not isinstance(where, dict):
            continue
        for key in ("filePath", "file_path"):
            value = where.get(key)
            if isinstance(value, str) and value:
                return value
    return ""


def applies(path):
    if not path:
        return False
    if os.path.splitext(path)[1].lower() not in WATCHED:
        return False
    # Only this repository. A hook that fires on every HTML file on the
    # machine would run these gates against somebody else's work.
    try:
        return os.path.commonpath([os.path.abspath(path), REPO]) == REPO
    except ValueError:
        # Different drives on Windows; commonpath raises rather than
        # returning something useless.
        return False


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0                      # not a payload; not this gate's problem

    path = changed_file(payload)
    if not applies(path):
        return 0

    failures = []
    for name, argv in GATES:
        run = subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        if run.returncode != 0:
            body = (run.stdout or "") + (run.stderr or "")
            failures.append("{}:\n{}".format(name, body.strip()))

    if not failures:
        return 0

    sys.stderr.write(
        "The house gates refused " + os.path.basename(path) + ".\n\n" +
        "\n\n".join(failures) + "\n\n" +
        "These are the two rules that have been broken and shipped more than "
        "once. Fix it here rather than finding it in CI.\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
