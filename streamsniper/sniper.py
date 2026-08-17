#!/usr/bin/env python3
"""
============================================================
StreamSniper v1.1.0
Auto-launch Twitch streams in fullscreen kiosk mode.
Watches one or more channels and launches/kills VLC via Streamlink.
F-Keys | www.f-keys.com
------------------------------------------------------------
WORKFLOW STACK:
  1. Boot: read watch list from ~/.streamsniper/channels.txt
  2. Standby clock on screen while everything is offline
  3. Every CHECK_INTERVAL: scan the list in priority order
  4. First live channel -> streamlink | VLC fullscreen, ads disabled
  5. Stream ends -> back to standby, rescan from the top
------------------------------------------------------------
CHANGE LOG v1.0.0 -> v1.1.0
  - CHANGED: hardcoded CHANNEL -> user-editable list (config.py)
  - ADDED: multi-channel watch, list order is priority
  - ADDED: watch list re-read every poll, so edits apply without restart
  - ADDED: clear guidance in the log when nothing is configured
  - FIXED: Helix URL was a module constant bound to one channel
------------------------------------------------------------
PROTECTED INVARIANT: an already-playing stream is never interrupted
by a higher-priority channel coming online. It plays until it ends.
============================================================
"""

import subprocess
import time
import sys
import os
import signal
import logging
import urllib.request
import urllib.error
import json
from datetime import datetime
from pathlib import Path

from config import load_channels, CHANNELS_FILE

# ── CONFIG ────────────────────────────────────────────────────────────────────
CHECK_INTERVAL  = 300          # seconds between polls (5 minutes)
QUALITY         = "best"       # streamlink quality: best, 1080p, 720p, 480p

# Twitch requires a Client-ID for the Helix API.
# If you have a Client-ID, put it here and set USE_HELIX = True
CLIENT_ID       = ""
USE_HELIX       = False        # flip to True if you have a Client-ID

# ── LOGGING ──────────────────────────────────────────────────────────────────
LOG_FILE = Path.home() / ".streamsniper" / "sniper.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("streamsniper")

# ── STATE ─────────────────────────────────────────────────────────────────────
vlc_process     = None
standby_proc    = None
current_channel = None         # channel currently on screen, None when standby

