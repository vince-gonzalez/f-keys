#!/usr/bin/env python3
"""
============================================================
snapshot v1.0.0
Daily/weekly KPI snapshot across every F-Keys property.
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The numbers arrive in six places nobody checks: npm, PyPI,
Zenodo, GitHub traffic, and whether the sites are even up.
This pulls them into one file per day, commits it so git
becomes the time series, and renders a page you can just open.

WORKFLOW STACK
  1. Collect from each source independently
  2. A failing source records its error and does NOT fail the run
  3. Write status/data/YYYY-MM-DD.json  (history, one per day)
  4. Write status/latest.json           (most recent)
  5. Render status/index.html           (the page you look at)
  6. Weekly mode diffs against the file from 7 days ago

DESIGN RULE
  Never let one dead endpoint lose the whole snapshot. Partial
  data with a visible error beats no data and a red build.

CREDENTIALS
  Works with none. Optional, read from env if present:
    GH_TOKEN          GitHub repo traffic (views/clones)
    CF_API_TOKEN      Cloudflare analytics   [not wired yet]
    CF_ACCOUNT_ID     Cloudflare account     [not wired yet]
  Sources needing a token simply report "skipped: no token".

Run:  python tools/snapshot.py            (daily)
      python tools/snapshot.py --weekly   (adds 7-day deltas)
============================================================
"""

import json
import os
import re
import sys
import time
import datetime
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_DIR  = os.path.join(ROOT, "status")
DATA_DIR    = os.path.join(STATUS_DIR, "data")

# This repo is public, so status/ is public. GitHub repo traffic is
# owner-only data, so the full snapshot goes to a PRIVATE repo and the
# published copy has those fields removed. Everything else in the
# snapshot (npm, PyPI, Zenodo, stars, uptime) was already public data.
PRIVATE_OUT   = os.environ.get("PRIVATE_OUT", os.path.join(ROOT, ".private-snapshot"))
PRIVATE_FIELDS = ("views_14d", "unique_views_14d", "traffic_error",
                  "clones_14d", "unique_cloners_14d")
UA         = "fkeys-snapshot/1.0 (+https://f-keys.com)"

# ── WHAT WE TRACK ────────────────────────────────────────────
PROPERTIES = [
    ("f-keys.com",        "https://f-keys.com"),
    ("opticquiz.com",     "https://opticquiz.com"),
    ("poticas.com",       "https://poticas.com"),
    ("5best2buy.com",     "https://www.5best2buy.com"),
    ("trailer-load.com",  "https://trailer-load.com"),
    ("tipstreams.com",    "https://tipstreams.com"),
    ("dogefundme.com",    "https://dogefundme.com"),
    ("modulign.org",      "https://modulign.org"),
    ("prompt.f-keys.com", "https://prompt.f-keys.com"),
    ("dp.f-keys.com",     "https://dp.f-keys.com"),
    ("zengin.es",         "https://zengin.es"),
]

NPM_PACKAGES  = ["@f-keys/tip-widget", "opticquiz-eye", "opticquiz-cvd", "opticquiz-cvd-mcp"]
PYPI_PACKAGES = ["gonzalgo", "opticquiz-cvd", "moonbeam-miner", "plumhud",
                 "keyj"]
# Three of these were shipped and then never added here, so the status page
# reported two of five packages and read as complete.

GITHUB_OWNER = "zengineco"
GITHUB_REPOS = [
    "f-keys", "gonzalgo", "opticquiz.com", "tip-widget", "poticas",
    "5best2buy.com", "trailer-load.com", "tipstreams.com", "prompt-game",
    "daisupop", "qv", "fytecraft.com", "modulign.org", "Moonbeam-NerdMiner",
]

PAPERS_URL = "https://f-keys.com/papers/"


# ── HTTP ─────────────────────────────────────────────────────
def fetch(url, headers=None, tries=3, timeout=25):
    """GET with retries. Returns (body_text, error_string)."""
    hdrs = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    last = ""
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace"), None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (400, 401, 403, 404):
                break               # not transient, stop retrying
        except Exception as e:
            last = type(e).__name__
        time.sleep(1.5 * (attempt + 1))
    return None, last


