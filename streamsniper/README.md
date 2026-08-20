```
╔═════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                         ║
║  ███████╗████████╗██████╗ ███████╗ █████╗ ███╗   ███╗    ███████╗███╗   ██╗██╗██████╗ ███████╗██████╗   ║
║  ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗████╗ ████║    ██╔════╝████╗  ██║██║██╔══██╗██╔════╝██╔══██╗  ║
║  ███████╗   ██║   ██████╔╝█████╗  ███████║██╔████╔██║    ███████╗██╔██╗ ██║██║██████╔╝█████╗  ██████╔╝  ║
║  ╚════██║   ██║   ██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║    ╚════██║██║╚██╗██║██║██╔═══╝ ██╔══╝  ██╔══██╗  ║
║  ███████║   ██║   ██║  ██║███████╗██║  ██║██║ ╚═╝ ██║    ███████║██║ ╚████║██║██║     ███████╗██║  ██║  ║
║  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝    ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝  ║
║                                                                                                         ║
║                                      they go live, it is on the TV                                      ║
║                                                                                                         ║
╚═════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![Platform](https://img.shields.io/badge/platform-Debian%20%7C%20Ubuntu-lightgrey)](https://f-keys.com/streamsniper/)

---

## How It Works

```
Device boots → Standby clock shows on screen
      ↓
Every 5 minutes: checks your channel list, in order
      ↓
Stream goes live → VLC launches fullscreen via Streamlink (no ads)
      ↓
Stream ends → Standby clock returns
```

---

## What You Need Before Starting

1. Your N100 mini PC plugged into a display (HDMI)
2. Internet connection (WiFi or ethernet)
3. Ubuntu/Debian booted with a desktop (GNOME, XFCE, anything)

---

## Installation (one-time setup)

Open a terminal on the N100 and run:

```bash
# 1. Copy the streamsniper folder to your home directory
#    (USB drive, SCP, or just retype — your choice)

# 2. Go into the folder
cd ~/streamsniper

# 3. Run the installer
bash install.sh
```

The installer will:
- Install `streamlink`, `vlc`, and `python3-pygame` via apt
- Copy files to `~/streamsniper/`
- Register a systemd service that starts on every boot automatically

---

## Starting It

```bash
# Start right now
sudo systemctl start streamsniper@$USER

# Check it's running
sudo systemctl status streamsniper@$USER

# Watch the live log
tail -f ~/.streamsniper/sniper.log
```

---

## Stopping It

```bash
# Stop for now
sudo systemctl stop streamsniper@$USER

# Disable auto-start on boot
sudo systemctl disable streamsniper@$USER
```

---

## File Structure

```
streamsniper/
├── sniper.py              # Main watcher — polls Twitch, controls VLC
├── standby.py             # Fullscreen clock shown while offline
├── streamsniper@.service  # Systemd service (auto-start on boot)
├── install.sh             # One-command installer
└── README.md              # This file
```

---

## Logs

All activity is logged to:
```
~/.streamsniper/sniper.log
```

Example output:
```
2026-01-15 20:00:00  INFO     💤 all 3 offline — next check in 300s
2024-01-15 20:05:00  INFO     🟢 Stream detected — going live!
2024-01-15 20:05:03  INFO     Stream launched (PID 4821)
2024-01-15 22:31:00  INFO     🔴 Stream ended — returning to standby
```

---

## Changing Settings

### Which channels it watches

The installer asks you, and writes the answer here:

```
~/.streamsniper/channels.txt
```

One Twitch username per line. Order is priority — if two are live at once, the
one nearer the top gets the screen. Lines starting with `#` are ignored.

```
# my channels
somestreamer
anotherstreamer
```

**Edits apply at the next check.** No restart needed. An already-playing stream
is never interrupted by someone higher in the list coming online — it plays out,
then the list is scanned again from the top.

### Everything else

Edit `sniper.py` and change these lines at the top:

```python
CHECK_INTERVAL = 300     # Seconds between checks (300 = 5 min)
QUALITY        = "best"  # best, 1080p, 720p, 480p
```

After changing those, restart the service:
```bash
sudo systemctl restart streamsniper@$USER
```

---

## Troubleshooting

**Stream doesn't launch / VLC doesn't open**
```bash
# Test streamlink manually
streamlink twitch.tv/YOUR_CHANNEL best
```

**Standby screen doesn't show**
```bash
# Test pygame directly
DISPLAY=:0 python3 ~/streamsniper/standby.py
```

**Service won't start**
```bash
# See detailed error
journalctl -u streamsniper@$USER -n 50
```

**Display stays off**
```bash
# Check xset is available
xset dpms force on
```

---

## Optional: Auto-login + Auto-start (true kiosk mode)

To make the N100 fully autonomous (no keyboard needed after power-on):

```bash
# Enable auto-login in your display manager
# For GDM (GNOME):
sudo nano /etc/gdm3/custom.conf
# Set: AutomaticLoginEnable=true
#      AutomaticLogin=yourusername
```

The systemd service already starts automatically after that.

---

*StreamSniper — built for the one-device, one-purpose lifestyle.*

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
