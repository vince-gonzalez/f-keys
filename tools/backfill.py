#!/usr/bin/env python3
"""
============================================================
backfill - the history that was actually recorded elsewhere
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The snapshot began on 18 August 2026, so the trend on the
status page starts there. But the registries were recording
long before anything here was: npm keeps daily download counts
per package, and every release carries the date it shipped.
That history exists, it is real, and nobody had gone to get it.

WHAT THIS WILL NOT DO
It will not invent the parts nobody recorded. Site traffic
before Cloudflare's retention window is gone. Uptime before
18 August has no answer, because nothing was checking. Those
fields are ABSENT from a backfilled day rather than estimated,
zeroed, or interpolated - a gap is a fact and a smooth line
would be a lie, on a page that sits next to papers with DOIs.

HOW FAR BACK
To 2026-07-12, the first PyPI release. There is nothing before
that because nothing had shipped. The limits are per source:

  npm       daily downloads, from the first release
  PyPI      daily downloads, from the first release. Measured
            rather than assumed: each package's earliest
            pypistats day IS its release day, so there is no
            rolling window cutting anything off - a package
            with 21 days of data is 21 days old
  releases  every version and its date, from both registries
  stars     the date each star arrived, from the GitHub API

So nothing is lost to retention. The floor is the work itself.

Every file written carries backfilled: true and the list of
sources it was built from, so a reader can tell a reconstructed
day from a measured one, and so can the next tool.

Run:  python tools/backfill.py --dry-run    (what it would write)
      python tools/backfill.py              (write them)
============================================================
"""

import datetime
import io
import json
import os
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import snapshot as S

ROOT = S.ROOT
DATA_DIR = S.DATA_DIR
UA = {"User-Agent": S.UA, "Accept": "application/json"}

NOTE = ("Reconstructed from the registries, which recorded this before the "
        "daily snapshot existed. Traffic and uptime are absent rather than "
        "estimated: nothing measured them on this date.")


def get(url, tries=3):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "replace")), None
        except Exception as e:
            err = "HTTP {}".format(getattr(e, "code", type(e).__name__))
            if getattr(e, "code", None) in (400, 401, 403, 404):
                return None, err
    return None, err


def npm_daily(today):
    """Daily downloads per npm package. The range endpoint caps at 18
    months, which is far longer than anything here has existed."""
    out, first = {}, None
    for pkg in S.NPM_PACKAGES:
        d, err = get("https://api.npmjs.org/downloads/range/2025-01-01:{}/{}"
                     .format(today, pkg.replace("/", "%2f")))
        if err:
            print("  npm {}: {}".format(pkg, err))
            continue
        for row in d.get("downloads") or []:
            if row["downloads"]:
                out.setdefault(row["day"], {})[pkg] = row["downloads"]
                if first is None or row["day"] < first:
                    first = row["day"]
    return out, first


def pypi_daily():
    """Daily downloads per PyPI package, for the package's whole life.

    Checked rather than assumed: opticquiz-cvd released 2026-07-12 and
    pypistats' earliest day for it is 2026-07-12; gonzalgo released
    2026-08-04 and its earliest is 2026-08-04. There is no rolling window
    truncating this - a short series means a young package."""
    out = {}
    for pkg in S.PYPI_PACKAGES:
        d, err = get("https://pypistats.org/api/packages/{}/overall".format(pkg))
        if err:
            print("  pypi {}: {}".format(pkg, err))
            continue
        for row in d.get("data") or []:
            if row.get("category") != "without_mirrors" or not row["downloads"]:
                continue
            out.setdefault(row["date"], {})[pkg] = row["downloads"]
    return out