def fetch_json(url, headers=None, tries=3):
    body, err = fetch(url, headers=headers, tries=tries)
    if err:
        return None, err
    try:
        return json.loads(body), None
    except ValueError:
        return None, "bad JSON"


# ── COLLECTORS ───────────────────────────────────────────────
def collect_uptime():
    out = []
    for name, url in PROPERTIES:
        t0 = time.time()
        body, err = fetch(url, headers={"Accept": "text/html"}, tries=2, timeout=20)
        ms = int((time.time() - t0) * 1000)
        out.append({"name": name, "url": url, "up": err is None,
                    "ms": ms, "error": err})
    return out


def collect_npm():
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    out = []
    for pkg in NPM_PACKAGES:
        d, err = fetch_json(f"https://api.npmjs.org/downloads/point/last-week/{pkg}")
        entry = {"package": pkg,
                 "weekly": (d or {}).get("downloads") if not err else None,
                 "error": err}
        # npm has no all-time endpoint; a wide point range is the way to get it.
        a, aerr = fetch_json(
            f"https://api.npmjs.org/downloads/point/2015-01-01:{today}/{pkg}", tries=2)
        entry["all_time"] = (a or {}).get("downloads") if not aerr else None
        out.append(entry)
    return out


def collect_pypi():
    out = []
    for pkg in PYPI_PACKAGES:
        d, err = fetch_json(f"https://pypistats.org/api/packages/{pkg}/recent")
        data = (d or {}).get("data", {}) if not err else {}
        entry = {"package": pkg,
                 "daily":   data.get("last_day"),
                 "weekly":  data.get("last_week"),
                 "monthly": data.get("last_month"),
                 "error": err}
        # /overall returns both categories. with_mirrors is roughly 3x the
        # real figure because mirror bots re-download constantly, so only
        # without_mirrors is reported here.
        o, oerr = fetch_json(f"https://pypistats.org/api/packages/{pkg}/overall", tries=2)
        if not oerr:
            entry["all_time"] = sum(r["downloads"] for r in (o.get("data") or [])
                                    if r.get("category") == "without_mirrors")
        else:
            entry["all_time"] = None
        out.append(entry)
    return out


def collect_github():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    auth  = {"Authorization": f"Bearer {token}"} if token else None
    out = []
    for repo in GITHUB_REPOS:
        entry = {"repo": repo}
        d, err = fetch_json(f"https://api.github.com/repos/{GITHUB_OWNER}/{repo}", headers=auth)
        if err:
            entry["error"] = err
            out.append(entry)
            continue
        entry.update({"stars": d.get("stargazers_count"),
                      "forks": d.get("forks_count"),
                      "open_issues": d.get("open_issues_count"),
                      "pushed_at": d.get("pushed_at"),
                      "archived": d.get("archived")})
        if token:
            # Traffic needs push access; absent that it 403s, which is fine.
            t, terr = fetch_json(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{repo}/traffic/views",
                headers=auth, tries=1)
            if terr:
                entry["traffic_error"] = terr
            else:
                entry["views_14d"] = t.get("count")
                entry["unique_views_14d"] = t.get("uniques")
            # Clones are the stronger signal for a package: people install it
            # rather than read about it. gonzalgo ran 828 clones against 35
            # page views the first time this was measured.
            c, cerr = fetch_json(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{repo}/traffic/clones",
                headers=auth, tries=1)
            if not cerr:
                entry["clones_14d"] = c.get("count")
                entry["unique_cloners_14d"] = c.get("uniques")
        else:
            entry["traffic_error"] = "skipped: no token"
        out.append(entry)
    return out


