#!/usr/bin/env python3
"""
============================================================
deadname-gate - this repository's entry point
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS IS A SHIM
The implementation moved to gatekit/, which is published so
other people can run the same gate. Copying it back here would
make two copies of one thing, which is how Key-J shipped three
defects and is the reason this repository has a parity test at
all.

So there is one implementation. CI runs the code that ships,
and the exception list stays local: DEADNAME_CONFIG
points at tools/deadname_gate.json rather than the packaged
default.

Run:  python tools/deadname_gate.py [path] [--list]
============================================================
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

os.environ.setdefault("DEADNAME_CONFIG", os.path.join(HERE, "deadname_gate.json"))
os.environ.setdefault("DEADNAME_ROOT", ROOT)
sys.path.insert(0, os.path.join(ROOT, "gatekit", "src"))

from gatekit.deadname_gate import main   # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
