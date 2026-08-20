#!/usr/bin/env python3
# =============================================================================
# Author: Vincent Gonzalez | © 2026 F-Keys | www.f-keys.com
# Project: Plum HUD
# Version: v3.0.0
# Description: Crypto miner fleet monitor — overlay HUD + command center
# Target OS: Windows 10/11 (primary), macOS/Linux best-effort
# =============================================================================

# ===== WORKFLOW STACK =====
# File:         plumhud.py
# Brand:        F-Keys
# Author:       Vincent Gonzalez
# Version:      v3.0.0
# Boot Order:
#   1. load_config()               → reads/creates plumhud_config.json
#   2. db_init()                   → creates/migrates plumhud.db SQLite schema
#   3. PlumHUDApp.__init__()       → root Tk (hidden), loads config + DB
#   4. AlertEngine()               → boots before poll engine
#   5. HUDWindow()                 → borderless overlay, topmost, canvas-drawn
#   6. CommandCenter()             → main control panel (5 tabs)
#   7. _start_async_engine()       → AsyncPollEngine + asyncio bg thread
#   8. _queue_drain_loop()         → after(500) main-thread stats consumer
# Section Map:
#   ~1–80     CONFIG BLOCK + constants
#   ~81–165   Utility / logging / config IO
#   ~166–280  DB layer (SQLite — readings + alerts_log)
#   ~281–410  Poll engine (threads via moonbeam.miners)
#   ~411–530  Alert engine + Discord/Telegram delivery
#   ~531–560  Canvas helpers
#   ~561–780  HUDWindow (ring / bar / spark / grid modes)
#   ~781–1100 CommandCenter (5 tabs)
#   ~1101–1200 PlumHUDApp root orchestrator
#   ~1201+    Entry point
# External Dependencies:
#   tkinter     — stdlib (ships with CPython on Windows)
#   (polling and webhooks are standard library)
#   Pillow      — pip install Pillow         (logo, tray icon)
#   matplotlib  — pip install matplotlib    (analytics chart)
#   pystray     — pip install pystray       (optional — system tray)
# Layout Target:  HUD 400x440px, CommandCenter 780x700px
# Browser Target: N/A — desktop Tkinter app
# ===== END WORKFLOW STACK =====

# ===== ASSET MANIFEST =====
# ./assets/logo.png          — Plum HUD logo PNG (auto-resized to 58x58)  // optional
# ./assets/sound_accept.wav  — Played on new accepted share               // MISSING: optional
# ./assets/sound_reject.wav  — Played on new rejected share               // MISSING: optional
# plumhud_config.json        — Auto-created on first run
# plumhud.db                 — SQLite analytics DB, auto-created on first run
# ===== END ASSET MANIFEST =====

# ===== LAST STABLE: v2.0.0 — 2026 =====
# Sync threading poller, no DB, no alert engine, no skin modes, no async.
# Fixed from v1: missing math import, thread-safe after() UI refresh.
# ===== END LAST STABLE =====

from moonbeam import miners as _mb

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog
import threading
import time
import json
import os
import math
import socket
import random
import traceback
import sqlite3
import asyncio
import datetime
import queue
from concurrent.futures import ThreadPoolExecutor


def _post_json(url, payload, timeout=6):
    """
    POST JSON with the standard library. requests was pulled in for two
    webhook calls; urllib does the same job and keeps the install at zero
    dependencies. Returns True when the endpoint accepted it.
    """
    import urllib.request, urllib.error
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "plumhud"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 300
    except Exception as e:                      # noqa: BLE001
        dlog("webhook post failed: {}".format(e))
        return False

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.backends.backend_tkagg as mpl_tkagg
    MPL_OK = True
except ImportError:
    MPL_OK = False


# =============================================================================
# ===== CONFIG BLOCK =====
# All tuneable constants — edit freely.
# No logic below reads these from anywhere other than here and _default_config().
# =============================================================================

# Config and DB live in one place per user, not wherever you happened to be
# standing. Relative paths meant running plumhud from two folders gave you
# two different fleets - and dropped a file containing your Discord webhook
# token into whatever directory that was, including repositories.
from . import paths as _paths               # noqa: E402
from .paths import CONFIG_FILE, DB_FILE     # noqa: E402
LOGO_FILE          = _paths.logo()            # packaged plum, or None
#   was "./assets/logo.png" - relative to the launch directory, so the
#   logo was never found unless you happened to start from the right
#   folder, and app.py skips a logo it cannot find without saying so.
POLL_TIMEOUT       = 2.5                     # Seconds to wait on one miner
POLL_INTERVAL      = 5                       # Seconds between full fleet polls
SCAN_TIMEOUT       = 1.0                     # TCP ping timeout per host (seconds)
SCAN_THREADS       = 64                      # Parallel threads during subnet scan
HUD_W              = 400                     # HUD overlay width px
HUD_H              = 440                     # HUD overlay height px
CMD_W              = 780                     # Command center window width px
CMD_H              = 700                     # Command center window height px
DB_RETENTION_DAYS  = 30                      # Auto-prune readings older than N days
ALERT_COOLDOWN_SEC = 120                     # Min seconds between repeat alerts per rule/miner
VERSION            = "v3.0.0"               # Version string shown in UI
DEV_MODE           = False                   # True = verbose console logging

# Skin presets — applied wholesale to cfg["theme"]
SKIN_PRESETS = {
    "Plum Dark": {
        "bg": "#0e0c14", "panel": "#1a1724", "panel2": "#241f35",
        "fg": "#e8e0f5", "fg2": "#9b93b8",
        "accent": "#c97eff", "accent2": "#7dd8f0",
        "online": "#26d47a", "warn": "#ffe971", "error": "#e05c5c",
        "shadow": "#080610", "border": "#3a2f5c", "seg_gap": "#0e0c14",
    },
    "Plum Matte": {
        "bg": "#1c1520", "panel": "#28202e", "panel2": "#352840",
        "fg": "#eeddf8", "fg2": "#a090b8",
        "accent": "#d48fff", "accent2": "#90d4e8",
        "online": "#3de88a", "warn": "#f5d060", "error": "#e86060",
        "shadow": "#100a14", "border": "#4a3870", "seg_gap": "#1c1520",
    },
    "F-Keys Cyan": {
        "bg": "#070e10", "panel": "#0d1c22", "panel2": "#112830",
        "fg": "#d0f4ff", "fg2": "#6ab8cc",
        "accent": "#7dd8f0", "accent2": "#c97eff",
        "online": "#26d47a", "warn": "#ffe971", "error": "#e05c5c",
        "shadow": "#030a0e", "border": "#1a4050", "seg_gap": "#070e10",
    },
    "Carbon": {
        "bg": "#111111", "panel": "#1e1e1e", "panel2": "#282828",
        "fg": "#e8e8e8", "fg2": "#888888",
        "accent": "#00d4aa", "accent2": "#ff8c42",
        "online": "#00cc66", "warn": "#ffcc00", "error": "#ff4444",
        "shadow": "#080808", "border": "#333333", "seg_gap": "#111111",
    },
    "Terminal Green": {
        "bg": "#050e05", "panel": "#0a1a0a", "panel2": "#0f260f",
        "fg": "#a0ffb0", "fg2": "#508855",
        "accent": "#00ff80", "accent2": "#80ffcc",
        "online": "#00ff80", "warn": "#ffff44", "error": "#ff4444",
        "shadow": "#020802", "border": "#1a4020", "seg_gap": "#050e05",
    },
}

FONT_MAIN   = "Segoe UI"
FONT_MONO   = "Consolas"
FONT_HEADER = "Segoe UI"

HUD_MODES  = ["ring", "bar", "spark", "grid"]
ALERT_TYPES = ["miner_offline", "hash_below", "temp_above", "reject_spike"]

# ===== END CONFIG BLOCK =====


# =============================================================================
# UTILITY
# =============================================================================

def dlog(msg):
    """DEV_MODE logger. READS: DEV_MODE"""
    if DEV_MODE:
        print(f"[PLUMHUD {datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")


def ts_now():
    """Return current UTC timestamp as ISO 8601 string."""
    return datetime.datetime.utcnow().isoformat()


def load_config():
    _paths.migrate_legacy()
    """
    Load config from disk. Merges missing keys forward from defaults.
    RETURNS: dict
    """
    if not os.path.exists(CONFIG_FILE):
        dlog("No config — using defaults.")
        return _default_config()
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        default = _default_config()
        for k, v in default.items():
            if k not in data:
                data[k] = v
        return data
    except Exception as e:
        dlog(f"load_config failed: {e}")
        return _default_config()


def save_config(cfg):
    """Persist config dict to CONFIG_FILE. READS/WRITES: CONFIG_FILE"""
    _paths.harden(CONFIG_FILE)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        dlog(f"save_config failed: {e}")


def _default_config():
    """Return a factory-fresh default config dict."""
    return {
        "miners":           [],
        "opacity":          0.92,
        "hud_corner":       "topright",
        "hud_x":            None,
        "hud_y":            None,
        "hud_mode":         "ring",
        "hud_skin":         "Plum Dark",
        "show_hash":        True,
        "show_temp":        True,
        "show_shares":      True,
        "show_ip":          False,
        "sound":            True,
        "font_size":        13,
        "theme":            dict(SKIN_PRESETS["Plum Dark"]),
        "alert_rules":      [],
        "discord_webhook":  "",
        "telegram_token":   "",
        "telegram_chat_id": "",
        "coin_price_usd":   0.0,
        "power_cost_kwh":   0.10,
    }