def collect_zenodo():
    """Harvest DOIs from the live papers page, then pull stats per record."""
    page, err = fetch(PAPERS_URL, headers={"Accept": "text/html"})
    if err:
        return {"error": f"papers page: {err}", "records": []}
    dois = sorted(set(re.findall(r"10\.5281/zenodo\.(\d+)", page)))
    records = []
    for rid in dois:
        d, derr = fetch_json(f"https://zenodo.org/api/records/{rid}", tries=2)
        if derr:
            records.append({"id": rid, "error": derr})
            continue
        s = d.get("stats") or {}
        records.append({
            "id": rid,
            "title": (d.get("metadata", {}) or {}).get("title") or d.get("title") or "",
            "views": s.get("views"),
            "unique_views": s.get("unique_views"),
            "downloads": s.get("downloads"),
            "unique_downloads": s.get("unique_downloads"),
        })
    return {"error": None, "records": records}


def cf_graphql(token, query, variables, tries=3):
    """
    POST to Cloudflare's GraphQL analytics endpoint, with retries.

    The first live run lost tipstreams.com to a single transient 502 while
    every other zone succeeded. One blip should not silently drop a site
    from the numbers, so 5xx and timeouts are retried; 4xx is not, because
    a bad token or a malformed query will not fix itself.
    """
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    last = ""
    for attempt in range(tries):
        req = urllib.request.Request(
            "https://api.cloudflare.com/client/v4/graphql",
            data=body,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json",
                     "User-Agent": UA},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode("utf-8", "replace"))
            if d.get("errors"):
                return None, str(d["errors"][0].get("message"))[:90]
            return d.get("data"), None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if 400 <= e.code < 500:
                return None, last
        except Exception as e:
            last = type(e).__name__
        time.sleep(2.0 * (attempt + 1))
    return None, last


ZONE_TRAFFIC_QUERY = """
query ($zoneTag: String!, $since: Date!, $until: Date!) {
  viewer {
    zones(filter: {zoneTag: $zoneTag}) {
      httpRequests1dGroups(
        limit: 40,
        filter: {date_geq: $since, date_leq: $until},
        orderBy: [date_DESC]
      ) {
        dimensions { date }
        sum {
          requests
          pageViews
          threats
          countryMap { clientCountryName requests }
        }
        uniq { uniques }
      }
    }
  }
}
"""


BOT_QUERY = """
query ($zoneTag: String!, $since: Time!, $until: Time!) {
  viewer {
    zones(filter: {zoneTag: $zoneTag}) {
      httpRequestsAdaptiveGroups(
        limit: 100,
        filter: {datetime_geq: $since, datetime_leq: $until}
      ) {
        count
        dimensions { verifiedBotCategory }
      }
    }
  }
}
"""


