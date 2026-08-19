# moonbeam

Find the NerdMiners on your network and read their vitals, from the terminal.

```
pip install moonbeam-miner
moonbeam
```

No dependencies. Standard library only, so the install cannot fail on
someone else's package.

## What it does

```
moonbeam            the miners it already knows, polled now
moonbeam scan       sweep this subnet and remember what answered
moonbeam watch      refresh until you stop it
moonbeam show <ip>  everything one miner reported
```

The first run has nothing saved, so it offers to scan. Anything that
answers is remembered in `~/.moonbeam/miners.json`.

```
  #   NAME             ADDRESS             HASHRATE     TEMP   ACCEPTED    UPTIME
  ------------------------------------------------------------------------------
  1   Moonbeam-01      192.168.1.42        486 GH/s     54°C     18,422     1d 2h
  2   Moonbeam-02      192.168.1.51              —         —         31         —
  3   192.168.1.77     192.168.1.77         offline

  2 miners answering · total 486 GH/s (1 did not report a hashrate)
```

## A dash means the miner did not say

It does not mean zero, and it is never a plausible number standing in for
one that never arrived. A fabricated hashrate that looks real is worse
than a visible gap, because nothing tells you it is wrong. The summary
line counts how many devices declined to report rather than quietly
averaging them in.

## What it talks to

ESP-Miner and AxeOS devices — NerdMiner, Bitaxe and relatives — answer on
`http://<ip>/api/system/info`. Discovery probes every host on your /24
concurrently and keeps whatever responds with that shape.

## Use it as a library

The polling core is separate from the terminal output, so a GUI can share
it:

```python
from moonbeam import scan, poll

for m in scan():
    print(m["alias"], m["hashrate"])
```

MIT licensed. Part of [F-Keys](https://f-keys.com).