# =============================================================================
# DB LAYER
# =============================================================================

_db_conn = None   # Module-level connection — written from bg thread, read from main


def db_init():
    """
    Open/create SQLite DB with WAL mode and create tables if missing.
    WRITES: _db_conn, DB_FILE
    """
    global _db_conn
    try:
        _db_conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        _db_conn.execute("PRAGMA journal_mode=WAL")
        _db_conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT    NOT NULL,
                ip        TEXT    NOT NULL,
                alias     TEXT,
                hash_mh   REAL    DEFAULT 0,
                temp_c    REAL    DEFAULT 0,
                shares    INTEGER DEFAULT 0,
                rejected  INTEGER DEFAULT 0,
                status    TEXT    DEFAULT 'Offline'
            )
        """)
        _db_conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT    NOT NULL,
                rule_type TEXT,
                miner_ip  TEXT,
                message   TEXT
            )
        """)
        _db_conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings (ts)")
        _db_conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_ip ON readings (ip)")
        _db_conn.commit()
        dlog("DB initialised.")
    except Exception as e:
        dlog(f"db_init failed: {e}")
        _db_conn = None


def db_write_reading(stat):
    """
    Insert one poll result into readings table.
    READS: _db_conn  WRITES: readings table
    """
    if not _db_conn:
        return
    try:
        _db_conn.execute(
            "INSERT INTO readings (ts,ip,alias,hash_mh,temp_c,shares,rejected,status) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (ts_now(), stat["ip"], stat["alias"], stat["hash"],
             stat["temp"], stat["shares"], stat["rejected"], stat["status"])
        )
        _db_conn.commit()
    except Exception as e:
        dlog(f"db_write_reading failed: {e}")


def db_write_alert(rule_type, miner_ip, message):
    """Insert alert event into alerts_log. READS: _db_conn"""
    if not _db_conn:
        return
    try:
        _db_conn.execute(
            "INSERT INTO alerts_log (ts,rule_type,miner_ip,message) VALUES (?,?,?,?)",
            (ts_now(), rule_type, miner_ip, message)
        )
        _db_conn.commit()
    except Exception as e:
        dlog(f"db_write_alert failed: {e}")


def db_prune():
    """Delete readings older than DB_RETENTION_DAYS."""
    if not _db_conn:
        return
    try:
        cutoff = (datetime.datetime.utcnow() -
                  datetime.timedelta(days=DB_RETENTION_DAYS)).isoformat()
        _db_conn.execute("DELETE FROM readings WHERE ts < ?", (cutoff,))
        _db_conn.commit()
        dlog(f"DB pruned before {cutoff}")
    except Exception as e:
        dlog(f"db_prune failed: {e}")


def db_get_history(ip, hours=1):
    """
    Fetch recent readings for one miner.
    RETURNS: list of (ts, hash_mh, temp_c, shares, rejected) tuples
    """
    if not _db_conn:
        return []
    try:
        since = (datetime.datetime.utcnow() -
                 datetime.timedelta(hours=hours)).isoformat()
        cur = _db_conn.execute(
            "SELECT ts, hash_mh, temp_c, shares, rejected FROM readings "
            "WHERE ip=? AND ts>=? ORDER BY ts ASC",
            (ip, since)
        )
        return cur.fetchall()
    except Exception as e:
        dlog(f"db_get_history failed: {e}")
        return []


def db_get_all_history(hours=6):
    """
    Fetch recent readings for all miners grouped by IP.
    RETURNS: dict {ip: [(ts, hash_mh, temp_c, shares, rejected), ...]}
    """
    if not _db_conn:
        return {}
    try:
        since = (datetime.datetime.utcnow() -
                 datetime.timedelta(hours=hours)).isoformat()
        cur = _db_conn.execute(
            "SELECT ip, ts, hash_mh, temp_c, shares, rejected "
            "FROM readings WHERE ts>=? ORDER BY ts ASC",
            (since,)
        )
        result = {}
        for row in cur.fetchall():
            ip = row[0]
            if ip not in result:
                result[ip] = []
            result[ip].append(row[1:])
        return result
    except Exception as e:
        dlog(f"db_get_all_history failed: {e}")
        return {}


def db_get_alert_log(limit=100):
    """
    Fetch most recent alert log entries.
    RETURNS: list of (ts, rule_type, miner_ip, message) tuples
    """
    if not _db_conn:
        return []
    try:
        cur = _db_conn.execute(
            "SELECT ts, rule_type, miner_ip, message FROM alerts_log "
            "ORDER BY ts DESC LIMIT ?", (limit,)
        )
        return cur.fetchall()
    except Exception as e:
        dlog(f"db_get_alert_log failed: {e}")
        return []


# =============================================================================
# ASYNC POLL ENGINE
# =============================================================================

def _is_num(v):
    """True only for a real measurement. Booleans are not measurements."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _to_hud(m, ip):
    """
    Adapt a moonbeam reading to the shape the HUD and DB expect.

    None is preserved. A miner that answered without a hashrate reads as
    None here and renders as a dash, because a plausible number you cannot
    tell is invented is worse than a visible gap. v3.0.0 filled these with
    random.randint() and the display was indistinguishable from real data.
    """
    if not m or m.get("offline"):
        return {"alias": "Miner_{}".format(ip.split(".")[-1]), "ip": ip,
                "hash": None, "temp": None, "shares": None, "rejected": None,
                "status": "Offline", "uptime": None}
    return {
        "alias":    m.get("alias") or "Miner_{}".format(ip.split(".")[-1]),
        "ip":       ip,
        "hash":     m.get("hashrate"),
        "temp":     m.get("temp"),
        "shares":   m.get("accepted"),
        "rejected": m.get("rejected"),
        "status":   "Online",
        "uptime":   m.get("uptime_s"),
    }


def poll_miner(ip):
    """One miner, via the shared moonbeam core. Never raises."""
    try:
        return _to_hud(_mb.poll(ip, timeout=POLL_TIMEOUT), ip)
    except Exception as e:                      # noqa: BLE001 - a poll must never kill the loop
        dlog("poll {}: {}".format(ip, e))
        return _to_hud(None, ip)


def poll_fleet(ips):
    """
    Every miner at once. moonbeam.miners does the concurrency with a thread
    pool from the standard library, so aiohttp and requests are no longer
    needed to read a miner.
    """
    try:
        readings = _mb.poll_many(list(ips), timeout=POLL_TIMEOUT)
    except Exception as e:                      # noqa: BLE001
        dlog("fleet poll: {}".format(e))
        return [_to_hud(None, ip) for ip in ips]
    return [_to_hud(r, r.get("ip")) for r in readings]


class PollEngine:
    """
    Polls the fleet on a timer in one daemon thread, writes each reading to
    SQLite, and hands the batch to the main thread through a queue.

    v3.0.0 ran a private asyncio event loop with an aiohttp session and a
    ThreadPoolExecutor fallback. moonbeam.miners already does the
    concurrency with the standard library, so the event loop, the optional
    dependency and the fallback path all went away with no loss of speed.

    DEPENDS ON: db_write_reading(), stats_queue, get_miners_cb()
    """

    def __init__(self, get_miners_cb, stats_queue, alert_engine):
        self._get_miners = get_miners_cb
        self._queue      = stats_queue
        self._alert      = alert_engine
        self._running    = False
        self._prune_ctr  = 0
        self._thread     = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        dlog("PollEngine started.")

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                miners = self._get_miners()
                if miners:
                    stats = poll_fleet([m["ip"] for m in miners])
                    # Keep the name the user gave a miner when the device
                    # only reports a generic one.
                    for i, st in enumerate(stats):
                        generic = "Miner_{}".format(st["ip"].split(".")[-1])
                        if st.get("alias") in (None, "", generic, st["ip"]):
                            st["alias"] = miners[i].get("alias", st.get("alias"))
                    for st in stats:
                        db_write_reading(st)
                    self._queue.put(stats)
                    self._alert.evaluate(stats)
                    self._prune_ctr += 1
                    if self._prune_ctr >= 100:
                        db_prune()
                        self._prune_ctr = 0
            except Exception as e:                  # noqa: BLE001
                dlog("poll cycle: {}".format(e))    # a bad cycle must not end the loop
            for _ in range(int(POLL_INTERVAL * 10)):
                if not self._running:
                    return
                time.sleep(0.1)


def tcp_ping(ip, port=80, timeout=SCAN_TIMEOUT):
    """TCP connectivity check. RETURNS: bool"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except Exception as e:
        dlog(f"tcp_ping {ip}: {e}")
        return False


def scan_subnet_parallel(subnet_prefix, progress_cb=None):
    """
    Scan subnet_prefix.1–254 using SCAN_THREADS parallel threads.
    progress_cb(completed, 254) called every 4 hosts if provided.
    RETURNS: list of responding IP strings
    """
    results = []
    lock    = threading.Lock()
    ctr     = [0]

    def _check(i):
        ip = f"{subnet_prefix}.{i}"
        if tcp_ping(ip):
            with lock:
                results.append(ip)
        with lock:
            ctr[0] += 1
            if progress_cb and ctr[0] % 4 == 0:
                progress_cb(ctr[0], 254)

    with ThreadPoolExecutor(max_workers=SCAN_THREADS) as ex:
        list(ex.map(_check, range(1, 255)))
    return results


# =============================================================================
# ALERT ENGINE
# =============================================================================

