```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║       ██████╗ ██╗     ██╗   ██╗███╗   ███╗██╗  ██╗██╗   ██╗██████╗         ║
║       ██╔══██╗██║     ██║   ██║████╗ ████║██║  ██║██║   ██║██╔══██╗        ║
║       ██████╔╝██║     ██║   ██║██╔████╔██║███████║██║   ██║██║  ██║        ║
║       ██╔═══╝ ██║     ██║   ██║██║╚██╔╝██║██╔══██║██║   ██║██║  ██║        ║
║       ██║     ███████╗╚██████╔╝██║ ╚═╝ ██║██║  ██║╚██████╔╝██████╔╝        ║
║       ╚═╝     ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝         ║
║                                                                            ║
║                      watch the fleet, not the screen                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

[![PyPI](https://img.shields.io/pypi/v/plumhud)](https://pypi.org/project/plumhud/) [![Python](https://img.shields.io/pypi/pyversions/plumhud)](https://pypi.org/project/plumhud/) [![License](https://img.shields.io/pypi/l/plumhud)](LICENSE)

Miner fleet monitor — a borderless overlay HUD that sits on top of whatever
you're doing, with alerts and history.

```
pip install plumhud
plumhud
```

```
plumhud          the overlay HUD and command center
plumhud check    poll once, print, exit — no window needed
plumhud where    where your config and history live
```

## What v4 changed, and why

**Nothing is invented any more.** v3 filled missing readings with
`random.randint()`, so a miner that answered without a hashrate displayed a
believable number you had no way to identify as fake. A field the miner did
not send is now `None`, renders as a dash, and is stored as NULL. "We did not
measure it" and "it is zero" are different facts and the display says which.

**Alert rules require a real measurement.** Removing the fabrication exposed
that the rules had never been written to survive a missing value — they would
have raised on the first `None`. A rule now stays quiet when the number never
arrived, and still fires on genuine problems.

**Your config stopped moving.** v3 wrote `plumhud_config.json` relative to the
working directory, so launching from two folders gave you two fleets — and
dropped a file containing your Discord webhook and Telegram token wherever you
happened to be, including repositories. Everything now lives in one per-user
directory (`plumhud where`), created owner-only. A v3 config found in the
current directory is adopted automatically.

**One poller, two faces.** Polling moved to
[`moonbeam-miner`](https://pypi.org/project/moonbeam-miner/), which the
terminal tool already used. That removed the private asyncio event loop, the
aiohttp session and its fallback path with no loss of speed — and means the
CLI and the HUD can never disagree about what a miner said.

**Zero required dependencies** beyond the shared core. `aiohttp` and
`requests` are gone; webhooks post through the standard library. Charts and
the logo are optional extras:

```
pip install "plumhud[charts]"
```

## What it does

Overlay HUD in four display modes (ring, bar, spark, grid) with an opacity
slider and five skins. A five-tab command center for miners, analytics,
alerts, skin and settings. Alert rules for offline, hashrate below, temperature
above and reject spikes, delivered to Discord or Telegram with a per-rule
cooldown. Every poll is written to a local SQLite database with 30-day
retention.

Talks to ESP-Miner and AxeOS devices — NerdMiner, Bitaxe and relatives — on
`http://<ip>/api/system/info`. Use `moonbeam scan` to find them.

## Requirements

Python 3.8+, and Tk for the window (bundled with Python on Windows and macOS;
`apt install python3-tk` on Debian and Ubuntu). `plumhud check` needs no
display at all.

---

```
  Vincent Gonzalez
  F-Keys  ·  https://f-keys.com
  ORCID 0009-0005-3640-014X
```

Part of [F-Keys](https://f-keys.com) — independent hardware, software
and internet products. See the [working log](https://f-keys.com/log/)
and [live status](https://f-keys.com/status/).
