#!/usr/bin/env python3
"""
============================================================
test_site - the claims this site makes about itself
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The Privacy page says there is no advertising, no analytics
and no cookie on f-keys.com. That was true the day it was
written, and an ad tag pasted into one hand-maintained page
is all it takes to turn it into a lie nobody notices. The
same goes for the rest: the homepage heading, the share
image, the structured data, the recovery links on the 404.

So none of it is promised. Each claim is asserted here
against the files that are actually served, and this fails
the build when a claim stops being true.

WORKFLOW STACK
  1. PAGES        - collect every .html the site serves
  2. no_trackers  - the Privacy page, as a property
  3. metadata     - head tags an agent resolves identity from
  4. homepage     - an h1 and real prose without running anything
  5. structured   - JSON-LD parses, says who to contact, and does
                    NOT carry the registered street address
  6. anchors      - about / contact / privacy are real pages
  7. contact      - the role address, never the personal one
  8. recovery     - the 404 points somewhere useful
  9. openapi     - every documented path is a file, and the spec
                    claims no auth, no server and no write that
                    F-Keys does not actually have
 10. llms.txt     - when-to-use guidance is present
 11. sitemap      - every URL it lists is a file that exists
 12. generated    - EVERY page buildsite writes still matches it,
                    not just the ones at the root

Run:  python tools/test_site.py
============================================================
"""

import io
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories that are not the website: vendored code, build output and
# the git database would all produce false positives.
# cv/ was in here, and it should not have been. The Privacy page's
# promises are made on behalf of the whole domain, and the CV pages are
# the ones a client is most likely to open. Skipping them meant the
# tracker rules were never asserted against the most client-facing thing
# on the site - which is how four of them kept fetching a typeface from
# Google long after every other page stopped.
# Only things that are NOT SERVED belong in here. cv/ was in this set
# and four of its pages were fetching a typeface from Google; dist/ and
# desktop/ were in it too, and /dp/dist/ and /keyj/desktop/src/ both
# answer 200 on the live domain. The Privacy page makes its promises on
# behalf of the whole site, so the only safe rule is that anything a
# visitor can reach gets checked. node_modules stays: it 404s.
SKIP_DIRS = {".git", ".github", "node_modules",
             "__pycache__", ".private-snapshot", ".agents", ".claude"}

# The pages this site generates, which are the ones these rules govern.
GENERATED = ["index.html", "apps.html", "games.html", "tools.html",
             "hardware.html", "research.html", "properties.html",
             "about.html", "contact.html", "privacy.html", "developers.html",
             "404.html"]

MIN_TEXT = 500

failures = []


def fail(check, message):
    failures.append((check, message))


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def html_files():
    out = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if n.endswith(".html"):
                out.append(os.path.join(base, n))
    return sorted(out)