class AlertEngine:
    """
    Evaluates alert rules after each poll cycle.
    Dispatches to: UI toast, Discord webhook, Telegram bot.

    DEPENDS ON: get_cfg_cb(), db_write_alert()
    READS:  cfg["alert_rules"], _last_fired (cooldown), _prev_stats (delta)
    WRITES: _last_fired, _prev_stats, alerts_log via db_write_alert()
    """

    def __init__(self, get_cfg_cb, ui_notify_cb=None):
        self._get_cfg    = get_cfg_cb
        self._ui_notify  = ui_notify_cb
        self._last_fired = {}   # {rule_key: unix_timestamp}
        self._prev_stats = {}   # {ip: last_stat_dict}

    def evaluate(self, stats):
        """
        Run all enabled rules against current stats list.
        Called from bg thread — only DB + HTTP are safe here; no Tk calls.
        """
        cfg   = self._get_cfg()
        rules = cfg.get("alert_rules", [])

        for stat in stats:
            ip   = stat["ip"]
            prev = self._prev_stats.get(ip, {})

            for rule in rules:
                if not rule.get("enabled", True):
                    continue
                rtype  = rule.get("type")
                thresh = rule.get("threshold", 0)
                rkey   = f"{rtype}:{ip}"
                now    = time.time()

                if now - self._last_fired.get(rkey, 0) < ALERT_COOLDOWN_SEC:
                    continue

                msg = None

                if rtype == "miner_offline" and stat["status"] == "Offline":
                    if prev.get("status") != "Offline":
                        msg = f"MINER OFFLINE: {stat['alias']} ({ip})"

                # A rule cannot fire on a reading that never arrived. Until
                # v4 these values could not be None, because the poller
                # substituted random numbers for them - so the comparisons
                # below were never given a None and were never written to
                # survive one. Now they can be, and "we did not measure it"
                # must not be reported as "it is low".
                elif rtype == "hash_below" and stat["status"] != "Offline":
                    if _is_num(stat.get("hash")) and stat["hash"] < thresh:
                        msg = (f"HASH RATE LOW: {stat['alias']} — "
                               f"{stat['hash']} GH/s (threshold {thresh})")

                elif rtype == "temp_above":
                    if _is_num(stat.get("temp")) and stat["temp"] > thresh:
                        msg = (f"HIGH TEMP: {stat['alias']} — "
                               f"{stat['temp']}°C (threshold {thresh}°C)")

                elif rtype == "reject_spike":
                    cur, was = stat.get("rejected"), prev.get("rejected")
                    if _is_num(cur) and _is_num(was):
                        delta = cur - was
                        if delta >= thresh and delta > 0:
                            msg = (f"REJECT SPIKE: {stat['alias']} — "
                                   f"+{delta} rejections")

                if msg:
                    self._last_fired[rkey] = now
                    db_write_alert(rtype, ip, msg)
                    dlog(f"ALERT FIRED: {msg}")
                    self._dispatch(msg, rule, cfg)

            self._prev_stats[ip] = dict(stat)

    def _dispatch(self, message, rule, cfg):
        """Send alert to all enabled channels."""
        if self._ui_notify:
            self._ui_notify(message)
        if rule.get("discord", False):
            self._send_discord(message, cfg)
        if rule.get("telegram", False):
            self._send_telegram(message, cfg)

    def _send_discord(self, message, cfg):
        """POST rich embed to Discord webhook. READS: cfg["discord_webhook"]"""
        url = cfg.get("discord_webhook", "").strip()
        if not url:
            return
        try:
            payload = {
                "username": "Plum HUD",
                "embeds": [{
                    "title":       "Plum HUD Alert",
                    "description": message,
                    "color":       0xc97eff,
                    "footer": {
                        "text": f"Plum HUD {VERSION} — {ts_now()[:19].replace('T', ' ')} UTC"
                    },
                }]
            }
            if not _post_json(url, payload):
                dlog("Discord webhook did not accept the message")
        except Exception as e:
            dlog(f"_send_discord failed: {e}")

    def _send_telegram(self, message, cfg):
        """POST message to Telegram bot. READS: cfg["telegram_token"], cfg["telegram_chat_id"]"""
        token   = cfg.get("telegram_token",   "").strip()
        chat_id = cfg.get("telegram_chat_id", "").strip()
        if not token or not chat_id:
            return
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            if not _post_json(url, {"chat_id": chat_id, "text": message}):
                dlog("Telegram did not accept the message")
        except Exception as e:
            dlog(f"_send_telegram failed: {e}")

    def test_discord(self, cfg):
        """Fire test message to Discord. RETURNS: None (errors suppressed)"""
        self._send_discord(
            f"Plum HUD {VERSION} — Discord alert connection test.", cfg)

    def test_telegram(self, cfg):
        """Fire test message to Telegram. RETURNS: None (errors suppressed)"""
        self._send_telegram(
            f"Plum HUD {VERSION} — Telegram alert connection test.", cfg)


# =============================================================================
# CANVAS HELPERS
# =============================================================================

def _rounded_rect(canvas, x1, y1, x2, y2, radius=12, **kwargs):
    """Draw a smooth rounded rectangle on a tk.Canvas via polygon."""
    pts = [
        x1+radius, y1,  x2-radius, y1,
        x2, y1,         x2, y1+radius,
        x2, y2-radius,  x2, y2,
        x2-radius, y2,  x1+radius, y2,
        x1, y2,         x1, y2-radius,
        x1, y1+radius,  x1, y1,
    ]
    fill    = kwargs.pop("fill", "")
    outline = kwargs.pop("outline", "")
    width   = kwargs.pop("width", 1)
    canvas.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=width)


def _sparkline(canvas, x, y, w, h, values, color, bg):
    """
    Draw a mini sparkline inside bounding box (x,y) → (x+w, y+h).
    DEPENDS ON: tk.Canvas
    """
    if len(values) < 2:
        canvas.create_rectangle(x, y, x+w, y+h, fill=bg, outline="")
        return
    canvas.create_rectangle(x, y, x+w, y+h, fill=bg, outline="")
    mx   = max(values) or 1
    mn   = min(values)
    span = (mx - mn) or 1
    pts  = []
    for i, v in enumerate(values):
        px = x + int(i / (len(values) - 1) * w)
        py = y + h - int((v - mn) / span * h)
        pts.extend([px, py])
    if len(pts) >= 4:
        canvas.create_line(pts, fill=color, width=1.5, smooth=True)


# =============================================================================
# HUD OVERLAY WINDOW
# =============================================================================

