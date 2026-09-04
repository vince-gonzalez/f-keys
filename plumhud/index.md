# PlumHUD

> Watch the fleet, not the screen.

Canonical: https://f-keys.com/plumhud/

A heads-up display for a fleet of miners. It sits on your desktop, goes quiet while everything is fine, and tells you the moment a machine stops earning.

**4.1.2** · pip install plumhud · Python 3.8+ with Tk · MIT

## What it does

A borderless overlay HUD that sits on top of whatever you are doing, with four display
modes, an opacity slider and five skins. A five-tab command center for miners, analytics,
alerts, skin and settings. Every poll is written to a local database with thirty-day
retention.

## Alerts

Rules for offline, hashrate below a floor, temperature above a ceiling and reject
spikes, delivered to Discord or Telegram with a per-rule cooldown.

## What version 4 changed

Nothing is invented any more. Version 3 filled missing readings with random numbers, so
a miner that answered without a hashrate displayed a believable figure you had no way to
identify as fake. A field the miner did not send is now shown as a dash and stored as
null, and alert rules stay quiet rather than reporting an absent measurement as a low one.

The config also stopped moving. It lives in one per-user directory, created owner-only,
because it holds a Discord webhook and a Telegram token.

## How it works

## What it does

## Specifications

| Field | Value |
| --- | --- |
| Name | Personal Ledger Utility Monitor, Heads-Up Display |
| Version | 4.1.2 |
| Licence | MIT |
| Install | pip install plumhud |
| Requires | Python 3.8+, Tk |
| Depends on | moonbeam-miner |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