def collect_cloudflare(days=7):
    """
    Per-site page views and unique visitors from Cloudflare.

    Free-plan constraints, learned the hard way and worth not relearning:
      - GraphQL rejects multi-zone filters ("too many zones"), so this
        queries ONE zone per request rather than batching.
      - httpRequests1dGroups is the daily dataset that works on Free.
        httpRequestsAdaptiveGroups (user agent, path, referer) is capped
        at 24h windows, so it is no use for a 7-day view.
      - There is no referrer data on Free, so click-through is invisible.
      - These counts include automated traffic. Uniques is closer to
        people than page views, but neither is a clean human number.
    """
    token = os.environ.get("CF_API_TOKEN")
    if not token:
        return {"error": "skipped: no CF_API_TOKEN", "sites": [],
                "totals": {"page_views": None, "uniques": None}, "days": days}

    # Enumerate zones so a new property appears here without a code change.
    zones, page = [], 1
    while True:
        d, err = fetch_json(
            f"https://api.cloudflare.com/client/v4/zones?per_page=50&page={page}",
            headers={"Authorization": f"Bearer {token}"}, tries=2)
        if err:
            return {"error": f"zone list: {err}", "sites": [],
                    "totals": {"page_views": None, "uniques": None}, "days": days}
        zones.extend([(z["id"], z["name"]) for z in d.get("result", [])])
        info = d.get("result_info") or {}
        if page >= (info.get("total_pages") or 1):
            break
        page += 1

    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = (today - datetime.timedelta(days=days)).isoformat()
    until = (today - datetime.timedelta(days=1)).isoformat()

    sites = []
    for zid, name in zones:
        data, err = cf_graphql(token, ZONE_TRAFFIC_QUERY,
                               {"zoneTag": zid, "since": since, "until": until})
        if err:
            sites.append({"site": name, "error": err})
            continue
        try:
            groups = data["viewer"]["zones"][0]["httpRequests1dGroups"]
        except (KeyError, IndexError, TypeError):
            sites.append({"site": name, "error": "no data returned"})
            continue
        countries = {}
        for g in groups:
            for c in (g["sum"].get("countryMap") or []):
                countries[c["clientCountryName"]] = (
                    countries.get(c["clientCountryName"], 0) + (c["requests"] or 0))
        top = sorted(countries.items(), key=lambda kv: -kv[1])[:5]
        total_c = sum(countries.values()) or 1

        sites.append({
            "site": name,
            "page_views": sum((g["sum"]["pageViews"] or 0) for g in groups),
            "uniques":    sum((g["uniq"]["uniques"] or 0) for g in groups),
            "requests":   sum((g["sum"]["requests"] or 0) for g in groups),
            "threats":    sum((g["sum"].get("threats") or 0) for g in groups),
            "days_returned": len(groups),
            "top_countries": [
                {"country": k, "requests": v, "pct": round(100.0 * v / total_c, 1)}
                for k, v in top],
        })

    # Verified-bot breakdown. The adaptive dataset is capped at 24h windows on
    # the Free plan, so this is a one-day sample. Run daily it accumulates into
    # the time series that a 7-day query cannot give us.
    now  = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    bsince = (now - datetime.timedelta(hours=23)).isoformat().replace("+00:00", "Z")
    buntil = now.isoformat().replace("+00:00", "Z")
    bots, bot_err = {}, None
    for zid, name in zones:
        data, err = cf_graphql(token, BOT_QUERY,
                               {"zoneTag": zid, "since": bsince, "until": buntil})
        if err:
            bot_err = bot_err or err
            continue
        try:
            rows = data["viewer"]["zones"][0]["httpRequestsAdaptiveGroups"]
        except (KeyError, IndexError, TypeError):
            continue
        for r in rows:
            cat = (r["dimensions"].get("verifiedBotCategory") or "").strip()
            bots[cat or "Unverified"] = bots.get(cat or "Unverified", 0) + (r["count"] or 0)

    ok = [s for s in sites if "error" not in s]
    sites.sort(key=lambda s: -(s.get("uniques") or 0))
    return {
        "error": None if ok else "no zone returned data",
        "days": days,
        "window": {"since": since, "until": until},
        "sites": sites,
        "totals": {
            "page_views": sum(s["page_views"] for s in ok) if ok else None,
            "uniques":    sum(s["uniques"] for s in ok) if ok else None,
            "threats":    sum(s.get("threats") or 0 for s in ok) if ok else None,
        },
        # "Unverified" is NOT the same as human - it is everything Cloudflare
        # could not positively identify as a known bot, which includes both
        # real people and the credential scanners that spoof AI user agents.
        "bots_24h": dict(sorted(bots.items(), key=lambda kv: -kv[1])),
        "bots_error": bot_err,
    }


# ── TOTALS ───────────────────────────────────────────────────
def summarise(snap):
    npm_total  = sum(x["weekly"] or 0 for x in snap["npm"])
    pypi_total = sum(x["weekly"] or 0 for x in snap["pypi"])
    recs       = snap["zenodo"]["records"]
    cf = snap.get("cloudflare", {}) or {}
    cft = cf.get("totals", {}) or {}
    return {
        "visitors_7d":       cft.get("uniques"),
        "page_views_7d":     cft.get("page_views"),
        "properties_up":     sum(1 for p in snap["uptime"] if p["up"]),
        "properties_total":  len(snap["uptime"]),
        "npm_weekly":        npm_total,
        "pypi_weekly":       pypi_total,
        "package_weekly":    npm_total + pypi_total,
        "zenodo_records":    len(recs),
        "zenodo_views":      sum(r.get("views") or 0 for r in recs),
        "zenodo_downloads":  sum(r.get("downloads") or 0 for r in recs),
        "github_stars":      sum(r.get("stars") or 0 for r in snap["github"]),
    }