def read(path):
    with io.open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def visible_text(source):
    """What is left once the markup and the scripts are gone."""
    s = re.sub(r"<script.*?</script>", " ", source, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", s)).strip()


# ── 2. the Privacy page, as a property ───────────────────────
# Each pattern is something the Privacy page says is not here. The
# message is the sentence that stops being true if the pattern matches.
BANNED = [
    (r"adsbygoogle|googlesyndication|ca-pub-",
     "Privacy says there is no advertising"),
    (r"google-analytics\.com|googletagmanager\.com|gtag\s*\(",
     "Privacy says there is no analytics"),
    (r"connect\.facebook\.net|fbq\s*\(|/tr\?id=",
     "Privacy says there is no tracking pixel"),
    (r"plausible\.io|umami\.|matomo\.|segment\.com|hotjar",
     "Privacy says there is no analytics"),
    # Cloudflare's beacon is the one that gets waved through as harmless.
    # It is cookieless, but it is still a script, and the Privacy page
    # says there is no analytics script of any kind. Traffic numbers for
    # a proxied zone are in the Cloudflare dashboard without it.
    (r"cloudflareinsights\.com|beacon\.min\.js",
     "Privacy says there is no analytics script of any kind"),
    # A font request reports the reader's IP on every page view, which is
    # the oldest way to watch someone read. Both faces are OFL 1.1 and are
    # served from /assets/fonts.css.
    (r"fonts\.googleapis\.com|fonts\.gstatic\.com",
     "Privacy says no page loads anything from another company's server"),
    (r"document\.cookie\s*=",
     "Privacy says this site sets no cookies"),
]


def no_trackers(pages):
    for path in pages:
        # A commented-out tag does not load, and a comment explaining why
        # a host was dropped must not read as that host coming back.
        source = re.sub(r"<!--.*?-->", " ", read(path), flags=re.S)
        for pattern, claim in BANNED:
            m = re.search(pattern, source, flags=re.I)
            if m:
                fail("no-trackers", "{}: {!r} - {}".format(
                    rel(path), m.group(0), claim))


# ── 3. the head tags identity is resolved from ───────────────
def metadata(pages):
    for name in GENERATED:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            fail("metadata", "missing generated page: " + name)
            continue
        s = read(path)
        for pattern, label in [
            (r'<html lang="[a-z-]+"', "html lang"),
            (r'<meta property="og:image" content="https://', "og:image"),
            (r'<meta property="og:type"', "og:type"),
            (r'<link rel="icon"', "favicon"),
            (r'<title>.+</title>', "title"),
            (r'<h1[^>]*>', "h1"),
        ]:
            if not re.search(pattern, s):
                fail("metadata", "{} has no {}".format(name, label))
        # the 404 is the one page that must NOT be indexed, and the only
        # one that must not claim a canonical URL of its own
        if name == "404.html":
            if "noindex" not in s:
                fail("metadata", "404.html is not noindex")
        elif not re.search(r'<link rel="canonical" href="https://', s):
            fail("metadata", name + " has no canonical")


def homepage_without_javascript():
    """The homepage is what an agent reads before it runs anything."""
    s = read(os.path.join(ROOT, "index.html"))
    text = visible_text(s)
    if len(text) < MIN_TEXT:
        fail("homepage", "index.html has {} chars of text, needs {}".format(
            len(text), MIN_TEXT))
    if not re.search(r"<h1[^>]*>\s*F-Keys\s*</h1>", s):
        fail("homepage", "index.html has no F-Keys h1")


# ── 4. structured data ───────────────────────────────────────
def structured():
    blocks = 0
    for name in GENERATED:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            continue
        for raw in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                read(path), flags=re.S):
            blocks += 1
            try:
                obj = json.loads(raw)
            except ValueError as e:
                fail("json-ld", "{}: does not parse: {}".format(name, e))
                continue
            if obj.get("@type") != "Organization":
                continue
            if not obj.get("contactPoint"):
                fail("json-ld", name + ": Organization has no contactPoint")
            addr = obj.get("address") or {}
            # No streetAddress on purpose: the registered address is a
            # home. Locality, region and country are enough for the schema
            # to resolve where the company answers from.
            for field in ("addressLocality", "addressRegion",
                          "postalCode", "addressCountry"):
                if not addr.get(field):
                    fail("json-ld",
                         "{}: address is missing {}".format(name, field))
            if addr.get("streetAddress"):
                fail("json-ld", name + ": address carries a street line, "
                                       "which is a home address")
    if blocks == 0:
        fail("json-ld", "no JSON-LD on any generated page")

    # The product pages are the other half of the answer. The scope is
    # what buildsite generates: log/ and status/ are hand-written and are
    # not products, so requiring a SoftwareApplication of them would be
    # asserting something nobody promised.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import buildsite
    for slug in buildsite.PAGES:
        page = os.path.join(ROOT, slug, "index.html")
        if not os.path.exists(page):
            fail("json-ld", "{}/ was not generated".format(slug))
            continue
        s = read(page)
        if '"@type": "SoftwareApplication"' not in s:
            fail("json-ld", "{}/ has no SoftwareApplication".format(slug))


# ── 5. the pages an agent checks before believing in a business ──
def anchors():
    for name in ("about.html", "contact.html", "privacy.html"):
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            fail("trust-anchors", "missing: " + name)
            continue
        n = len(visible_text(read(path)))
        if n < MIN_TEXT:
            fail("trust-anchors",
                 "{} has {} chars, needs {}".format(name, n, MIN_TEXT))

    contact = read(os.path.join(ROOT, "contact.html"))
    for needle in ("hello@f-keys.com", "Punta Gorda", "L26000436157"):
        if needle not in contact:
            fail("trust-anchors", "contact.html does not name " + needle)

    # The street line was removed on purpose and must not come back by way
    # of a copied block or a regenerated schema.
    for name in GENERATED:
        path = os.path.join(ROOT, name)
        if os.path.exists(path) and "Matecumbe" in read(path):
            fail("trust-anchors",
                 name + " publishes the registered street address")


