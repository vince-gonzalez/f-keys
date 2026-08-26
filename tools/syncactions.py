#!/usr/bin/env python3
"""
============================================================
syncactions - one action.yml, published to its own repo
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The GitHub Marketplace only lists an Action whose action.yml
sits at the root of a repository. The four here live in
.github/actions/ of this one, where they are tested by
actions-selftest.yml but findable by nobody.

Copying each into its own repo by hand makes four more copies
of four things, which is the fault this repository has now
made and fixed three separate times. So the copy is a build
step: this repository stays the source, each action repo is
output, and --check fails when one has drifted.

WORKFLOW STACK
  1. ACTIONS   - which local directory maps to which repo
  2. stage()   - action.yml, README, LICENSE into a temp tree
  3. push()    - commit and push, only if something changed
  4. --check   - CI: is every published repo current?

Run:  python tools/syncactions.py --check
      python tools/syncactions.py --push
============================================================
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER = "vince-gonzalez"
SOURCE = "https://github.com/vince-gonzalez/f-keys"

# (local directory, repo name, banner name, one-line description)
ACTIONS = [
    ("typefloor", "typefloor", "TYPEFLOOR",
     "type below a readable floor fails the build"),
    ("contrast", "contrast-gate", "CONTRAST",
     "colour nobody can read fails the build"),
    ("deadname", "deadname-gate", "DEADNAME",
     "a name that should be gone fails the build"),
    ("cvd", "cvd-palette", "CVD PALETTE",
     "a palette that collapses under colour blindness fails the build"),
]

MIT = """MIT License

Copyright (c) 2026 Vincent Gonzalez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

USAGE = {
    "typefloor": """```yaml
- uses: vince-gonzalez/typefloor@v1
  with:
    path: ./src
    floor: "13"          # px, optional
    config: a.json       # recorded exceptions, optional
```

Fails when any declared font size is below the floor. Six point type is not
a style choice; this exists because the same reader reported the same thing
more than once.""",

    "contrast": """```yaml
- uses: vince-gonzalez/contrast-gate@v1
  with:
    path: ./src
    require-pairs: "true"
```

Reads CSS custom properties - `--ink: #hex` against `--bg: #hex` - and fails
when an ink cannot reach 4.5:1 on any surface the file declares.

It does **not** read literal `color:` declarations. A stylesheet using neither
has nothing to compare, and would otherwise exit 0 and read as a pass on a
site nobody checked. `require-pairs: true` turns that into a failure.""",

    "deadname": """```yaml
- uses: vince-gonzalez/deadname-gate@v1
  with:
    path: ./src
    config: deadname.json
```

Fails when a name that should be gone reaches a title, a footer, a byline,
alt text or a comment - while leaving machine identifiers alone, because
renaming a repository path or a published artifact breaks working links or
contradicts a deposited record. Both halves matter: a gate that cannot tell
those apart gets switched off.

Nothing is forbidden by default, and it exits **2** rather than 0 when told
nothing - a pass while checking nothing is not a pass.

```json
{ "forbidden": ["oldname"], "allowed": [], "skip_paths": [] }
```

Written for a company rename. It is the same shape as the problem of a person
changing their name and finding it in three hundred places, which is the
harder version and the one worth getting right.""",

    "cvd": """```yaml
- uses: vince-gonzalez/cvd-palette@v1
  with:
    colors: "#1f77b4,#ff7f0e,#2ca02c"
    # or:
    file: palette.json
```

Fails when two colours become the same colour under protanopia, deuteranopia
or tritanopia.

The matplotlib defaults `#d62728` and `#2ca02c` are **71.8 apart to normal
vision and 4.8 apart under deuteranopia**. Roughly one man in twelve cannot
tell them apart, and nobody catches it in review because the reviewer can see
it.

`file:` takes a JSON array, a JSON object of name to hex, or any file at all -
a stylesheet, a config - which is scanned for `#rrggbb`.

Exits **2** rather than 0 when handed fewer than two colours, because a pass
on an empty list is not a pass.""",
}