# ── REDACTION ────────────────────────────────────────────────
def redact(snap):
    """Copy of the snapshot with owner-only fields removed, for publishing."""
    pub = json.loads(json.dumps(snap))
    for repo in pub.get("github", []):
        for f in PRIVATE_FIELDS:
            repo.pop(f, None)
    pub["redacted"] = ("GitHub repo traffic is owner-only and lives in the "
                       "private KPI repo, not here.")
    return pub


# ── RENDER ───────────────────────────────────────────────────
def fmt(n):
    """Thousands separators, and an em dash when a source gave us nothing."""
    return "—" if n is None else f"{n:,}"


def row(label, value, delta=None):
    d = ""
    if delta is not None and delta != 0:
        sign = "+" if delta > 0 else ""
        cls = "up" if delta > 0 else "down"
        d = f' <span class="{cls}">{sign}{delta}</span>'
    return f"<tr><td>{label}</td><td class='num'>{value}{d}</td></tr>"


def render(snap, prev):
    s = snap["summary"]
    p = (prev or {}).get("summary", {})

    def dl(key):
        if not p or p.get(key) is None or s.get(key) is None:
            return None
        return s[key] - p[key]

    cf = snap.get("cloudflare", {}) or {}
    cf_sites = cf.get("sites", []) or []
    if cf.get("error"):
        traffic_html = (f"<p class='dim'>{cf['error']}</p>"
                        "<p class='dim' style='margin-top:.6rem;font-size:.82rem'>"
                        "Add CF_API_TOKEN and this fills with per-site visitors.</p>")
    else:
        traffic_html = "<table>" + "".join(
            (f"<tr><td>{x['site']}"
             + (f"<br><span class='dim' style='font-size:.8rem'>"
                f"{x['top_countries'][0]['country']} {x['top_countries'][0]['pct']}%</span>"
                if x.get("top_countries") else "")
             + f"</td><td class='num'>"
             f"{fmt(x.get('uniques'))} <span class='dim'>/ {fmt(x.get('page_views'))} pv</span>"
             "</td></tr>") if "error" not in x else
            (f"<tr><td>{x['site']}</td><td class='num dim'>{x['error']}</td></tr>")
            for x in cf_sites) + "</table>"

    # Uptime is a one-line strip now, not a headline. It matters when it breaks
    # and not otherwise.
    down = [x["name"] for x in snap["uptime"] if not x["up"]]
    slow = sorted((x for x in snap["uptime"] if x["up"]), key=lambda x: -x["ms"])[:1]
    if down:
        uptime_strip = ("<span class='down'>DOWN: " + ", ".join(down) + "</span>")
    else:
        s0 = slow[0] if slow else None
        uptime_strip = (f"<span class='ok'>All {len(snap['uptime'])} properties responding</span>"
                        + (f" <span class='dim'>· slowest {s0['name']} {s0['ms']}ms</span>" if s0 else ""))

    up_rows = "".join(
        f"<tr><td>{x['name']}</td><td class='num'>"
        f"{'<span class=ok>UP</span>' if x['up'] else '<span class=down>DOWN</span>'}"
        f" <span class='dim'>{x['ms']}ms</span></td></tr>"
        for x in snap["uptime"])

    pkg_rows = "".join(
        f"<tr><td>{x['package']}</td><td class='num'>{fmt(x.get('weekly'))}"
        f" <span class='dim'>/ {fmt(x.get('all_time'))} all time</span></td></tr>"
        for x in snap["npm"] + snap["pypi"])

    top_papers = sorted([r for r in snap["zenodo"]["records"] if r.get("views")],
                        key=lambda r: -(r.get("views") or 0))[:8]
    paper_rows = "".join(
        f"<tr><td title=\"{r['title']}\">{r['title'][:58]}</td>"
        f"<td class='num'>{r['views']} <span class='dim'>/ {r.get('downloads') or 0} dl</span></td></tr>"
        for r in top_papers) or "<tr><td colspan=2 class='dim'>no data</td></tr>"

    has_traffic = any(r.get("views_14d") is not None for r in snap["github"])
    repo_rows = "".join(
        f"<tr><td>{r['repo']}</td><td class='num'>"
        + (f"{r.get('views_14d') if r.get('views_14d') is not None else '—'} " if has_traffic else "")
        + f"<span class='dim'>{r.get('stars') or 0}★</span></td></tr>"
        for r in sorted(snap["github"],
                        key=lambda r: (-(r.get("views_14d") or 0), -(r.get("stars") or 0))))
    repo_title = "REPOS — 14d views / stars" if has_traffic else "REPOS — stars"

    bots = (cf.get("bots_24h") or {})
    if bots:
        btotal = sum(bots.values()) or 1
        # Re-sort here: the snapshot is written with sort_keys=True for stable
        # diffs, which alphabetises these and buries the large buckets.
        ranked = sorted(bots.items(), key=lambda kv: -kv[1])
        mix_rows = "".join(
            f"<tr><td>{k}</td><td class='num'>{fmt(v)}"
            f" <span class='dim'>{round(100.0*v/btotal,1)}%</span></td></tr>"
            for k, v in ranked[:9])
        mix_html = ("<table>" + mix_rows + "</table>"
                    "<p class='dim' style='margin-top:.9rem;font-size:.8rem'>"
                    "24-hour sample — the only window the free plan allows for this "
                    "dataset. <strong>Unverified</strong> is not the same as human: it "
                    "is everything Cloudflare could not positively identify, which "
                    "includes real people and the scanners that spoof AI user agents."
                    "</p>")
    else:
        mix_html = ("<p class='dim'>" + (cf.get("bots_error") or "no sample yet") + "</p>")

    errs = []
    for x in snap["npm"] + snap["pypi"]:
        if x.get("error"):
            errs.append(f"{x['package']}: {x['error']}")
    for x in snap["github"]:
        if x.get("error") or x.get("traffic_error"):
            errs.append(f"{x['repo']}: {x.get('error') or x.get('traffic_error')}")
    if snap["zenodo"].get("error"):
        errs.append(f"zenodo: {snap['zenodo']['error']}")
    if snap["cloudflare"].get("error"):
        errs.append(f"cloudflare: {snap['cloudflare']['error']}")
    err_html = ("<ul class='errs'>" + "".join(f"<li>{e}</li>" for e in errs) + "</ul>") \
        if errs else "<p class='dim'>All sources reported.</p>"

    import buildsite as B

    cards = (
        '<div class="doc"><h1>Status</h1>'
        '<p class="sub">Generated {gen}. {strip}</p>'
        '<table class="facts">'
        '<tr><th>Visitors &middot; 7d</th><td>{v}</td></tr>'
        '<tr><th>Page views &middot; 7d</th><td>{pv}</td></tr>'
        '<tr><th>Package installs / wk</th><td>{pk}</td></tr>'
        '<tr><th>Paper views</th><td>{pvw}</td></tr>'
        '<tr><th>Paper downloads</th><td>{pd}</td></tr>'
        '</table>'
        '<h2>Traffic &mdash; visitors / page views, 7d</h2>{traffic}'
        '<h2>Packages &mdash; week / all time</h2><table class="facts">{pkg}</table>'
        '<h2>Who is asking &mdash; 24h sample</h2>{mix}'
        '<h2>Papers &mdash; views / downloads</h2><table class="facts">{papers}</table>'
        '<h2>Sources not reporting</h2>{errs}'
        '</div>'
    ).format(gen=snap["generated_at"], strip=re.sub(r"<[^>]+>", "", uptime_strip),
             v=fmt(s.get("visitors_7d")), pv=fmt(s.get("page_views_7d")),
             pk=s["package_weekly"], pvw=s["zenodo_views"], pd=s["zenodo_downloads"],
             traffic=traffic_html,
             pkg="".join("<tr><th>{}</th><td>{} / {} all time</td></tr>".format(
                 x["package"], fmt(x.get("weekly")), fmt(x.get("all_time")))
                 for x in snap["npm"] + snap["pypi"]),
             mix=mix_html,
             papers="".join("<tr><th>{}</th><td>{} views / {} downloads</td></tr>".format(
                 (r["title"] or "")[:58], fmt(r.get("views")), fmt(r.get("downloads")))
                 for r in top_papers) or "<tr><td>no data</td></tr>",
             errs=err_html)

    return B.shell("Status \u2014 F-Keys", "F-Keys\\Status", cards, "live numbers",
                   description="Measured traffic, installs and paper activity "
                               "across every F-Keys property.",
                   canonical="https://f-keys.com/status/")


