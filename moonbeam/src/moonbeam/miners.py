"""
============================================================
moonbeam.miners — discovery and polling
F-Keys | www.f-keys.com
------------------------------------------------------------
The shared core. The CLI renders it in a terminal and PlumHUD
renders it in a window; neither should own the polling.

WORKFLOW STACK
  1. local_subnet()  — work out which /24 this machine is on
  2. scan()          — probe every host concurrently
  3. poll()          — read one miner's vitals

API CONTRACT
  ESP-Miner / AxeOS devices answer on
      http://<ip>/api/system/info
  with initMiner, hashRate, temp, sharesAccepted,
  sharesRejected, uptimeSeconds.

DESIGN RULE — MISSING IS MISSING
  A field the miner did not send is reported as None and
  printed as a dash. It is never filled in with a plausible
  number. A fabricated hashrate that looks real is worse than
  an obvious gap, because you cannot tell you are being lied
  to. Standard library only, so `pip install` cannot fail on a
  dependency.
============================================================
"""

import concurrent.futures
import ipaddress
import json
import os
import socket
import urllib.error
import urllib.request

__all__ = ["local_subnet", "poll", "scan", "load_saved", "save_miners", "CONFIG_PATH"]

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".moonbeam")
CONFIG_PATH = os.path.join(CONFIG_DIR, "miners.json")

API_PATH = "/api/system/info"
DEFAULT_TIMEOUT = 1.5
DEFAULT_WORKERS = 64


def local_subnet():
    """
    The /24 this machine sits on, e.g. '192.168.1.0/24'.

    Opens a UDP socket to a public address to discover which interface
    the OS would route through. No packet is actually sent.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return str(ipaddress.ip_network(ip + "/24", strict=False))


def poll(ip, timeout=DEFAULT_TIMEOUT):
    """
    Read one miner. Returns a dict, or None if nothing answered.

    Every vital is Optional. If the device omits a field it stays None
    and the caller shows a dash.
    """
    url = "http://{}{}".format(ip, API_PATH)
    req = urllib.request.Request(url, headers={"User-Agent": "moonbeam"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            data = json.loads(r.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, socket.timeout, ValueError, OSError):
        return None
    if not isinstance(data, dict):
        return None

    return {
        "ip": ip,
        "alias": data.get("initMiner") or data.get("hostname") or ip,
        "hashrate": data.get("hashRate"),
        "temp": data.get("temp"),
        "accepted": data.get("sharesAccepted"),
        "rejected": data.get("sharesRejected"),
        "uptime_s": data.get("uptimeSeconds"),
        "power": data.get("power"),
        "voltage": data.get("voltage"),
        "frequency": data.get("frequency"),
        "best_diff": data.get("bestDiff"),
        "pool": data.get("stratumURL"),
        "version": data.get("version"),
        "raw": data,
    }


def scan(subnet=None, timeout=DEFAULT_TIMEOUT, workers=DEFAULT_WORKERS, progress=None):
    """
    Probe every host on a /24 and return the miners that answered.

    progress: optional callable(done, total) for a live counter.
    """
    subnet = subnet or local_subnet()
    hosts = [str(h) for h in ipaddress.ip_network(subnet, strict=False).hosts()]
    found, done = [], 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(poll, h, timeout): h for h in hosts}
        for fut in concurrent.futures.as_completed(futures):
            done += 1
            if progress:
                progress(done, len(hosts))
            try:
                got = fut.result()
            except Exception:
                got = None
            if got:
                found.append(got)

    found.sort(key=lambda m: tuple(int(p) for p in m["ip"].split(".")))
    return found


def poll_many(ips, timeout=DEFAULT_TIMEOUT, workers=DEFAULT_WORKERS):
    """Poll a known list of addresses. Unreachable ones come back offline."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, max(len(ips), 1))) as pool:
        for ip, got in zip(ips, pool.map(lambda i: poll(i, timeout), ips)):
            results.append(got or {"ip": ip, "alias": ip, "offline": True})
    return results


def load_saved():
    """Addresses remembered from a previous scan."""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return [str(x) for x in data.get("miners", [])]
    except (OSError, ValueError):
        return []


def save_miners(ips):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"miners": sorted(set(ips))}, f, indent=2)
    return CONFIG_PATH
