```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                            ║
║       ██████╗ ███████╗███╗   ███╗ █████╗ ██████╗ ██╗    ██╗██████╗  █████╗ ██████╗         ║
║       ██╔══██╗██╔════╝████╗ ████║██╔══██╗██╔══██╗██║    ██║██╔══██╗██╔══██╗██╔══██╗        ║
║       ██████╔╝█████╗  ██╔████╔██║███████║██████╔╝██║ █╗ ██║██████╔╝███████║██████╔╝        ║
║       ██╔══██╗██╔══╝  ██║╚██╔╝██║██╔══██║██╔═══╝ ██║███╗██║██╔══██╗██╔══██║██╔═══╝         ║
║       ██║  ██║███████╗██║ ╚═╝ ██║██║  ██║██║     ╚███╔███╔╝██║  ██║██║  ██║██║             ║
║       ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝      ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝             ║
║                                                                                            ║
║                        your phone is already the extra row of keys                         ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```

[![status](https://img.shields.io/badge/status-alpha-e8a04a)](https://f-keys.com/remapwrap/)
[![node](https://img.shields.io/badge/node-16%2B-3c873a)](https://nodejs.org)

<img src="assets/logo.png" alt="RemapWrap" width="160" align="right">

**The company is named after this.** RemapWrap began as *F-Keys* &mdash; an extra
row of keys, on glass you already own &mdash; and the name outgrew the product.
The product then went missing for five months, surviving in one zip file in a
folder called "zip to sort". This is that code, recovered.

## What it does

Runs a small server on your PC. Scan the QR code with your phone and the phone
becomes a drag-and-drop grid of keys that fire **real OS-level keystrokes**. The
software you are driving does not know RemapWrap exists, which is the point: it
works with everything, because it is indistinguishable from a keyboard.

No app on the phone. No hardware. A Stream Deck costs $150 and lives in a
drawer; this is the device already in your hand.

```
npm install
npm start
```

Then open the dashboard the server prints, and scan the code with your phone.
Both devices need to be on the same network.

| | |
|---|---|
| `remapwrap-server.js` | the bridge: serves the pages, relays WebSocket messages, fires keystrokes |
| `dashboard.html` | the PC side: layout builder, pairing QR, live feed |
| `controller.html` | the phone side: the keypad itself |

Ports **7331** (HTTP) and **7332** (WebSocket) must be open on the local
network. Keystroke injection is handled by `@nut-tree-fork/nut-js`.

## Alpha, honestly

This is v0.1.0 and it has never been packaged. It runs from source, the layout
format is JSON that is edited live, and nothing about it has been hardened. It
is published because a design that exists only in a zip file is a design that
gets lost.

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