# ── MAIN ─────────────────────────────────────────────────────
def load_prev(today, days_back):
    target = today - datetime.timedelta(days=days_back)
    for delta in range(0, 4):          # tolerate a missed run
        d = target - datetime.timedelta(days=delta)
        p = os.path.join(DATA_DIR, f"{d.isoformat()}.json")
        if os.path.exists(p):
            try:
                return json.load(open(p, encoding="utf-8"))
            except ValueError:
                return None
    return None


def main():
    weekly = "--weekly" in sys.argv
    os.makedirs(DATA_DIR, exist_ok=True)

    today = datetime.datetime.now(datetime.timezone.utc).date()
    snap = {
        "date": today.isoformat(),
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
                                .strftime("%Y-%m-%d %H:%M UTC"),
        "mode": "weekly" if weekly else "daily",
    }

    print("collecting uptime...");     snap["uptime"]     = collect_uptime()
    print("collecting npm...");        snap["npm"]        = collect_npm()
    print("collecting pypi...");       snap["pypi"]       = collect_pypi()
    print("collecting github...");     snap["github"]     = collect_github()
    print("collecting zenodo...");     snap["zenodo"]     = collect_zenodo()
    print("collecting cloudflare..."); snap["cloudflare"] = collect_cloudflare()
    snap["summary"] = summarise(snap)

    prev = load_prev(today, 7 if weekly else 1)

    # PRIVATE: the complete snapshot, including owner-only repo traffic.
    priv_data = os.path.join(PRIVATE_OUT, "data")
    os.makedirs(priv_data, exist_ok=True)
    for path in (os.path.join(priv_data, f"{today.isoformat()}.json"),
                 os.path.join(PRIVATE_OUT, "latest.json")):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2, sort_keys=True)

    # PUBLIC: same snapshot with the owner-only fields stripped.
    pub = redact(snap)
    with open(os.path.join(DATA_DIR, f"{today.isoformat()}.json"), "w", encoding="utf-8") as f:
        json.dump(pub, f, indent=2, sort_keys=True)
    with open(os.path.join(STATUS_DIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(pub, f, indent=2, sort_keys=True)
    with open(os.path.join(STATUS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render(pub, prev))

    s = snap["summary"]
    print()
    print(f"  sites up          {s['properties_up']}/{s['properties_total']}")
    print(f"  package installs  {s['package_weekly']}/wk  (npm {s['npm_weekly']}, pypi {s['pypi_weekly']})")
    print(f"  papers            {s['zenodo_records']} records, "
          f"{s['zenodo_views']} views, {s['zenodo_downloads']} downloads")
    print(f"  github stars      {s['github_stars']}")
    down = [p["name"] for p in snap["uptime"] if not p["up"]]
    if down:
        print(f"  DOWN: {', '.join(down)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
