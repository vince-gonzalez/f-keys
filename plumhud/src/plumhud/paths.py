"""
============================================================
plumhud.paths — one home for config and history
F-Keys | www.f-keys.com
------------------------------------------------------------
v3.0.0 wrote plumhud_config.json and plumhud.db relative to
the working directory. Two consequences, both bad:

  - Running plumhud from two folders gave you two fleets, and
    the second one looked like you had lost your miners.
  - That file holds the Discord webhook and Telegram token, so
    it landed in whatever directory you happened to be in.
    Including, easily, a git repository.

Everything now lives under one per-user directory, and the
config file is created with owner-only permissions because of
what is in it.
============================================================
"""

import os
import stat

__all__ = ["APP_DIR", "CONFIG_FILE", "DB_FILE", "LOG_FILE", "harden"]


def _app_dir():
    """Per-user application directory, following each platform's habit."""
    override = os.environ.get("PLUMHUD_HOME")
    if override:
        return override
    home = os.path.expanduser("~")
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
        return os.path.join(base, "PlumHUD")
    if os.uname().sysname == "Darwin" if hasattr(os, "uname") else False:
        return os.path.join(home, "Library", "Application Support", "PlumHUD")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    return os.path.join(base, "plumhud")


APP_DIR = _app_dir()
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
DB_FILE = os.path.join(APP_DIR, "plumhud.db")
LOG_FILE = os.path.join(APP_DIR, "plumhud.log")

os.makedirs(APP_DIR, exist_ok=True)


def harden(path=CONFIG_FILE):
    """
    Restrict the config to its owner. It stores a Discord webhook URL and a
    Telegram bot token, either of which is enough for someone else to post
    as you. Best effort: Windows ignores the POSIX bits, and a failure here
    must never stop the app from starting.
    """
    try:
        if os.path.exists(path):
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def migrate_legacy():
    """
    v3.0.0 wrote its config beside whatever directory you launched from.
    If one is sitting in the current directory and we have no config yet,
    move it in rather than silently starting with an empty fleet - losing
    someone's miner list is a worse first impression than a stray file.
    Returns the path it adopted, or None.
    """
    legacy = os.path.join(os.getcwd(), "plumhud_config.json")
    if os.path.exists(CONFIG_FILE) or not os.path.exists(legacy):
        return None
    try:
        import shutil
        shutil.copy2(legacy, CONFIG_FILE)
        harden(CONFIG_FILE)
        return legacy
    except OSError:
        return None