# ── 6. a missing page still tells you where to go ────────────
def recovery():
    path = os.path.join(ROOT, "404.html")
    if not os.path.exists(path):
        fail("404", "no 404.html - GitHub Pages will serve its own")
        return
    s = read(path)
    for target in ("/sitemap.xml", "/llms.txt", "/apps.html", "/contact.html"):
        if target not in s:
            fail("404", "404.html does not point at " + target)


def contact_is_reachable():
    """The published address is a role address on the site's own domain,
    which only works while that domain accepts mail. A contact page that
    bounces is worse than no contact page, and it fails silently."""
    for name in GENERATED:
        path = os.path.join(ROOT, name)
        if os.path.exists(path) and "@me.com" in read(path):
            fail("contact", name + " publishes a personal address rather "
                                   "than the role address")
    if "hello@f-keys.com" not in read(os.path.join(ROOT, "llms.txt")):
        fail("contact", "llms.txt does not carry the contact address")


def openapi():
    """A specification is a promise an agent cannot check before it acts
    on it. Every path in this one must be a file that exists, and it must
    not claim an authentication scheme, a server or a write operation
    that F-Keys does not have."""
    path = os.path.join(ROOT, "openapi.json")
    if not os.path.exists(path):
        fail("openapi", "no openapi.json")
        return
    try:
        spec = json.loads(read(path))
    except ValueError as e:
        fail("openapi", "does not parse: {}".format(e))
        return

    if not spec.get("paths"):
        fail("openapi", "documents no paths")

    for url, ops in (spec.get("paths") or {}).items():
        local = os.path.join(ROOT, url.lstrip("/").replace("/", os.sep))
        if not os.path.isfile(local):
            fail("openapi", "documents a path with no file behind it: " + url)
        for method in ops:
            if method.lower() != "get":
                fail("openapi", "{} declares {}, but nothing here accepts a "
                                "write".format(url, method.upper()))

    # Function calling turns an operation into a signature, and an
    # untyped `object` gives it nothing to fill in. Every response must
    # resolve to a schema that actually names its properties, and every
    # operationId must be unique or two tools collide under one name.
    schemas = spec.get("components", {}).get("schemas", {})
    seen = {}
    for url, ops in (spec.get("paths") or {}).items():
        op = ops.get("get") or {}
        oid = op.get("operationId")
        if not oid:
            fail("openapi", url + " has no operationId")
        elif oid in seen:
            fail("openapi", "operationId {!r} is used by both {} and {}"
                            .format(oid, seen[oid], url))
        else:
            seen[oid] = url
        if not op.get("description") and not op.get("summary"):
            fail("openapi", url + " has neither a summary nor a description")

        try:
            schema = op["responses"]["200"]["content"]["application/json"][
                "schema"]
        except (KeyError, TypeError):
            fail("openapi", url + " has no JSON response schema")
            continue
        # Inline, not a $ref. The tools that turn an operation into a
        # function signature do not dereference, so a $ref reads to them
        # as an argument with no type at all - which is how this scored
        # zero typed schemas while every schema was in fact present.
        if "$ref" in schema:
            fail("openapi", url + " answers with a $ref; function-calling "
                                  "converters do not resolve those")
        elif not schema.get("properties"):
            fail("openapi", url + " has a response schema that names no "
                                  "properties")

    # A $ref anywhere in the document defeats the point of inlining, and
    # one arrived by accident: the Kernel Trust meta-schema contains the
    # word as data, so type-inferring it produced a property literally
    # named $ref whose value was an object - the one shape a resolver
    # walking this file must never meet.
    stack = [spec]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "$ref" in node:
                fail("openapi", "contains a $ref: " + repr(node["$ref"])[:60])
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)

    # what an integrator is entitled to rely on, stated rather than implied
    for key in ("x-versioning", "x-rate-limit"):
        if not spec.get(key):
            fail("openapi", "does not declare " + key)

    # the version prefix is a promise; it has to be declared where a tool
    # reading only the servers block will see it
    if not any(str(s.get("url", "")).rstrip("/").endswith("/v1")
               for s in spec.get("servers") or []):
        fail("openapi", "no versioned server; x-versioning claims url-path "
                        "but nothing in servers carries a prefix")

    if spec.get("components", {}).get("securitySchemes") or spec.get("security"):
        fail("openapi", "declares authentication, but there is nothing to "
                        "authenticate against")

    for server in spec.get("servers") or []:
        if not str(server.get("url", "")).startswith("https://f-keys.com"):
            fail("openapi", "names a server that is not this site: " +
                 str(server.get("url")))

    # The spec must not depend on what the weather was when the snapshot
    # ran. It did: Cloudflare's bot categories became schema properties,
    # so a day that saw "Security" and a day that saw "Accessibility"
    # produced different specs, and the build went red on the next push
    # for a reason nobody had caused. Rendering it against every day on
    # record has to give one answer.
    import glob
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import buildapi
    live = os.path.join(ROOT, "status", "latest.json")
    days = sorted(glob.glob(os.path.join(ROOT, "status", "data", "*.json")))
    if days and os.path.exists(live):
        kept = read(live)
        shapes = {}
        try:
            for day in days:
                with io.open(live, "w", encoding="utf-8", newline="\n") as f:
                    f.write(read(day))
                shapes.setdefault(buildapi.render(), []).append(
                    os.path.basename(day))
        finally:
            with io.open(live, "w", encoding="utf-8", newline="\n") as f:
                f.write(kept)
        if len(shapes) > 1:
            fail("openapi", "the specification changes with the day's data: "
                 + " vs ".join(", ".join(v) for v in shapes.values()))

    # The developer page is the human-readable half. An audit called it
    # thin, which it was: it named the packages but never said what
    # authentication is required, what the rate limit is, or what happens
    # when a path is withdrawn - the three things anyone decides to
    # integrate on.
    dev = os.path.join(ROOT, "developers.html")
    if not os.path.exists(dev):
        fail("openapi", "no developers.html")
        return
    page = read(dev)
    if "/openapi.json" not in page:
        fail("openapi", "developers.html does not link the specification")

    text = visible_text(page)
    if len(text) < 3000:
        fail("openapi", "developers.html is {} chars; a page that does not "
                        "answer auth, limits and versioning is thin"
                        .format(len(text)))
    for heading, why in [
        ("Authentication", "what credentials are needed"),
        ("Rate limits", "whether to throttle"),
        ("Versioning and deprecation", "what happens when a path is withdrawn"),
        ("The command line", "how to drive it without an integration"),
    ]:
        if heading not in page:
            fail("openapi", "developers.html does not answer {} ({})"
                            .format(why, heading))
    if "curl " not in page:
        fail("openapi", "developers.html shows no example request")


