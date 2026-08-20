```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                            ║
║                      ███████╗      ██╗  ██╗███████╗██╗   ██╗███████╗                       ║
║                      ██╔════╝      ██║ ██╔╝██╔════╝╚██╗ ██╔╝██╔════╝                       ║
║                      █████╗  █████╗█████╔╝ █████╗   ╚████╔╝ ███████╗                       ║
║                      ██╔══╝  ╚════╝██╔═██╗ ██╔══╝    ╚██╔╝  ╚════██║                       ║
║                      ██║           ██║  ██╗███████╗   ██║   ███████║                       ║
║                      ╚═╝           ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝                       ║
║                                                                                            ║
║                one repository, and everything the studio ships is inside it                ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```

[f-keys.com](https://f-keys.com) is the company site, and this repository is
the site, the products it lists, and the tools that keep the two honest.

## What is in here

| | |
|---|---|
| `index.html`, `*.html`, `win98.css` | the site, generated |
| `keyj/`, `moonbeam/`, `plumhud/`, `streamsniper/` | shipping products, each with its own README |
| `leadseer/`, `pixelstaff/`, `qv/`, `remapwrap/`, `micdrop/`, `wikipolish/` | product pages |
| `gonzalgo/`, `papers/` | the indexes and the deposited work |
| `log/`, `status/` | the working log and the measured numbers |
| `tools/` | everything that builds or checks the above |

## The site is generated, not edited

`tools/buildsite.py` holds the catalogue and emits all eighteen pages through
one shell, so a product exists in exactly one place. Editing a generated
`.html` file directly means the next build overwrites it.

```
python tools/buildsite.py     the site
python tools/buildlog.py      the working log
python tools/snapshot.py      the numbers behind /status/
python tools/readme.py --verify   the README standard, checked
```

## Two things are enforced rather than remembered

`tools/brand-gate.py` fails the build if a dissolved brand name reaches a page
a person will read, while allowing the identifiers that cannot change without
breaking every link. It runs in CI.

`.github/workflows/release.yml` refuses to publish a version the package does
not claim, on both the desktop and the Python branch, because a tag and a
manifest disagreeing ships the wrong version under the right name.

---

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║      ███████╗      ██╗  ██╗███████╗██╗   ██╗███████╗       ║
║      ██╔════╝      ██║ ██╔╝██╔════╝╚██╗ ██╔╝██╔════╝       ║
║      █████╗  █████╗█████╔╝ █████╗   ╚████╔╝ ███████╗       ║
║      ██╔══╝  ╚════╝██╔═██╗ ██╔══╝    ╚██╔╝  ╚════██║       ║
║      ██║           ██║  ██╗███████╗   ██║   ███████║       ║
║      ╚═╝           ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝       ║
║                                                            ║
║               ·   C  R  E  A  T  I  V  E   ·               ║
║                                                            ║
║          ────────────────────────────────────────          ║
║                                                            ║
║                      Vincent Gonzalez                      ║
║                         f-keys.com                         ║
║                 ORCID 0009-0005-3640-014X                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

Part of [F-Keys](https://f-keys.com) — independent hardware, software
and internet products. See the [working log](https://f-keys.com/log/)
and [live status](https://f-keys.com/status/).