def readme(name, banner_name, blurb, local):
    import readme as R
    body = "\n" + USAGE[local] + """

## Exit codes

| Code | Means |
|---|---|
| `0` | Clean |
| `1` | It found something. The file and line are printed. |
| `2` | Misconfigured - it could not check, and will not report clean |

## Where this comes from

The gate itself is [`legible`](https://pypi.org/project/legible/) on PyPI, so
it runs the same way on your machine as in CI:

```
pip install legible
```

Source, and the self-test that runs this Action against a fixture it must
pass and one it must fail, live in [f-keys](%s).

## Licence

MIT.
""" % SOURCE
    if local == "cvd":
        body = body.replace(
            "The gate itself is [`legible`](https://pypi.org/project/legible/) on PyPI, so\nit runs the same way on your machine as in CI:\n\n```\npip install legible\n```",
            "The engine is [`opticquiz-cvd`](https://pypi.org/project/opticquiz-cvd/)\non PyPI, so it runs the same way on your machine as in CI:\n\n```\npip install opticquiz-cvd\n```")
    return R.banner(banner_name, blurb) + body


def stage(local, repo, banner_name, blurb, into):
    src = os.path.join(ROOT, ".github", "actions", local)
    shutil.copyfile(os.path.join(src, "action.yml"),
                    os.path.join(into, "action.yml"))
    for extra in sorted(os.listdir(src)):
        if extra != "action.yml":
            shutil.copyfile(os.path.join(src, extra),
                            os.path.join(into, extra))
    io.open(os.path.join(into, "README.md"), "w",
            encoding="utf-8", newline="\n").write(
        readme(repo, banner_name, blurb, local))
    io.open(os.path.join(into, "LICENSE"), "w",
            encoding="utf-8", newline="\n").write(MIT)


def run(args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise SystemExit("%s failed:\n%s" % (" ".join(args[:3]),
                                             (r.stderr or r.stdout)[:600]))
    return r


def main():
    push = "--push" in sys.argv
    check = "--check" in sys.argv
    if not push and not check:
        print(__doc__.strip().split("Run:")[-1])
        return 0

    problems = []
    for local, repo, banner_name, blurb in ACTIONS:
        work = tempfile.mkdtemp(prefix="action-" + repo + "-")
        try:
            stage(local, repo, banner_name, blurb, work)

            if check:
                # compare against what is published, file by file
                for name in sorted(os.listdir(work)):
                    r = run(["gh", "api",
                             "repos/%s/%s/contents/%s" % (OWNER, repo, name),
                             "--jq", ".content"], check=False)
                    if r.returncode != 0:
                        problems.append("%s: %s is not published" % (repo, name))
                        continue
                    import base64
                    live = base64.b64decode(r.stdout.strip()).decode(
                        "utf-8", "replace").replace("\r\n", "\n")
                    local_text = io.open(os.path.join(work, name),
                                         encoding="utf-8").read().replace("\r\n", "\n")
                    if live != local_text:
                        problems.append("%s: %s has drifted from "
                                        ".github/actions/%s" % (repo, name, local))
                continue

            run(["git", "init", "-q", "-b", "main"], cwd=work)
            run(["git", "add", "-A"], cwd=work)
            run(["git", "-c", "user.name=Vincent Gonzalez",
                 "-c", "user.email=hello@f-keys.com",
                 "commit", "-q", "-m",
                 "%s\n\nGenerated from f-keys/.github/actions/%s by "
                 "tools/syncactions.py.\nThat repository is the source and "
                 "runs the self-test; this one\nexists so the Marketplace can "
                 "list it, which needs action.yml at a\nrepository root."
                 % (blurb[0].upper() + blurb[1:], local)], cwd=work)
            run(["git", "remote", "add", "origin",
                 "https://github.com/%s/%s.git" % (OWNER, repo)], cwd=work)
            run(["git", "push", "-q", "-f", "origin", "main"], cwd=work)
            print("  pushed %s/%s" % (OWNER, repo))
        finally:
            shutil.rmtree(work, ignore_errors=True)

    if check:
        for p in problems:
            print("  syncactions:", p)
        print("syncactions: ok" if not problems
              else "syncactions: %d FAILED" % len(problems))
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