def published_zones():
    """The status page prints per-property traffic, and the data behind it
    comes from Cloudflare, which returns EVERY zone on the account - not a
    list of F-Keys properties. Three domains that are nobody's business
    were published on a public page because the renderer printed whatever
    the API handed it.

    A public page must publish from a list of what may be published. This
    asserts that: every site named in the status data and on the status
    page is one the snapshot's own allowlist permits."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import snapshot

    allowed = snapshot.PUBLISHABLE_SITES
    files = [os.path.join(ROOT, "status", "latest.json")]
    data_dir = os.path.join(ROOT, "status", "data")
    if os.path.isdir(data_dir):
        files += [os.path.join(data_dir, n) for n in sorted(os.listdir(data_dir))
                  if n.endswith(".json")]

    seen = set()
    for path in files:
        if not os.path.exists(path):
            continue
        try:
            doc = json.loads(read(path))
        except ValueError:
            fail("zones", rel(path) + " does not parse")
            continue
        for site in ((doc.get("cloudflare") or {}).get("sites") or []):
            name = site.get("site")
            if not name:
                continue
            seen.add(name)
            if name not in allowed:
                fail("zones", "{} publishes {!r}, which is not a property "
                              "this site publishes".format(rel(path), name))

    # and the rendered page, in case it is ever written from something
    # other than those files
    page = os.path.join(ROOT, "status", "index.html")
    if os.path.exists(page):
        source = read(page)
        # the first cell of every traffic row is the site name
        for body in re.findall(r'data-body="traffic">(.*?)</tbody>',
                               source, flags=re.S):
            for cell in re.findall(r'<td class="">([^<]+)</td>', body):
                if cell.strip() and cell.strip() not in allowed:
                    fail("zones", "status/index.html shows {!r} in the "
                                  "traffic table".format(cell.strip()))


def counts_in_prose():
    """A number written out in a sentence still has to be the number.

    The homepage said "Twenty-two products are live" while the catalogue
    held twenty-six, and every gate passed for weeks because none of
    them had any opinion about prose.

    Then this gate stopped working, silently, and passed anyway. The
    sentence was rewritten to "products are on the shelves" and wrapped
    across a line, so the pattern matched nothing at all and a check
    over zero claims reported success. A gate that cannot find the thing
    it checks has NOT verified it, so finding nothing is now a failure -
    the same rule contrast-gate learned as --require-pairs.

    Whitespace is collapsed first, because where a sentence happens to
    wrap in the source is not a fact about the site.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import buildsite

    products = buildsite.count_word(len(buildsite.CATALOGUE))
    live = buildsite.count_word(buildsite.live_count()).lower()
    shelves = buildsite.count_word(len(buildsite.CATEGORIES)).lower()

    for path in html_files():
        source = read(path)
        for token in ("%%PRODUCTS%%", "%%SHELVES%%", "%%LIVE%%"):
            if token in source:
                fail("counts", "{} still carries an unfilled {}"
                     .format(rel(path), token))

    # (file, regex, expected, what it is) - every one MUST be found.
    claims = [
        ("index.html", r"([A-Z][a-z]+(?:-[a-z]+)?) products are on the shelves",
         products, "the catalogue size"),
        ("index.html", r"([a-z]+(?:-[a-z]+)?) of them live today",
         live, "the live count"),
        ("about.html", r"([A-Z][a-z]+(?:-[a-z]+)?) products are on the shelves",
         products, "the catalogue size"),
        ("about.html", r"([a-z]+(?:-[a-z]+)?) of them live today",
         live, "the live count"),
        ("index.html", r"([a-z]+(?:-[a-z]+)?) of them, sorted",
         shelves, "the number of shelves"),
    ]
    for name, pattern, want, what in claims:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            fail("counts", "missing " + name)
            continue
        flat = re.sub(r"\s+", " ", visible_text(read(path)))
        found = re.findall(pattern, flat)
        if not found:
            fail("counts", "{}: no sentence states {} any more - this gate "
                           "was checking nothing".format(name, what))
            continue
        for said in found:
            if said != want:
                fail("counts", "{} says {!r} for {}, it is {!r}"
                     .format(name, said, what, want))


