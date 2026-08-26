#!/usr/bin/env python3
"""Every place a package writes its version must agree. Run before any upload.

Seven wheels went to PyPI reporting a version different from the one on the tin,
because `pyproject.toml` was bumped and `__init__.py` was not. The filename and
the METADATA both derive from pyproject, so they agree with each other and the
mismatch is invisible from outside the wheel. This is the check that sees it.

    python version-gate.py            report
    python version-gate.py --sync X   write version X to every site in one tree
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Where each package tree lives.
#
# This file used to live in the temp directory, which gets cleaned. It is
# the thing that stops a wheel disagreeing with its own metadata, and it
# was one sweep away from disappearing - the same mistake as leaving a
# signing key there. It is version controlled now.
TREES = {
    "gonzalgo":       r"C:\tmp\gonzalgo-work",
    "authorecon":     r"C:\tmp\authorecon",
    "mmforge":        r"C:\tmp\setmm-choice",
    "certivl":        r"C:\tmp\certivl",
    "ishihara":       r"C:\tmp\ishihara",
    "opticquiz-cvd":  r"C:\tmp\opticquiz.com\packages\cvd-py",
    "keyj":           r"C:\tmp\f-keys\keyj-cli",
    "plumhud":        r"C:\tmp\f-keys\plumhud",
    "moonbeam-miner": r"C:\tmp\f-keys\moonbeam",
    "remapwrap":      r"C:\tmp\f-keys\remapwrap-cli",
    "loadbearing":    r"C:\tmp\loadbearing",
}

PYPROJECT = re.compile(r'(?m)^(version\s*=\s*")([^"]+)(")')
DUNDER = re.compile(r'(?m)^(__version__\s*=\s*")([^"]+)(")')
JSONVER = re.compile(r'("version"\s*:\s*")([^"]+)(")')


def sites(root: Path) -> list[tuple[Path, re.Pattern, str]]:
    out = []
    p = root / "pyproject.toml"
    if p.exists():
        m = PYPROJECT.search(p.read_text(encoding="utf-8", errors="replace"))
        if m:
            out.append((p, PYPROJECT, m.group(2)))
    for f in ("server.json", "package.json"):
        j = root / f
        if j.exists():
            m = JSONVER.search(j.read_text(encoding="utf-8", errors="replace"))
            if m:
                out.append((j, JSONVER, m.group(2)))
    for init in sorted(root.glob("src/*/__init__.py")) + sorted(root.glob("*/__init__.py")):
        m = DUNDER.search(init.read_text(encoding="utf-8", errors="replace"))
        if m:
            out.append((init, DUNDER, m.group(2)))
    return out


def sync(root: Path, target: str) -> list[str]:
    touched = []
    for f, pat, cur in sites(root):
        if cur == target:
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        t = pat.sub(lambda m: m.group(1) + target + m.group(3), t, count=1)
        f.write_text(t, encoding="utf-8", newline="\n")
        touched.append(f"{f.name} {cur}->{target}")
    return touched


def main() -> int:
    if "--sync" in sys.argv:
        i = sys.argv.index("--sync")
        target, tree = sys.argv[i + 1], sys.argv[i + 2]
        for line in sync(Path(tree), target) or ["already consistent"]:
            print("   " + line)
        return 0

    bad = 0
    for name, d in TREES.items():
        root = Path(d)
        if not root.exists():
            print(f"   {name:16} TREE MISSING")
            continue
        s = sites(root)
        vals = {v for _, _, v in s}
        ok = len(vals) <= 1
        bad += 0 if ok else 1
        print("   %-16s %-9s %s   %s" % (
            name, sorted(vals)[0] if len(vals) == 1 else "SPLIT",
            "ok " if ok else "BAD",
            ", ".join(f"{f.name}={v}" for f, _, v in s)))
    print()
    print("   consistent" if not bad else f"   {bad} package(s) disagree with themselves")
    return 1 if bad else 0




# ── The manifest, checked against reality ─────────────────────
#
# Added because the same mistake was made twice in one sitting: a server.json
# naming github.com/zengineco/<pkg> when the repository is actually under
# vince-gonzalez. The MCP registry verifies the io.github.<owner> namespace
# AGAINST the repository owner, so a manifest that names the wrong owner
# cannot be published at all - and nothing said so until the push failed.
#
# Run:  python tools/version_gate.py --manifests

def _git_remote(root):
    import subprocess
    try:
        out = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=20)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def check_manifests():
    import json as _json
    import urllib.error
    import urllib.request

    problems = []
    checked = 0
    for name, root in TREES.items():
        manifest = Path(root) / "server.json"
        if not manifest.exists():
            continue
        checked += 1
        try:
            doc = _json.loads(manifest.read_text(encoding="utf-8"))
        except ValueError as e:
            problems.append("{}: server.json will not parse ({})".format(name, e))
            continue

        declared = (doc.get("repository") or {}).get("url", "")
        remote = _git_remote(root)
        if remote:
            # git@host:owner/repo.git and https://host/owner/repo.git are the
            # same repository written two ways.
            def slug(u):
                u = u.strip().replace("git@github.com:", "https://github.com/")
                return u[:-4] if u.endswith(".git") else u
            if slug(declared).lower() != slug(remote).lower():
                problems.append(
                    "{}: server.json says {} but origin is {}"
                    .format(name, declared or "(nothing)", remote))

        owner = ""
        if "github.com/" in declared:
            owner = declared.split("github.com/")[1].split("/")[0]
        ident = doc.get("name", "")
        if owner and ident.startswith("io.github."):
            named = ident[len("io.github."):].split("/")[0]
            if named.lower() != owner.lower():
                problems.append(
                    "{}: namespace io.github.{} does not match repository owner {}"
                    .format(name, named, owner))

        for url in [doc.get("websiteUrl", ""), declared]:
            if not url:
                continue
            # Redirects are NOT followed. github.com/<old-owner>/<repo>
            # answers 301 to the new owner after a transfer, so following it
            # reports a healthy 200 for a URL that names somebody who no
            # longer holds the repository - which is exactly how a stale
            # manifest was declared clean.
            class _NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *a, **k):
                    return None

            opener = urllib.request.build_opener(_NoRedirect)
            try:
                code = opener.open(urllib.request.Request(
                    url, headers={"User-Agent": "curl/8"}), timeout=20).status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception:
                code = "unreachable"
            if code != 200:
                extra = " (a redirect is not a healthy URL here)" if                     isinstance(code, int) and 300 <= code < 400 else ""
                problems.append("{}: {} returns {}{}".format(name, url, code, extra))

    print("")
    if problems:
        print("   manifests: {} problem(s)".format(len(problems)))
        for p in problems:
            print("     " + p)
        return 1
    print("   manifests: {} checked, every URL and namespace agrees".format(checked))
    return 0


# ── Entry point ───────────────────────────────────────────────
# One dispatch, at the bottom, after everything it can call is defined.
# The first attempt put the manifest branch above check_manifests() and it
# raised NameError; the second put it below `raise SystemExit(main())`,
# where nothing could ever reach it.
if __name__ == "__main__":
    if "--manifests" in sys.argv:
        raise SystemExit(check_manifests())
    raise SystemExit(main())