# ── TWITCH CHECK ─────────────────────────────────────────────────────────────
def is_live_helix(channel: str) -> bool:
    """Check via Twitch Helix API (requires Client-ID)."""
    url = f"https://api.twitch.tv/helix/streams?user_login={channel}"
    req = urllib.request.Request(
        url,
        headers={
            "Client-ID": CLIENT_ID,
            "Accept": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return len(data.get("data", [])) > 0
    except Exception as e:
        log.warning(f"Helix API error for {channel}: {e}")
        return False


def is_live_streamlink(channel: str) -> bool:
    """
    Use streamlink itself to check if a channel is live.
    This is the no-API-key fallback — streamlink handles auth internally.
    Returns True if the stream is accessible.
    """
    try:
        result = subprocess.run(
            ["streamlink", f"twitch.tv/{channel}", "--stream-url", QUALITY],
            capture_output=True, text=True, timeout=20
        )
        return result.returncode == 0
    except FileNotFoundError:
        log.error("streamlink not found. Run: sudo apt install streamlink")
        return False
    except subprocess.TimeoutExpired:
        log.warning(f"streamlink check timed out for {channel}")
        return False
    except Exception as e:
        log.warning(f"streamlink check error for {channel}: {e}")
        return False


def channel_is_live(channel: str) -> bool:
    if USE_HELIX and CLIENT_ID:
        return is_live_helix(channel)
    return is_live_streamlink(channel)


def find_live_channel(channels):
    """Return the first live channel in priority order, or None."""
    for channel in channels:
        if channel_is_live(channel):
            return channel
    return None


# ── DISPLAY CONTROL ───────────────────────────────────────────────────────────
def wake_display():
    """Turn on the connected display."""
    try:
        subprocess.run(["xset", "dpms", "force", "on"], check=False)
        subprocess.run(["xset", "s", "reset"], check=False)
    except Exception as e:
        log.warning(f"Could not wake display: {e}")


def sleep_display():
    """Turn off the connected display."""
    try:
        subprocess.run(["xset", "dpms", "force", "off"], check=False)
    except Exception as e:
        log.warning(f"Could not sleep display: {e}")


# ── STANDBY SCREEN ────────────────────────────────────────────────────────────
def launch_standby():
    """Launch the standby screen (fullscreen clock/status display)."""
    global standby_proc
    kill_standby()
    standby_script = Path(__file__).parent / "standby.py"
    if standby_script.exists():
        try:
            env = {**os.environ, "DISPLAY": ":0"}
            standby_proc = subprocess.Popen(
                [sys.executable, str(standby_script)],
                env=env
            )
            log.info("Standby screen launched")
        except Exception as e:
            log.warning(f"Could not launch standby screen: {e}")


def kill_standby():
    global standby_proc
    if standby_proc and standby_proc.poll() is None:
        standby_proc.terminate()
        try:
            standby_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            standby_proc.kill()
        standby_proc = None
        log.info("Standby screen closed")


# ── STREAM CONTROL ────────────────────────────────────────────────────────────
def launch_stream(channel: str):
    """Launch a Twitch stream via streamlink piped into VLC fullscreen."""
    global vlc_process
    kill_stream()
    kill_standby()
    wake_display()

    log.info(f"🔴 {channel} is LIVE — launching stream...")

    cmd = [
        "streamlink",
        f"twitch.tv/{channel}",
        QUALITY,
        "--player", "vlc --fullscreen --no-video-title-show --play-and-exit",
        "--twitch-disable-ads",
        "--twitch-low-latency",
    ]

    try:
        env = {**os.environ, "DISPLAY": ":0"}
        vlc_process = subprocess.Popen(cmd, env=env)
        log.info(f"Stream launched (PID {vlc_process.pid})")
    except FileNotFoundError:
        log.error("streamlink not found. Install with: sudo apt install streamlink")
    except Exception as e:
        log.error(f"Failed to launch stream: {e}")


def kill_stream():
    global vlc_process
    if vlc_process and vlc_process.poll() is None:
        vlc_process.terminate()
        try:
            vlc_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            vlc_process.kill()
        vlc_process = None
        log.info("Stream closed")

    # Also kill any orphaned VLC/streamlink processes
    subprocess.run(["pkill", "-f", "vlc"], capture_output=True)
    subprocess.run(["pkill", "-f", "streamlink"], capture_output=True)


def stream_is_running() -> bool:
    return vlc_process is not None and vlc_process.poll() is None


# ── SIGNAL HANDLING ───────────────────────────────────────────────────────────
def handle_exit(signum, frame):
    log.info("Shutting down StreamSniper...")
    kill_stream()
    kill_standby()
    sleep_display()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def main():
    global current_channel

    channels = load_channels()

    log.info("=" * 60)
    log.info("  StreamSniper v1.1.0 started")
    log.info(f"  Watching: {', '.join(channels) if channels else 'NOTHING YET'}")
    log.info(f"  Check interval: {CHECK_INTERVAL}s | Quality: {QUALITY}")
    log.info("=" * 60)

    if not channels:
        log.warning(f"No channels configured. Add Twitch usernames to: {CHANNELS_FILE}")

    launch_standby()
    warned_empty = not channels

    while True:
        try:
            # Re-read every poll so edits to channels.txt apply without a restart
            channels = load_channels()
            now = datetime.now().strftime("%H:%M")

            if not channels:
                if not warned_empty:
                    log.warning(f"Watch list is empty. Add usernames to: {CHANNELS_FILE}")
                    warned_empty = True
                if current_channel:
                    kill_stream()
                    current_channel = None
                    launch_standby()
                time.sleep(CHECK_INTERVAL)
                continue
            warned_empty = False

            if current_channel:
                # Something is on screen. Leave it alone until it ends.
                if stream_is_running() and channel_is_live(current_channel):
                    log.info(f"[{now}] ✅ {current_channel} running normally")
                elif channel_is_live(current_channel):
                    log.info(f"[{now}] VLC stopped unexpectedly — relaunching {current_channel}")
                    launch_stream(current_channel)
                else:
                    log.info(f"[{now}] 🔴 {current_channel} ended — returning to standby")
                    kill_stream()
                    current_channel = None
                    launch_standby()
            else:
                # Nothing playing. Scan the list in priority order.
                live = find_live_channel(channels)
                if live:
                    log.info(f"[{now}] 🟢 {live} detected — going live!")
                    launch_stream(live)
                    current_channel = live
                else:
                    log.info(f"[{now}] 💤 all {len(channels)} offline — next check in {CHECK_INTERVAL}s")

        except Exception as e:
            log.error(f"Unexpected error in main loop: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
