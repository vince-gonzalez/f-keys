#!/usr/bin/env python3
"""
============================================================
StreamSniper — config v1.1.0
Shared channel configuration for sniper.py and standby.py.
F-Keys | www.f-keys.com
------------------------------------------------------------
WORKFLOW STACK:
  1. load_channels() reads ~/.streamsniper/channels.txt
  2. First run writes a commented template and returns []
  3. Blank lines and # comments are ignored
  4. Usernames are lowercased and de-duplicated, order preserved
     (order IS priority — the first live channel wins)
------------------------------------------------------------
CHANGE LOG v1.0.0 -> v1.1.0
  - NEW FILE: channel config extracted out of sniper.py
  - CHANGED: single hardcoded CHANNEL -> user-editable list
============================================================
"""

from pathlib import Path

CONFIG_DIR    = Path.home() / ".streamsniper"
CHANNELS_FILE = CONFIG_DIR / "channels.txt"

TEMPLATE = """\
# StreamSniper — channels to watch
#
# One Twitch username per line. Order is priority: if more than one
# is live, the one nearest the top gets the screen.
#
# Lines starting with # are ignored. Save the file and restart with:
#   sudo systemctl restart streamsniper@$USER
#
# Example:
#   somestreamer
#   anotherstreamer

"""


def _write_template():
    """Create the config dir and a commented, empty channels file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CHANNELS_FILE.exists():
        CHANNELS_FILE.write_text(TEMPLATE, encoding="utf-8")


def load_channels():
    """
    Return the watch list in priority order.
    Empty list means the user has not configured anything yet.
    """
    if not CHANNELS_FILE.exists():
        _write_template()
        return []

    channels = []
    for raw in CHANNELS_FILE.read_text(encoding="utf-8").splitlines():
        name = raw.split("#", 1)[0].strip().lower()
        if name and name not in channels:
            channels.append(name)
    return channels


def describe():
    """Short human string for logs and the standby screen."""
    channels = load_channels()
    if not channels:
        return "no channels configured"
    if len(channels) == 1:
        return channels[0]
    return f"{channels[0]} +{len(channels) - 1} more"