def security_txt():
    """security.txt has to be present, reachable, and NOT expired.

    RFC 9116 makes Expires mandatory and caps it at a year, which means
    every security.txt is a claim with a fuse on it. An expired one is
    worse than none: a researcher reads it, sees a dead date, and
    assumes nobody is home. Nothing about the file changes on the day
    it lapses, so nothing would tell us.

    The 30-day warning is the point. Failing on the day it expires
    would fail the build on a day nobody chose.
    """
    import datetime
    path = os.path.join(ROOT, ".well-known", "security.txt")
    if not os.path.isfile(path):
        fail("security", ".well-known/security.txt is missing")
        return
    s = read(path)
    for field in ("Contact:", "Expires:"):
        if not re.search(r"^" + field, s, re.M):
            fail("security", "security.txt has no " + field.rstrip(":"))
    if "hello@f-keys.com" not in s:
        fail("security", "security.txt does not publish the role address")
    m = re.search(r"^Expires:\s*(\S+)", s, re.M)
    if not m:
        return
    try:
        when = datetime.datetime.strptime(m.group(1),
                                          "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        fail("security", "Expires is not an RFC 3339 timestamp: " + m.group(1))
        return
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    left = (when - now).days
    if left < 0:
        fail("security", "security.txt EXPIRED {} days ago ({})".format(
            -left, m.group(1)))
    elif left < 30:
        fail("security", "security.txt expires in {} days ({}) - "
                         "push the date out".format(left, m.group(1)))


# Build output this repository serves but did not author. dp/dist is a
# Vite build whose real home is dp.f-keys.com, where /assets/... is
# correct; it is only wrong at the /dp/dist/ path f-keys.com also
# happens to serve. Its internal paths are that build's business and
# cannot be fixed from here.
#
# The distinction is deliberate and narrow: the LINK rule does not apply
# to these, because they were built for a different mount point. Every
# other rule does - above all the tracker rules, which the Privacy page
# makes on behalf of anything a visitor can reach.
VENDORED = ("/dist/", "/node_modules/")


def authored(path):
    rel_path = "/" + rel(path)
    return not any(v in rel_path for v in VENDORED)


def internal_links():
    """Every root-relative link this site AUTHORS has to resolve to a file.

    Added after a product page shipped with a link to /cvd-palette-action,
    a path invented while writing prose and never created. A visitor gets a
    404 from a page that looks finished, and nothing else here would have
    noticed: the sitemap check only reads the sitemap, and the markdown and
    schema checks only read what they generate.
    """
    for path in html_files():
        if not authored(path):
            continue
        source = read(path)
        for href in re.findall(r'href="(/[^"#?]*)"', source):
            target = href.lstrip("/")
            if not target:
                continue
            if not exists_exactly(target):
                fail("links", "{} links to {}, which is not a file"
                     .format(rel(path), href))


def exists_exactly(target):
    """Does this path exist with EXACTLY this spelling?

    os.path.isfile would answer yes to /docs.html when the file is
    Docs.html, because this repository is developed on Windows and
    Windows does not care about case. GitHub Pages serves it from
    Linux, which does. A gate that runs on the forgiving filesystem
    and passes a link the strict one would 404 is worse than no gate,
    so every segment is matched against the real directory listing.
    """
    here = ROOT
    parts = [p for p in target.split("/") if p]
    for i, part in enumerate(parts):
        try:
            listing = os.listdir(here)
        except OSError:
            return False
        if part not in listing:
            return False
        here = os.path.join(here, part)
        last = i == len(parts) - 1
        if os.path.isfile(here):
            return last
    # a directory: it serves if it has an index, and a bare directory
    # link is how /status/ and /papers/ are written
    return os.path.isdir(here)


def agent_instructions():
    path = os.path.join(ROOT, "llms.txt")
    s = read(path)
    if "## When to use F-Keys" not in s:
        fail("llms.txt", "no when-to-use section")
    if "## Developer resources" not in s:
        fail("llms.txt", "no developer resources section")
    for url in ("https://f-keys.com/Docs.html",
                "https://f-keys.com/contact.html",
                "https://f-keys.com/developers.html",
                "https://f-keys.com/openapi.json"):
        if url not in s:
            fail("llms.txt", "does not list " + url)


# ── 7. the output still matches the generator ────────────────
def generated_is_current():
    """buildsite.py is the source of truth; a hand-edit to a generated
    page is silently reverted by the next build, so it is caught here
    instead of in production."""
    # Every page buildsite writes, not just the ones at the root. A change
    # to the shell - a new node in the navigation tree, say - rewrites all
    # of them, and checking only the root once let twelve product pages
    # ship with a different navigation while this reported ok.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import buildmd
    names = buildmd.targets()

    before = {n: read(os.path.join(ROOT, n))
              for n in names if os.path.exists(os.path.join(ROOT, n))}
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools",
                                                     "buildsite.py")],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        fail("generated", "buildsite.py failed: " + r.stderr.strip()[:300])
        return
    for name, old in before.items():
        if read(os.path.join(ROOT, name)) != old:
            fail("generated",
                 "{} differs from what buildsite.py produces - it was "
                 "edited by hand, or the build was not re-run"
                 .format(name.replace("\\", "/")))


