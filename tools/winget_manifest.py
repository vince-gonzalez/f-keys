#!/usr/bin/env python3
"""
============================================================
winget_manifest — build the three manifests from a release
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS

Key-J 1.5.0 reached winget by hand: download the installer,
hash it, write three YAML files, and get one of them wrong.
`InstallerType: nsis` was rejected by `winget validate`, which
knows it as `nullsoft`. Every future version was going to be
that same hour, with the same chance of the same mistake.

So the manifests are generated from the release that actually
exists. The URL and the hash come from the published asset
rather than from someone retyping them, which removes the one
error a reviewer cannot catch: a manifest that validates
perfectly against the wrong binary.

Run:  python tools/winget_manifest.py 1.6.0
      python tools/winget_manifest.py 1.6.0 --out ../wm

Then, on Windows:
      winget validate --manifest <out>
and open the PR against microsoft/winget-pkgs.
============================================================
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request

REPO = "zengineco/f-keys"
PACKAGE = "FKeysCreative.KeyJ"
PUBLISHER = "F-Keys Creative LLC"
SCHEMA = "1.12.0"

# winget's own name for the installer NSIS produces. It is not "nsis", and
# that is the single thing this file exists to stop anyone typing again.
INSTALLER_TYPE = "nullsoft"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "f-keys-tools"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def release(version):
    tag = "keyj-v" + version
    data = json.loads(fetch(
        "https://api.github.com/repos/{}/releases/tags/{}".format(REPO, tag)))
    for asset in data.get("assets", []):
        if asset["name"].endswith(".exe"):
            return tag, asset["browser_download_url"], asset["name"], data
    raise SystemExit("  no .exe asset on {} - was the Windows build published?"
                     .format(tag))


def sha256_of(url):
    """Hash the asset that is actually published, not a local copy of it."""
    h = hashlib.sha256()
    req = urllib.request.Request(url, headers={"User-Agent": "f-keys-tools"})
    with urllib.request.urlopen(req, timeout=300) as r:
        total = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest().upper(), total


VERSION_YAML = """# yaml-language-server: $schema=https://aka.ms/winget-manifest.version.{schema}.schema.json

PackageIdentifier: {pkg}
PackageVersion: {ver}
DefaultLocale: en-US
ManifestType: version
ManifestVersion: {schema}
"""

INSTALLER_YAML = """# yaml-language-server: $schema=https://aka.ms/winget-manifest.installer.{schema}.schema.json

PackageIdentifier: {pkg}
PackageVersion: {ver}
Platform:
- Windows.Desktop
MinimumOSVersion: 10.0.17763.0
InstallerType: {itype}
Scope: user
UpgradeBehavior: install
ReleaseDate: {date}
Installers:
- Architecture: x64
  InstallerUrl: {url}
  InstallerSha256: {sha}
ManifestType: installer
ManifestVersion: {schema}
"""

LOCALE_YAML = """# yaml-language-server: $schema=https://aka.ms/winget-manifest.defaultLocale.{schema}.schema.json

PackageIdentifier: {pkg}
PackageVersion: {ver}
PackageLocale: en-US
Publisher: {publisher}
PublisherUrl: https://f-keys.com
PublisherSupportUrl: https://github.com/{repo}/issues
Author: Vincent Gonzalez
PackageName: Key-J
PackageUrl: https://f-keys.com/keyj/
License: Proprietary
LicenseUrl: https://github.com/{repo}/blob/main/keyj/LICENSE
Copyright: Copyright (c) 2026 F-Keys Creative LLC
ShortDescription: Turns your keyboard into an instrument - every keystroke plays a note, in any application.
Description: |-
  Key-J plays a musical note on every keystroke, in any application, and turns
  guitar tablature into something you can play by typing.

  Paste a tab, choose a tuning, and Key-J converts the frets to notes. In
  sequence mode every key plays the next note of that run, so the pitches are
  handled and what is left to you is timing and feel. Eight tunings including
  drop D, DADGAD, seven-string and bass, with a capo offset.

  Also here: a 61-key on-screen keyboard, a step grid with nine kits, seven
  tone presets, six play styles, a scrolling staff, and export to WAV as either
  the sequence at a tempo or a recording of what you typed. Sequences save and
  load as plain text.

  Key-J is free to use. It collects nothing and makes no network requests.
Moniker: keyj
Tags:
- audio
- guitar
- keyboard
- midi
- music
- synthesizer
- tablature
ReleaseNotesUrl: https://github.com/{repo}/releases/tag/{tag}
Documentations:
- DocumentLabel: Manual
  DocumentUrl: https://f-keys.com/keyj/manual/
- DocumentLabel: Privacy
  DocumentUrl: https://f-keys.com/keyj/privacy/
ManifestType: defaultLocale
ManifestVersion: {schema}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("version", help="the released version, e.g. 1.6.0")
    ap.add_argument("--out", default=None,
                    help="directory to write into (default: build/winget/<version>)")
    args = ap.parse_args()

    tag, url, name, data = release(args.version)
    print("  release  {}".format(tag))
    print("  asset    {}".format(name))
    print("  hashing the published asset...")
    sha, size = sha256_of(url)
    print("  sha256   {}".format(sha))
    print("  size     {:,} bytes".format(size))

    date = (data.get("published_at") or "")[:10]
    fields = dict(schema=SCHEMA, pkg=PACKAGE, ver=args.version, url=url,
                  sha=sha, date=date, repo=REPO, tag=tag,
                  publisher=PUBLISHER, itype=INSTALLER_TYPE)

    out = args.out or os.path.join("build", "winget", args.version)
    os.makedirs(out, exist_ok=True)
    files = {
        PACKAGE + ".yaml": VERSION_YAML,
        PACKAGE + ".installer.yaml": INSTALLER_YAML,
        PACKAGE + ".locale.en-US.yaml": LOCALE_YAML,
    }
    for fname, template in files.items():
        path = os.path.join(out, fname)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(template.format(**fields))
        print("  wrote    {}".format(path))

    print()
    print("  Next, on Windows:")
    print("    winget validate --manifest {}".format(os.path.abspath(out)))
    print()
    print("  Then copy into a fork of microsoft/winget-pkgs at:")
    print("    manifests/f/FKeysCreative/KeyJ/{}/".format(args.version))
    print("  and open the PR. Leave the CLA and install-test boxes unticked")
    print("  unless they are actually true.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