def releases():
    """Every published version and the day it shipped. These are events,
    not measurements, and they are exact."""
    out = {}
    for pkg in S.PYPI_PACKAGES:
        d, err = get("https://pypi.org/pypi/{}/json".format(pkg))
        if err:
            continue
        for version, files in (d.get("releases") or {}).items():
            if files:
                day = files[0]["upload_time_iso_8601"][:10]
                out.setdefault(day, []).append(
                    {"package": pkg, "version": version, "registry": "PyPI"})
    for pkg in S.NPM_PACKAGES:
        d, err = get("https://registry.npmjs.org/" + pkg.replace("/", "%2f"))
        if err:
            continue
        for version, when in (d.get("time") or {}).items():
            if version in ("created", "modified"):
                continue
            out.setdefault(when[:10], []).append(
                {"package": pkg, "version": version, "registry": "npm"})
    return out


def stars():
    """The date each star arrived. Needs the gh CLI's credentials; the
    anonymous API refuses the header that carries the timestamp."""
    out = {}
    for full in S.GITHUB_REPOS:
        try:
            r = subprocess.run(
                ["gh", "api", "-H", "Accept: application/vnd.github.v3.star+json",
                 "repos/{}/stargazers".format(full), "--jq", ".[].starred_at"],
                capture_output=True, text=True, timeout=40)
        except Exception:
            continue
        if r.returncode != 0:
            continue
        for line in (r.stdout or "").split("\n"):
            line = line.strip()
            if line:
                out[line[:10]] = out.get(line[:10], 0) + 1
    return out


def main():
    dry = "--dry-run" in sys.argv
    today = datetime.datetime.now(datetime.timezone.utc).date()

    print("collecting what the registries kept...")
    npm, npm_first = npm_daily(today.isoformat())
    pypi = pypi_daily()
    rel = releases()
    star_days = stars()

    days = sorted(set(npm) | set(pypi) | set(rel))
    if not days:
        print("backfill: no history available from any source")
        return 1

    print("  npm downloads     %d days from %s" % (len(npm), min(npm) if npm else "-"))
    print("  pypi downloads    %d days from %s"
          % (len(pypi), min(pypi) if pypi else "-"))
    print("  release events    %d days from %s" % (len(rel), min(rel)))
    print("  star events       %d days" % len(star_days))
    print()

    running_stars = 0
    written, skipped = 0, 0
    for day in days:
        running_stars += star_days.get(day, 0)
        path = os.path.join(DATA_DIR, day + ".json")

        if os.path.exists(path):
            try:
                with io.open(path, encoding="utf-8") as f:
                    if not json.load(f).get("backfilled"):
                        skipped += 1          # measured; never overwrite
                        continue
            except ValueError:
                pass

        npm_day = npm.get(day, {})
        pypi_day = pypi.get(day, {})
        summary = {}
        if npm_day:
            summary["npm_daily"] = sum(npm_day.values())
        if pypi_day:
            summary["pypi_daily"] = sum(pypi_day.values())
        if npm_day or pypi_day:
            summary["package_daily"] = (summary.get("npm_daily", 0) +
                                        summary.get("pypi_daily", 0))
        if running_stars:
            summary["github_stars"] = running_stars
        if rel.get(day):
            summary["releases_published"] = len(rel[day])

        doc = {
            "date": day,
            "generated_at": "backfilled",
            "mode": "backfill",
            "backfilled": True,
            "backfill_note": NOTE,
            "backfill_sources": sorted(
                (["npm"] if npm_day else []) +
                (["pypi"] if pypi_day else []) +
                (["releases"] if rel.get(day) else []) +
                (["github-stars"] if star_days.get(day) else [])),
            "summary": summary,
            "npm": [{"package": k, "registry": "npm", "daily": v}
                    for k, v in sorted(npm_day.items())],
            "pypi": [{"package": k, "registry": "PyPI", "daily": v}
                     for k, v in sorted(pypi_day.items())],
            "releases": sorted(rel.get(day, []),
                               key=lambda r: (r["registry"], r["package"])),
        }

        if dry:
            print("  would write %s  %s" % (day, ", ".join(doc["backfill_sources"])))
        else:
            with io.open(path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(doc, f, indent=2, sort_keys=True)
        written += 1

    print()
    print("backfill: %d day(s) %s, %d measured day(s) left alone"
          % (written, "to write" if dry else "written", skipped))
    print("          earliest is %s - nothing shipped before that" % days[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