class HUDWindow(tk.Toplevel):
    """
    Borderless, always-on-top overlay drawn entirely on a tk.Canvas.
    Supports 4 display modes: ring, bar, spark, grid.
    Opacity fully configurable (0.1 = near-invisible, 1.0 = fully opaque).

    DEPENDS ON: PlumHUDApp.get_stats(), db_get_history(), SKIN_PRESETS
    READS: cfg["opacity"], cfg["hud_mode"], cfg["theme"], cfg["show_*"]
    """

    def __init__(self, root, cfg, get_stats_cb):
        super().__init__(root)
        self.root       = root
        self.cfg        = cfg
        self.get_stats  = get_stats_cb
        self.theme      = cfg["theme"]
        self._drag_off  = (0, 0)
        self._running   = True
        self._logo_img  = None

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha",   cfg["opacity"])
        self.resizable(False, False)
        self.configure(bg=self.theme["bg"])
        self.geometry(self._calc_geom())

        self.canvas = tk.Canvas(
            self, width=HUD_W, height=HUD_H,
            bg=self.theme["bg"], highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>",       self._drag_start)
        self.canvas.bind("<B1-Motion>",      self._drag_move)
        self.canvas.bind("<Button-3>",       self._right_click)
        self.canvas.bind("<Double-Button-1>",self._cycle_mode)

        self._load_logo()
        self.after(300, self._draw_loop)

    # ------------------------------------------------------------------
    # Geometry / drag
    # ------------------------------------------------------------------

    def _calc_geom(self):
        """Restore saved position or calculate from hud_corner config."""
        sx, sy  = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h, p = HUD_W, HUD_H, 18
        if self.cfg.get("hud_x") is not None and self.cfg.get("hud_y") is not None:
            return f"{w}x{h}+{self.cfg['hud_x']}+{self.cfg['hud_y']}"
        corners = {
            "topright":    f"{w}x{h}+{sx-w-p}+{p}",
            "topleft":     f"{w}x{h}+{p}+{p}",
            "bottomright": f"{w}x{h}+{sx-w-p}+{sy-h-70}",
            "bottomleft":  f"{w}x{h}+{p}+{sy-h-70}",
        }
        return corners.get(self.cfg.get("hud_corner", "topright"), corners["topright"])

    def _drag_start(self, event):
        self._drag_off = (event.x, event.y)

    def _drag_move(self, event):
        x = self.winfo_pointerx() - self._drag_off[0]
        y = self.winfo_pointery() - self._drag_off[1]
        self.geometry(f"+{x}+{y}")
        self.cfg["hud_x"] = x
        self.cfg["hud_y"] = y

    def _right_click(self, event):
        """Right-click opens Command Center."""
        try:
            self.root.cmd.deiconify()
            self.root.cmd.lift()
        except Exception:
            pass

    def _cycle_mode(self, event):
        """Double-click cycles display mode ring→bar→spark→grid→ring."""
        modes   = HUD_MODES
        current = self.cfg.get("hud_mode", "ring")
        idx     = modes.index(current) if current in modes else 0
        self.cfg["hud_mode"] = modes[(idx + 1) % len(modes)]
        dlog(f"HUD mode → {self.cfg['hud_mode']}")

    # ------------------------------------------------------------------
    # Logo
    # ------------------------------------------------------------------

    def _load_logo(self):
        """Load and resize logo PNG. Silently skips if missing or PIL not installed."""
        if not PIL_OK or not LOGO_FILE or not os.path.exists(LOGO_FILE):
            return
        try:
            img = Image.open(LOGO_FILE).convert("RGBA").resize((58, 58), Image.LANCZOS)
            self._logo_img = ImageTk.PhotoImage(img)
        except Exception as e:
            dlog(f"_load_logo: {e}")

    # ------------------------------------------------------------------
    # Draw loop
    # ------------------------------------------------------------------

    def _draw_loop(self):
        """Scheduled render tick — runs every 600ms via after()."""
        if not self._running:
            return
        try:
            self._render()
        except Exception as e:
            dlog(f"_draw_loop error: {e}")
        self.after(600, self._draw_loop)

    def _render(self):
        """
        Clear canvas and dispatch to mode renderer.
        READS: cfg["hud_mode"], get_stats()
        """
        c  = self.canvas
        th = self.theme
        c.delete("all")

        miners = self.get_stats()
        mode   = self.cfg.get("hud_mode", "ring")

        # Outer panel
        _rounded_rect(c, 4, 4, HUD_W-4, HUD_H-4,
                      radius=20, fill=th["panel"], outline=th["border"], width=2)

        # Header
        c.create_text(HUD_W//2, 20, text="PLUM HUD",
                      font=(FONT_HEADER, 12, "bold"),
                      fill=th["accent"], anchor="center")
        c.create_text(HUD_W//2, 36,
                      text=f"{VERSION}  ·  {mode.upper()}  ·  {len(miners)} miners",
                      font=(FONT_MONO, 8), fill=th["fg2"], anchor="center")

        if   mode == "ring":  self._render_ring(c, th, miners)
        elif mode == "bar":   self._render_bar(c, th, miners)
        elif mode == "spark": self._render_spark(c, th, miners)
        elif mode == "grid":  self._render_grid(c, th, miners)

        # Footer
        c.create_text(HUD_W//2, HUD_H-10,
                      text="drag · right-click=panel · dbl-click=mode",
                      font=(FONT_MAIN, 7), fill=th["fg2"], anchor="center")

    # ------------------------------------------------------------------
    # Ring mode
    # ------------------------------------------------------------------

    def _render_ring(self, c, th, miners):
        """Pie-ring with one segment per miner. Summary in center donut."""
        N  = len(miners)
        cx = HUD_W // 2
        cy = HUD_H // 2
        r_outer = 145
        r_inner = 70

        if N == 0:
            c.create_text(cx, cy, text="No Miners\nConfigured",
                          font=(FONT_MAIN, 15, "bold"),
                          fill=th["fg2"], justify="center")
            self._render_summary_row(c, th, miners, HUD_H - 54)
            return

        gap_deg = max(2.0, 8.0 / N)
        seg_deg = (360.0 / N) - gap_deg

        for i, m in enumerate(miners):
            start = (i * 360.0 / N) + gap_deg / 2
            col   = self._seg_color(m, th)
            c.create_arc(cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer,
                         start=start, extent=seg_deg,
                         fill=col, outline=th["seg_gap"], width=4, style=tk.PIE)

        # Inner donut
        c.create_oval(cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner,
                      fill=th["panel"], outline=th["border"], width=2)

        # Labels on segments (suppressed when >12 miners — text would overlap)
        if N <= 12:
            for i, m in enumerate(miners):
                start   = (i * 360.0 / N) + gap_deg / 2
                mid_rad = math.radians(start + seg_deg / 2)
                mid_r   = r_inner + (r_outer - r_inner) / 2 + 4
                lx      = cx + mid_r * math.cos(mid_rad)
                ly      = cy - mid_r * math.sin(mid_rad)
                alias   = m["alias"][:7]
                c.create_text(lx+1, ly+1, text=alias,
                              font=(FONT_MONO, 8, "bold"),
                              fill=th["shadow"], anchor="center")
                c.create_text(lx, ly, text=alias,
                              font=(FONT_MONO, 8, "bold"),
                              fill="#ffffff", anchor="center")

        # Center content
        if self._logo_img:
            c.create_image(cx, cy - 8, image=self._logo_img, anchor="center")
        else:
            c.create_text(cx, cy - 10, text="🍑", font=(FONT_MAIN, 24),
                          anchor="center")

        self._render_summary_row(c, th, miners, HUD_H - 54)

    # ------------------------------------------------------------------
    # Bar mode
    # ------------------------------------------------------------------

    def _render_bar(self, c, th, miners):
        """Horizontal hash-rate bars, one per miner."""
        if not miners:
            c.create_text(HUD_W//2, HUD_H//2, text="No Miners",
                          font=(FONT_MAIN, 14), fill=th["fg2"], anchor="center")
            return

        top      = 52
        bottom   = HUD_H - 60
        n        = len(miners)
        bar_h    = max(14, min(32, (bottom - top - n * 4) // n))
        gap      = 4
        max_hash = max((m["hash"] for m in miners), default=1) or 1
        bar_x    = 92
        bar_maxw = HUD_W - bar_x - 70

        for i, m in enumerate(miners):
            y   = top + i * (bar_h + gap)
            col = self._seg_color(m, th)
            bw  = int((m["hash"] / max_hash) * bar_maxw)
            alias = m["alias"][:10]

            c.create_text(bar_x - 5, y + bar_h // 2, text=alias,
                          font=(FONT_MONO, 8), fill=th["fg2"], anchor="e")

            _rounded_rect(c, bar_x, y, bar_x + bar_maxw, y + bar_h,
                          radius=4, fill=th["panel2"], outline="")
            if bw > 4:
                _rounded_rect(c, bar_x, y, bar_x + bw, y + bar_h,
                              radius=4, fill=col, outline="")

            c.create_text(bar_x + bar_maxw + 6, y + bar_h // 2,
                          text=str(m["hash"]),
                          font=(FONT_MONO, 8, "bold"), fill=th["accent"], anchor="w")

        self._render_summary_row(c, th, miners, HUD_H - 54)

    # ------------------------------------------------------------------
    # Spark mode
    # ------------------------------------------------------------------

    def _render_spark(self, c, th, miners):
        """Mini sparkline per miner using last 1h DB history."""
        if not miners:
            c.create_text(HUD_W//2, HUD_H//2, text="No Miners",
                          font=(FONT_MAIN, 14), fill=th["fg2"], anchor="center")
            return

        top     = 52
        bottom  = HUD_H - 60
        n       = len(miners)
        cell_h  = max(38, (bottom - top) // max(n, 1))
        spark_w = HUD_W - 120
        label_x = 90

        for i, m in enumerate(miners):
            y       = top + i * cell_h
            col     = self._seg_color(m, th)
            history = db_get_history(m["ip"], hours=1)
            vals    = [row[1] for row in history] if history else [m["hash"]]

            c.create_text(label_x - 5, y + cell_h // 2 - 8,
                          text=m["alias"][:10],
                          font=(FONT_MONO, 8, "bold"), fill=th["fg"], anchor="e")
            c.create_text(label_x - 5, y + cell_h // 2 + 8,
                          text=m["status"][:7],
                          font=(FONT_MONO, 7), fill=col, anchor="e")

            _sparkline(c, label_x, y + 4, spark_w, cell_h - 8,
                       vals, col, th["panel2"])

            c.create_text(HUD_W - 10, y + cell_h // 2,
                          text=f"{m['hash']} MH",
                          font=(FONT_MONO, 8), fill=th["accent"], anchor="e")

        self._render_summary_row(c, th, miners, HUD_H - 54)

    # ------------------------------------------------------------------
    # Grid mode
    # ------------------------------------------------------------------

    def _render_grid(self, c, th, miners):
        """Compact status tiles — up to 32 miners in a 4-column grid."""
        top    = 48
        cols   = 4
        pad    = 8
        tile_w = (HUD_W - pad * 2 - (cols - 1) * pad) // cols
        tile_h = 42

        for i, m in enumerate(miners):
            row = i // cols
            col = i % cols
            x   = pad + col * (tile_w + pad)
            y   = top + row * (tile_h + pad)
            col_color = self._seg_color(m, th)

            _rounded_rect(c, x, y, x + tile_w, y + tile_h,
                          radius=6, fill=th["panel2"], outline=col_color, width=1)

            c.create_text(x + tile_w // 2, y + 13,
                          text=m["alias"][:8],
                          font=(FONT_MONO, 8, "bold"), fill="#ffffff", anchor="center")
            c.create_text(x + tile_w // 2, y + 28,
                          text=f"{m['hash']} MH",
                          font=(FONT_MONO, 7), fill=col_color, anchor="center")

        self._render_summary_row(c, th, miners, HUD_H - 54)

    # ------------------------------------------------------------------
    # Shared summary row
    # ------------------------------------------------------------------

    def _render_summary_row(self, c, th, miners, y):
        """4-column footer: miners online, total hash, accepts, rejects."""
        total_hash   = sum(m["hash"]     for m in miners)
        total_shares = sum(m["shares"]   for m in miners)
        total_rej    = sum(m["rejected"] for m in miners)
        online       = sum(1 for m in miners if m["status"] in ("Online", "Demo"))

        c.create_line(16, y - 6, HUD_W - 16, y - 6, fill=th["border"], width=1)

        col_w   = (HUD_W - 32) // 4
        entries = [
            ("MINERS", f"{online}/{len(miners)}"),
            ("HASH",   f"{total_hash} MH"),
            ("ACCEPT", str(total_shares)),
            ("REJECT", str(total_rej)),
        ]
        for idx, (label, val) in enumerate(entries):
            sx = 16 + col_w * idx + col_w // 2
            c.create_text(sx, y + 4,  text=label, font=(FONT_MAIN, 7),
                          fill=th["fg2"], anchor="center")
            c.create_text(sx, y + 20, text=val,   font=(FONT_MONO, 10, "bold"),
                          fill=th["accent"], anchor="center")

    # ------------------------------------------------------------------
    # Segment color helper
    # ------------------------------------------------------------------

    def _seg_color(self, miner, th):
        """RETURNS: color hex string for miner status."""
        if miner["status"] == "Offline":
            return th["error"]
        if miner["status"] == "Demo":
            return th.get("accent2", th["accent"])
        if miner.get("temp", 0) >= 70:
            return th["warn"]
        return th["online"]

    # ------------------------------------------------------------------
    # Public config update
    # ------------------------------------------------------------------

    def apply_config(self, cfg):
        """Hot-apply config without destroying window."""
        self.cfg   = cfg
        self.theme = cfg["theme"]
        self.canvas.configure(bg=cfg["theme"]["bg"])
        self.configure(bg=cfg["theme"]["bg"])
        self.attributes("-alpha", cfg["opacity"])

    def stop(self):
        self._running = False


# =============================================================================
# COMMAND CENTER — 5 TABS
# =============================================================================

class CommandCenter(tk.Toplevel):
    """
    Main control window with 5 tabs:
      Tab 1 — Miners   : live treeview, add / remove / scan
      Tab 2 — Analytics: matplotlib history chart
      Tab 3 — Alerts   : rule builder + alert log
      Tab 4 — Skin     : presets, opacity, mode, metrics toggles, accent color
      Tab 5 — Settings : webhooks, power cost, font, sound

    DEPENDS ON: PlumHUDApp.get_stats(), PlumHUDApp.apply_config(),
                AlertEngine, db_get_all_history(), db_get_alert_log()
    """

    def __init__(self, root, cfg, apply_config_cb, get_stats_cb,
                 alert_engine, get_miners_cb):
        super().__init__(root)
        self.root          = root
        self.cfg           = cfg
        self.theme         = cfg["theme"]
        self.apply_config  = apply_config_cb
        self.get_stats     = get_stats_cb
        self.alert_engine  = alert_engine
        self.get_miners    = get_miners_cb

        self.title(f"Plum HUD — Command Center  {VERSION}")
        self.geometry(f"{CMD_W}x{CMD_H}")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.resizable(True, True)
        self.configure(bg=self.theme["bg"])

        self._chart_widget = None

        self._build_ui()
        self._style_ttk()
        self.refresh_miner_list()

    def _on_close(self):
        self.withdraw()

    # ------------------------------------------------------------------
    # Dark TTK styles
    # ------------------------------------------------------------------

    def _style_ttk(self):
        th = self.theme
        s  = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview",
            background=th["panel"], fieldbackground=th["panel"],
            foreground=th["fg"], rowheight=26,
            font=(FONT_MONO, 10), borderwidth=0)
        s.configure("Treeview.Heading",
            background=th["panel2"], foreground=th["accent"],
            font=(FONT_MAIN, 10, "bold"), relief="flat")
        s.map("Treeview",
              background=[("selected", th["border"])],
              foreground=[("selected", th["accent"])])
        s.configure("TNotebook",
            background=th["bg"], borderwidth=0)
        s.configure("TNotebook.Tab",
            background=th["panel2"], foreground=th["fg2"],
            padding=[14, 6], font=(FONT_MAIN, 10))
        s.map("TNotebook.Tab",
              background=[("selected", th["panel"])],
              foreground=[("selected", th["accent"])])

    # ------------------------------------------------------------------
    # Top-level UI layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        th = self.theme

        # Header
        hdr = tk.Frame(self, bg=th["panel2"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="🍑  PLUM HUD  COMMAND CENTER",
                 font=(FONT_HEADER, 16, "bold"),
                 bg=th["panel2"], fg=th["accent"], pady=10
                 ).pack(side="left", padx=18)
        tk.Label(hdr, text=VERSION,
                 font=(FONT_MONO, 10), bg=th["panel2"], fg=th["fg2"]
                 ).pack(side="right", padx=18)

        # Notebook
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=8, pady=8)

        def _tab(label):
            f = tk.Frame(self._nb, bg=th["bg"])
            self._nb.add(f, text=label)
            return f

        t_miners    = _tab("  ⬡ Miners  ")
        t_analytics = _tab("  📈 Analytics  ")
        t_alerts    = _tab("  ⚠ Alerts  ")
        t_skin      = _tab("  🎨 Skin  ")
        t_settings  = _tab("  ⚙ Settings  ")

        self._build_miners_tab(t_miners)
        self._build_analytics_tab(t_analytics)
        self._build_alerts_tab(t_alerts)
        self._build_skin_tab(t_skin)
        self._build_settings_tab(t_settings)

    # ------------------------------------------------------------------ TAB 1: Miners

    def _build_miners_tab(self, parent):
        th = self.theme

        tb = tk.Frame(parent, bg=th["bg"], pady=6)
        tb.pack(fill="x", padx=10)

        for label, cmd, bg in [
            ("⟳  Scan Subnet",  self._scan_subnet,       th["accent2"]),
            ("＋  Add Miner",    self._add_miner,          th["online"]),
            ("✕  Remove",        self._remove_miner,       th["error"]),
            ("↓  Export CSV",   self._export_csv,         th["warn"]),
            ("↻  Refresh",      self.refresh_miner_list,  th["accent"]),
        ]:
            tk.Button(tb, text=label, command=cmd, bg=bg, fg=th["bg"],
                      relief="flat", padx=10, pady=5,
                      font=(FONT_MAIN, 10, "bold"), cursor="hand2"
                      ).pack(side="left", padx=3)

        # Scan progress bar (hidden until scan runs)
        self._scan_prog_var = tk.DoubleVar(value=0)
        self._scan_bar = ttk.Progressbar(parent, variable=self._scan_prog_var,
                                          maximum=254)

        # Treeview
        tf = tk.Frame(parent, bg=th["bg"])
        tf.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        cols   = ["Alias", "IP", "Hash (MH/s)", "Temp (°C)",
                  "Shares", "Rejected", "Uptime", "Status"]
        widths = [100, 130, 100, 90, 80, 80, 70, 80]
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ------------------------------------------------------------------ TAB 2: Analytics

    def _build_analytics_tab(self, parent):
        th = self.theme

        ctrl = tk.Frame(parent, bg=th["bg"], pady=6)
        ctrl.pack(fill="x", padx=10)

        tk.Label(ctrl, text="Window:", bg=th["bg"], fg=th["fg2"],
                 font=(FONT_MAIN, 10)).pack(side="left", padx=(0, 6))
        self._analytics_hours = tk.IntVar(value=6)
        for h, lbl in [(1,"1h"), (6,"6h"), (12,"12h"), (24,"24h")]:
            tk.Radiobutton(ctrl, text=lbl, variable=self._analytics_hours, value=h,
                           bg=th["bg"], fg=th["fg"], selectcolor=th["panel2"],
                           activebackground=th["bg"], font=(FONT_MAIN, 10)
                           ).pack(side="left", padx=2)

        tk.Label(ctrl, text="Metric:", bg=th["bg"], fg=th["fg2"],
                 font=(FONT_MAIN, 10)).pack(side="left", padx=(14, 6))
        self._analytics_metric = tk.StringVar(value="hash_mh")
        for val, lbl in [("hash_mh","Hash"),("temp_c","Temp"),("shares","Shares")]:
            tk.Radiobutton(ctrl, text=lbl, variable=self._analytics_metric, value=val,
                           bg=th["bg"], fg=th["fg"], selectcolor=th["panel2"],
                           activebackground=th["bg"], font=(FONT_MAIN, 10)
                           ).pack(side="left", padx=2)

        tk.Button(ctrl, text="⟳  Render", command=self._render_analytics_chart,
                  bg=th["accent"], fg=th["bg"], relief="flat",
                  padx=10, pady=4, font=(FONT_MAIN, 10, "bold"), cursor="hand2"
                  ).pack(side="left", padx=12)

        self._analytics_frame = tk.Frame(parent, bg=th["bg"])
        self._analytics_frame.pack(fill="both", expand=True, padx=10, pady=4)

        if not MPL_OK:
            tk.Label(self._analytics_frame,
                     text="matplotlib not installed\npip install matplotlib",
                     bg=th["bg"], fg=th["fg2"],
                     font=(FONT_MAIN, 12), justify="center").pack(pady=50)

    # ------------------------------------------------------------------ TAB 3: Alerts

    def _build_alerts_tab(self, parent):
        th = self.theme

        # Rule builder
        rb = tk.LabelFrame(parent, text="  Add Alert Rule  ",
                           bg=th["panel"], fg=th["accent"],
                           font=(FONT_MAIN, 11, "bold"), padx=10, pady=8)
        rb.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(rb, text="Type:", bg=th["panel"], fg=th["fg2"],
                 font=(FONT_MAIN, 10)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._rule_type = tk.StringVar(value="miner_offline")
        ttk.Combobox(rb, textvariable=self._rule_type,
                     values=ALERT_TYPES, state="readonly",
                     width=18, font=(FONT_MAIN, 10)
                     ).grid(row=0, column=1, sticky="w")

        tk.Label(rb, text="Threshold:", bg=th["panel"], fg=th["fg2"],
                 font=(FONT_MAIN, 10)).grid(row=0, column=2, padx=(14, 8), sticky="w")
        self._rule_thresh = tk.Entry(rb, width=8, bg=th["panel2"], fg=th["fg"],
                                      font=(FONT_MONO, 10), insertbackground=th["fg"])
        self._rule_thresh.insert(0, "0")
        self._rule_thresh.grid(row=0, column=3, sticky="w")

        self._rule_discord  = tk.BooleanVar(value=False)
        self._rule_telegram = tk.BooleanVar(value=False)
        tk.Checkbutton(rb, text="Discord",  variable=self._rule_discord,
                       bg=th["panel"], fg=th["fg"], selectcolor=th["panel2"],
                       font=(FONT_MAIN, 10)).grid(row=0, column=4, padx=8, sticky="w")
        tk.Checkbutton(rb, text="Telegram", variable=self._rule_telegram,
                       bg=th["panel"], fg=th["fg"], selectcolor=th["panel2"],
                       font=(FONT_MAIN, 10)).grid(row=0, column=5, padx=4, sticky="w")
        tk.Button(rb, text="＋ Add Rule", command=self._add_alert_rule,
                  bg=th["accent"], fg=th["bg"], relief="flat",
                  padx=8, pady=4, font=(FONT_MAIN, 10, "bold"), cursor="hand2"
                  ).grid(row=0, column=6, padx=12)

        # Active rules list
        rules_lf = tk.LabelFrame(parent, text="  Active Rules  ",
                                  bg=th["panel"], fg=th["accent"],
                                  font=(FONT_MAIN, 11, "bold"), padx=6, pady=6)
        rules_lf.pack(fill="x", padx=10, pady=4)
        self._rules_list_frame = tk.Frame(rules_lf, bg=th["panel"])
        self._rules_list_frame.pack(fill="x")
        self._refresh_rules_list()

        # Alert log
        log_lf = tk.LabelFrame(parent, text="  Alert Log (last 100)  ",
                                bg=th["panel"], fg=th["accent"],
                                font=(FONT_MAIN, 11, "bold"), padx=6, pady=6)
        log_lf.pack(fill="both", expand=True, padx=10, pady=(4, 4))

        self._alert_log_text = tk.Text(
            log_lf, bg=th["panel2"], fg=th["fg2"],
            font=(FONT_MONO, 9), state="disabled",
            height=8, relief="flat", wrap="word")
        log_sb = ttk.Scrollbar(log_lf, orient="vertical",
                               command=self._alert_log_text.yview)
        self._alert_log_text.configure(yscrollcommand=log_sb.set)
        self._alert_log_text.pack(side="left", fill="both", expand=True)
        log_sb.pack(side="right", fill="y")

        tk.Button(parent, text="↻  Refresh Log", command=self._refresh_alert_log,
                  bg=th["panel"], fg=th["fg2"], relief="flat",
                  padx=8, pady=4, font=(FONT_MAIN, 9), cursor="hand2"
                  ).pack(pady=(0, 6))
        self._refresh_alert_log()

    # ------------------------------------------------------------------ TAB 4: Skin

    def _build_skin_tab(self, parent):
        th = self.theme

        # Preset buttons
        preset_lf = tk.LabelFrame(parent, text="  Skin Presets  ",
                                  bg=th["panel"], fg=th["accent"],
                                  font=(FONT_MAIN, 11, "bold"), padx=10, pady=10)
        preset_lf.pack(fill="x", padx=10, pady=(10, 6))

        for i, (name, skin) in enumerate(SKIN_PRESETS.items()):
            tk.Button(
                preset_lf, text=name,
                bg=skin["panel"], fg=skin["accent"],
                activebackground=skin["panel2"],
                relief="flat", padx=12, pady=8,
                font=(FONT_MAIN, 10, "bold"), cursor="hand2",
                command=lambda n=name: self._apply_skin_preset(n)
            ).grid(row=0, column=i, padx=4)

        # Visual controls
        vis_lf = tk.LabelFrame(parent, text="  Visual Controls  ",
                               bg=th["panel"], fg=th["accent"],
                               font=(FONT_MAIN, 11, "bold"), padx=10, pady=10)
        vis_lf.pack(fill="x", padx=10, pady=6)

        def lbl(text, r):
            tk.Label(vis_lf, text=text, bg=th["panel"], fg=th["fg2"],
                     font=(FONT_MAIN, 10)).grid(row=r, column=0, sticky="w",
                                                pady=5, padx=(0, 12))

        lbl("HUD Opacity:", 0)
        self.s_opacity = tk.Scale(vis_lf, from_=0.1, to=1.0, resolution=0.01,
                                   orient="horizontal", length=220,
                                   bg=th["panel"], fg=th["fg"], highlightthickness=0,
                                   troughcolor=th["border"],
                                   activebackground=th["accent"],
                                   showvalue=True)
        self.s_opacity.set(self.cfg["opacity"])
        self.s_opacity.grid(row=0, column=1, sticky="w")
        tk.Label(vis_lf, text="0.1 = ghost  ·  1.0 = fully opaque",
                 bg=th["panel"], fg=th["fg2"], font=(FONT_MAIN, 8)
                 ).grid(row=0, column=2, padx=10)

        lbl("Display Mode:", 1)
        self._skin_mode_var = tk.StringVar(value=self.cfg.get("hud_mode", "ring"))
        ttk.Combobox(vis_lf, textvariable=self._skin_mode_var,
                     values=HUD_MODES, state="readonly", width=10,
                     font=(FONT_MAIN, 10)
                     ).grid(row=1, column=1, sticky="w")
        tk.Label(vis_lf, text="or double-click the HUD to cycle",
                 bg=th["panel"], fg=th["fg2"], font=(FONT_MAIN, 8)
                 ).grid(row=1, column=2, padx=10)

        lbl("Snap Corner:", 2)
        self._corner_var = tk.StringVar(value=self.cfg.get("hud_corner", "topright"))
        ttk.Combobox(vis_lf, textvariable=self._corner_var,
                     values=["topright","topleft","bottomright","bottomleft"],
                     state="readonly", width=14, font=(FONT_MAIN, 10)
                     ).grid(row=2, column=1, sticky="w")

        lbl("Accent Color:", 3)
        self._accent_btn = tk.Button(
            vis_lf, text="  Pick  ", command=self._pick_accent,
            bg=th["accent"], fg=th["bg"], relief="flat",
            padx=8, font=(FONT_MAIN, 10, "bold"), cursor="hand2")
        self._accent_btn.grid(row=3, column=1, sticky="w")

        # Metrics toggles
        met_lf = tk.LabelFrame(parent, text="  Metrics Display  ",
                               bg=th["panel"], fg=th["accent"],
                               font=(FONT_MAIN, 11, "bold"), padx=10, pady=10)
        met_lf.pack(fill="x", padx=10, pady=6)

        self._show_hash   = tk.BooleanVar(value=self.cfg.get("show_hash",   True))
        self._show_temp   = tk.BooleanVar(value=self.cfg.get("show_temp",   True))
        self._show_shares = tk.BooleanVar(value=self.cfg.get("show_shares", True))
        self._show_ip     = tk.BooleanVar(value=self.cfg.get("show_ip",     False))

        for i, (text, var) in enumerate([
            ("Hash rate",   self._show_hash),
            ("Temperature", self._show_temp),
            ("Shares",      self._show_shares),
            ("IP address",  self._show_ip),
        ]):
            tk.Checkbutton(met_lf, text=text, variable=var,
                           bg=th["panel"], fg=th["fg"], selectcolor=th["panel2"],
                           activebackground=th["panel"], font=(FONT_MAIN, 10)
                           ).grid(row=0, column=i, padx=12, sticky="w")

        tk.Button(parent, text="✔  Apply Skin & Visual Settings",
                  command=self._apply_skin_settings,
                  bg=th["online"], fg=th["bg"], relief="flat",
                  padx=20, pady=8,
                  font=(FONT_MAIN, 12, "bold"), cursor="hand2"
                  ).pack(pady=14)

    # ------------------------------------------------------------------ TAB 5: Settings

    def _build_settings_tab(self, parent):
        th = self.theme

        frm = tk.Frame(parent, bg=th["bg"], padx=20, pady=14)
        frm.pack(fill="x")

        def row_lbl(text, r):
            tk.Label(frm, text=text, bg=th["bg"], fg=th["fg2"],
                     font=(FONT_MAIN, 10)).grid(row=r, column=0, sticky="w",
                                                pady=6, padx=(0, 14))

        def entry(r, default, width=42):
            e = tk.Entry(frm, width=width, bg=th["panel2"], fg=th["fg"],
                         font=(FONT_MONO, 10), insertbackground=th["fg"],
                         relief="flat")
            e.insert(0, str(default))
            e.grid(row=r, column=1, sticky="w")
            return e

        row_lbl("Discord Webhook URL:", 0)
        self._e_discord = entry(0, self.cfg.get("discord_webhook", ""))
        tk.Button(frm, text="Test", command=self._test_discord,
                  bg=th["panel2"], fg=th["fg"], relief="flat",
                  padx=8, font=(FONT_MAIN, 9), cursor="hand2"
                  ).grid(row=0, column=2, padx=6)

        row_lbl("Telegram Bot Token:", 1)
        self._e_tg_token = entry(1, self.cfg.get("telegram_token", ""))

        row_lbl("Telegram Chat ID:", 2)
        self._e_tg_chat = entry(2, self.cfg.get("telegram_chat_id", ""))
        tk.Button(frm, text="Test", command=self._test_telegram,
                  bg=th["panel2"], fg=th["fg"], relief="flat",
                  padx=8, font=(FONT_MAIN, 9), cursor="hand2"
                  ).grid(row=2, column=2, padx=6)

        row_lbl("Coin Price (USD):", 3)
        self._e_coin = entry(3, self.cfg.get("coin_price_usd", 0.0), width=14)

        row_lbl("Power Cost (USD/kWh):", 4)
        self._e_power = entry(4, self.cfg.get("power_cost_kwh", 0.10), width=14)

        row_lbl("Font Size:", 5)
        self._s_font = tk.Scale(frm, from_=10, to=22, orient="horizontal",
                                 length=160, bg=th["bg"], fg=th["fg"],
                                 highlightthickness=0, troughcolor=th["border"],
                                 activebackground=th["accent"])
        self._s_font.set(self.cfg.get("font_size", 13))
        self._s_font.grid(row=5, column=1, sticky="w")

        self._var_sound = tk.BooleanVar(value=self.cfg.get("sound", True))
        tk.Checkbutton(frm, text="Sound on share events",
                       variable=self._var_sound,
                       bg=th["bg"], fg=th["fg"], selectcolor=th["panel2"],
                       font=(FONT_MAIN, 10)
                       ).grid(row=6, column=0, columnspan=2, sticky="w", pady=6)

        # DB info
        db_size = "N/A"
        try:
            db_size = f"{os.path.getsize(DB_FILE) / 1024:.1f} KB"
        except Exception:
            pass
        tk.Label(frm, text=f"DB: {DB_FILE}  ({db_size})",
                 bg=th["bg"], fg=th["fg2"], font=(FONT_MONO, 9)
                 ).grid(row=7, column=0, columnspan=3, sticky="w", pady=8)

        tk.Button(frm, text="✔  Save Settings", command=self._apply_settings,
                  bg=th["online"], fg=th["bg"], relief="flat",
                  padx=16, pady=7, font=(FONT_MAIN, 11, "bold"), cursor="hand2"
                  ).grid(row=8, column=0, columnspan=2, pady=(10, 0), sticky="w")

    # ------------------------------------------------------------------
    # Tab 1 actions
    # ------------------------------------------------------------------

    def refresh_miner_list(self):
        """Repopulate treeview from current live stats."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        for m in self.get_stats():
            tag = "online" if m["status"] in ("Online", "Demo") else "offline"
            if m.get("temp", 0) >= 70:
                tag = "warn"
            self.tree.insert("", "end", values=(
                m["alias"], m["ip"], m["hash"], m["temp"],
                m["shares"], m["rejected"], m["uptime"], m["status"]
            ), tags=(tag,))
        self.tree.tag_configure("online",  foreground=self.theme["online"])
        self.tree.tag_configure("offline", foreground=self.theme["error"])
        self.tree.tag_configure("warn",    foreground=self.theme["warn"])

    def _scan_subnet(self):
        """Parallel subnet scan with progress bar."""
        subnet = simpledialog.askstring(
            "Scan Subnet", "Enter subnet prefix (e.g. 192.168.1):",
            initialvalue="192.168.1", parent=self)
        if not subnet:
            return

        self._scan_prog_var.set(0)
        self._scan_bar.pack(fill="x", padx=10, pady=2)

        def _progress(n, total):
            self.after(0, lambda: self._scan_prog_var.set(n))

        def _run():
            found_ips = scan_subnet_parallel(subnet, progress_cb=_progress)
            added = 0
            existing = [m["ip"] for m in self.cfg["miners"]]
            for ip in found_ips:
                if ip not in existing:
                    self.cfg["miners"].append({
                        "alias": f"Miner_{ip.split('.')[-1]}", "ip": ip})
                    added += 1
            save_config(self.cfg)
            self.after(0, self._scan_bar.pack_forget)
            self.after(0, self.refresh_miner_list)
            self.after(0, lambda: messagebox.showinfo(
                "Scan Complete",
                f"Scanned {subnet}.1–254\n"
                f"Found: {len(found_ips)} host(s)\n"
                f"Added: {added} new miner(s)",
                parent=self))

        threading.Thread(target=_run, daemon=True).start()

    def _add_miner(self):
        ip = simpledialog.askstring(
            "Add Miner", "Miner IP address:",
            initialvalue="192.168.1.", parent=self)
        if not ip:
            return
        alias = simpledialog.askstring(
            "Add Miner", "Alias:",
            initialvalue=f"Miner_{ip.split('.')[-1]}", parent=self)
        if not alias:
            alias = f"Miner_{ip.split('.')[-1]}"
        if ip in [m["ip"] for m in self.cfg["miners"]]:
            messagebox.showwarning("Duplicate", f"{ip} is already listed.", parent=self)
            return
        self.cfg["miners"].append({"alias": alias, "ip": ip})
        save_config(self.cfg)
        self.refresh_miner_list()

    def _remove_miner(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Remove", "Select a miner row first.", parent=self)
            return
        ip = self.tree.item(sel[0], "values")[1]
        if not messagebox.askyesno("Remove", f"Remove miner at {ip}?", parent=self):
            return
        self.cfg["miners"] = [m for m in self.cfg["miners"] if m["ip"] != ip]
        save_config(self.cfg)
        self.refresh_miner_list()

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export Stats", filetypes=[("CSV", "*.csv")],
            defaultextension=".csv", parent=self)
        if not path:
            return
        try:
            with open(path, "w") as f:
                f.write("Alias,IP,Hash (MH/s),Temp (°C),Shares,Rejected,Uptime,Status\n")
                for m in self.get_stats():
                    f.write(f"{m['alias']},{m['ip']},{m['hash']},{m['temp']},"
                            f"{m['shares']},{m['rejected']},{m['uptime']},{m['status']}\n")
            messagebox.showinfo("Export", f"Saved:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)

    # ------------------------------------------------------------------
    # Tab 2 actions
    # ------------------------------------------------------------------

    def _render_analytics_chart(self):
        if not MPL_OK:
            return
        hours  = self._analytics_hours.get()
        metric = self._analytics_metric.get()
        data   = db_get_all_history(hours=hours)

        if not data:
            messagebox.showinfo(
                "Analytics",
                "No historical data yet.\n"
                "Add miners and let a few poll cycles run.", parent=self)
            return

        th  = self.theme
        fig, ax = plt.subplots(figsize=(7, 3.2), facecolor=th["panel"])
        ax.set_facecolor(th["panel"])

        midx = {"hash_mh": 1, "temp_c": 2, "shares": 3}.get(metric, 1)
        ylbl = {"hash_mh": "MH/s", "temp_c": "°C", "shares": "shares"}.get(metric, "")
        palette = [th["accent"], th["accent2"], th["online"], th["warn"], th["error"]]

        for ci, (ip, rows) in enumerate(data.items()):
            if not rows:
                continue
            step   = max(1, len(rows) // 80)
            times  = list(range(len(rows[::step])))
            values = [r[midx] for r in rows[::step]]
            ax.plot(times, values, label=ip,
                    color=palette[ci % len(palette)],
                    linewidth=1.5, alpha=0.9)

        ax.set_ylabel(ylbl, color=th["fg2"], fontsize=9)
        ax.tick_params(colors=th["fg2"], labelsize=7)
        ax.set_xticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(th["border"])
        if len(data) <= 8:
            ax.legend(fontsize=7, facecolor=th["panel2"],
                      edgecolor=th["border"], labelcolor=th["fg2"])
        ax.set_title(f"{ylbl} — last {hours}h",
                     color=th["accent"], fontsize=10, fontweight="bold")
        fig.tight_layout(pad=0.5)

        if self._chart_widget:
            self._chart_widget.get_tk_widget().destroy()

        cv = mpl_tkagg.FigureCanvasTkAgg(fig, master=self._analytics_frame)
        cv.draw()
        cv.get_tk_widget().pack(fill="both", expand=True)
        self._chart_widget = cv
        plt.close(fig)

    # ------------------------------------------------------------------
    # Tab 3 actions
    # ------------------------------------------------------------------

    def _add_alert_rule(self):
        try:
            thresh = float(self._rule_thresh.get())
        except ValueError:
            thresh = 0.0
        rule = {
            "type":      self._rule_type.get(),
            "threshold": thresh,
            "enabled":   True,
            "discord":   self._rule_discord.get(),
            "telegram":  self._rule_telegram.get(),
        }
        self.cfg.setdefault("alert_rules", []).append(rule)
        save_config(self.cfg)
        self._refresh_rules_list()

    def _refresh_rules_list(self):
        for w in self._rules_list_frame.winfo_children():
            w.destroy()
        th    = self.theme
        rules = self.cfg.get("alert_rules", [])
        if not rules:
            tk.Label(self._rules_list_frame, text="No rules configured.",
                     bg=th["panel"], fg=th["fg2"], font=(FONT_MAIN, 10)
                     ).pack(pady=4)
            return
        for i, r in enumerate(rules):
            row = tk.Frame(self._rules_list_frame, bg=th["panel"])
            row.pack(fill="x", pady=2)
            chs = " · ".join(
                [c for c, f in [("Discord",r.get("discord")),("Telegram",r.get("telegram"))] if f]
            ) or "no delivery"
            label_txt = (f"[{'ON' if r.get('enabled',True) else 'OFF'}]  "
                         f"{r['type']}  thresh={r['threshold']}  → {chs}")
            tk.Label(row, text=label_txt, bg=th["panel"], fg=th["fg"],
                     font=(FONT_MONO, 9)).pack(side="left", padx=4)
            tk.Button(row, text="✕",
                      command=lambda idx=i: self._delete_rule(idx),
                      bg=th["error"], fg="#fff", relief="flat",
                      padx=6, font=(FONT_MAIN, 9), cursor="hand2"
                      ).pack(side="right", padx=4)

    def _delete_rule(self, idx):
        try:
            self.cfg["alert_rules"].pop(idx)
            save_config(self.cfg)
            self._refresh_rules_list()
        except Exception as e:
            dlog(f"_delete_rule: {e}")

    def _refresh_alert_log(self):
        rows = db_get_alert_log(limit=100)
        self._alert_log_text.config(state="normal")
        self._alert_log_text.delete("1.0", "end")
        if not rows:
            self._alert_log_text.insert("end", "No alerts fired yet.")
        else:
            for ts, rtype, ip, msg in rows:
                self._alert_log_text.insert(
                    "end",
                    f"{ts[:19].replace('T',' ')}  [{rtype}]  {ip}\n  {msg}\n\n")
        self._alert_log_text.config(state="disabled")

    # ------------------------------------------------------------------
    # Tab 4 actions
    # ------------------------------------------------------------------

    def _apply_skin_preset(self, name):
        if name not in SKIN_PRESETS:
            return
        self.cfg["theme"]    = dict(SKIN_PRESETS[name])
        self.cfg["hud_skin"] = name
        self.theme           = self.cfg["theme"]
        save_config(self.cfg)
        self.apply_config(self.cfg)

    def _pick_accent(self):
        color = colorchooser.askcolor(
            title="Pick Accent Color",
            color=self.theme["accent"], parent=self)[1]
        if color:
            self.cfg["theme"]["accent"] = color
            self.theme["accent"]        = color
            self._accent_btn.configure(bg=color)

    def _apply_skin_settings(self):
        self.cfg["opacity"]    = self.s_opacity.get()
        self.cfg["hud_mode"]   = self._skin_mode_var.get()
        self.cfg["hud_corner"] = self._corner_var.get()
        self.cfg["hud_x"]      = None
        self.cfg["hud_y"]      = None
        self.cfg["show_hash"]   = self._show_hash.get()
        self.cfg["show_temp"]   = self._show_temp.get()
        self.cfg["show_shares"] = self._show_shares.get()
        self.cfg["show_ip"]     = self._show_ip.get()
        save_config(self.cfg)
        self.apply_config(self.cfg)
        messagebox.showinfo("Skin", "Visual settings applied.", parent=self)

    # ------------------------------------------------------------------
    # Tab 5 actions
    # ------------------------------------------------------------------

    def _apply_settings(self):
        self.cfg["discord_webhook"]  = self._e_discord.get().strip()
        self.cfg["telegram_token"]   = self._e_tg_token.get().strip()
        self.cfg["telegram_chat_id"] = self._e_tg_chat.get().strip()
        self.cfg["font_size"]        = self._s_font.get()
        self.cfg["sound"]            = self._var_sound.get()
        try:
            self.cfg["coin_price_usd"] = float(self._e_coin.get())
        except ValueError:
            pass
        try:
            self.cfg["power_cost_kwh"] = float(self._e_power.get())
        except ValueError:
            pass
        save_config(self.cfg)
        self.apply_config(self.cfg)
        messagebox.showinfo("Settings", "Settings saved.", parent=self)

    def _test_discord(self):
        self.cfg["discord_webhook"] = self._e_discord.get().strip()
        if not self.cfg["discord_webhook"]:
            messagebox.showwarning("Discord", "Enter a webhook URL first.", parent=self)
            return
        threading.Thread(
            target=lambda: self.alert_engine.test_discord(self.cfg),
            daemon=True).start()
        messagebox.showinfo("Discord", "Test message sent — check your channel.", parent=self)

    def _test_telegram(self):
        self.cfg["telegram_token"]   = self._e_tg_token.get().strip()
        self.cfg["telegram_chat_id"] = self._e_tg_chat.get().strip()
        if not self.cfg["telegram_token"] or not self.cfg["telegram_chat_id"]:
            messagebox.showwarning("Telegram",
                                   "Enter both bot token and chat ID first.", parent=self)
            return
        threading.Thread(
            target=lambda: self.alert_engine.test_telegram(self.cfg),
            daemon=True).start()
        messagebox.showinfo("Telegram", "Test message sent — check your Telegram.", parent=self)


# =============================================================================
# SYSTEM TRAY (optional)
# =============================================================================

def _try_start_tray(app):
    """Start pystray icon if available. Silently skips if missing."""
    try:
        import pystray
        from PIL import Image as PilImg
    except ImportError:
        dlog("pystray/Pillow not installed — tray icon skipped.")
        return
    try:
        img = (PilImg.open(LOGO_FILE).resize((64, 64)).convert("RGBA")
               if LOGO_FILE and os.path.exists(LOGO_FILE)
               else PilImg.new("RGBA", (64, 64), (180, 80, 220, 255)))
    except Exception:
        img = PilImg.new("RGBA", (64, 64), (180, 80, 220, 255))

    def _show(icon, item):
        app.after(0, app.cmd.deiconify)

    def _quit(icon, item):
        icon.stop()
        app.after(0, app.quit_app)

    icon = pystray.Icon(
        "PlumHUD", img, f"Plum HUD {VERSION}",
        pystray.Menu(
            pystray.MenuItem("Open Panel", _show),
            pystray.MenuItem("Quit", _quit),
        )
    )
    threading.Thread(target=icon.run, daemon=True).start()
    dlog("Tray icon started.")


# =============================================================================
# ROOT APPLICATION
# =============================================================================

class PlumHUDApp(tk.Tk):
    """
    Hidden root Tk. All visible UI lives in Toplevel windows.
    Owns: config, live stats list, stats_queue, PollEngine, AlertEngine.

    BOOT ORDER:
      1. load_config + db_init
      2. AlertEngine
      3. _sync_poll (blocks briefly for initial data)
      4. HUDWindow + CommandCenter
      5. PollEngine (bg thread)
      6. _queue_drain_loop (after(500) main-thread consumer)
      7. _try_start_tray (optional)
    """

    def __init__(self):
        super().__init__()
        self.withdraw()                     # Root window stays hidden

        self.cfg         = load_config()
        self.stats       = []
        self.stats_queue = queue.Queue()

        db_init()

        # Alert engine must boot before poll engine
        self.alert_engine = AlertEngine(
            get_cfg_cb   = lambda: self.cfg,
            ui_notify_cb = self._ui_alert_toast,
        )

        # Fast initial sync poll so HUD has data immediately
        self._sync_poll()

        # Windows
        self.hud = HUDWindow(self, self.cfg, lambda: self.stats)
        self.cmd = CommandCenter(
            self, self.cfg,
            self._apply_config,
            lambda: self.stats,
            self.alert_engine,
            lambda: self.cfg.get("miners", []),
        )
        self.cmd.deiconify()

        # Async engine
        self._poll_engine = PollEngine(
            get_miners_cb = lambda: self.cfg.get("miners", []),
            stats_queue   = self.stats_queue,
            alert_engine  = self.alert_engine,
        )
        self._poll_engine.start()

        # Main-thread queue drain
        self._queue_drain_loop()

        # Tray icon (optional)
        _try_start_tray(self)

        self.protocol("WM_DELETE_WINDOW", self.quit_app)

    # ------------------------------------------------------------------

    def _sync_poll(self):
        """
        One-shot synchronous poll of all configured miners.
        WRITES: self.stats
        """
        new_stats = []
        for m in self.cfg.get("miners", []):
            try:
                new_stats.append(poll_miner(m["ip"]))
            except Exception as e:
                dlog(f"_sync_poll {m['ip']}: {e}")
        self.stats = new_stats
        dlog(f"Sync poll: {len(self.stats)} miners.")

    def _queue_drain_loop(self):
        """
        Drain stats_queue on the main thread.
        Keeps only the latest batch — stale intermediates are discarded.
        Scheduled every 500ms via after().
        WRITES: self.stats
        """
        try:
            latest = None
            while not self.stats_queue.empty():
                latest = self.stats_queue.get_nowait()
            if latest is not None:
                self.stats = latest
                try:
                    self.cmd.refresh_miner_list()
                except Exception:
                    pass
        except Exception as e:
            dlog(f"_queue_drain_loop: {e}")
        self.after(500, self._queue_drain_loop)

    def _apply_config(self, cfg):
        """
        Broadcast config update to all windows.
        WRITES: self.cfg, hud.cfg, hud.theme, hud opacity
        """
        self.cfg = cfg
        try:
            self.hud.apply_config(cfg)
        except Exception as e:
            dlog(f"_apply_config HUD: {e}")

    def _ui_alert_toast(self, message):
        """
        Show alert dialog on main thread.
        DECISION: messagebox used for now.
        NEXT STEPS: replace with plyer.notification for non-blocking toasts.
        """
        self.after(0, lambda: messagebox.showwarning("Plum HUD Alert", message))

    def quit_app(self):
        """Clean shutdown: save config, stop engines, close DB, destroy."""
        save_config(self.cfg)
        try:
            self._poll_engine.stop()
        except Exception:
            pass
        try:
            self.hud.stop()
        except Exception:
            pass
        try:
            if _db_conn:
                _db_conn.close()
        except Exception:
            pass
        self.destroy()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = PlumHUDApp()
    app.mainloop()