# ── 8. the map matches the territory ─────────────────────────
def sitemap():
    path = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(path):
        fail("sitemap", "no sitemap.xml")
        return
    urls = re.findall(r"<loc>https://f-keys\.com/([^<]*)</loc>", read(path))
    for u in urls:
        u = u.split("#")[0].split("?")[0]
        local = os.path.join(ROOT, u.replace("/", os.sep))
        if u == "" or os.path.isfile(local):
            continue
        if os.path.isdir(local) and os.path.isfile(
                os.path.join(local, "index.html")):
            continue
        fail("sitemap", "lists a path with no file behind it: /" + u)


def main():
    pages = html_files()
    print("test_site: {} html files".format(len(pages)))

    no_trackers(pages)
    metadata(pages)
    homepage_without_javascript()
    structured()
    anchors()
    contact_is_reachable()
    internal_links()
    security_txt()
    counts_in_prose()
    published_zones()
    openapi()
    recovery()
    agent_instructions()
    sitemap()
    generated_is_current()

    if not failures:
        print("test_site: ok")
        return 0

    by_check = {}
    for check, message in failures:
        by_check.setdefault(check, []).append(message)
    for check in sorted(by_check):
        print("\n{}:".format(check))
        for m in by_check[check]:
            print("  -", m)
    print("\ntest_site: {} FAILED".format(len(failures)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
