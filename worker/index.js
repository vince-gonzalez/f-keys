/*
============================================================
f-keys-markdown - Accept negotiation in front of GitHub Pages
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
An agent that sends `Accept: text/markdown` got text/html and
a Vary header that did not mention Accept. GitHub Pages
cannot do either thing: it serves a file, it does not
negotiate, and it will not set a header per request.

Cloudflare is already in front of the origin, so the
negotiation happens here. tools/buildmd.py writes a .md
beside every generated .html; this picks between them and,
either way, tells caches that Accept is what it picked on.
That last part is the whole point - without Vary: Accept a
cache will hand the HTML variant to the next agent that asks
for markdown, or the markdown to the next browser.

WORKFLOW STACK
  1. wantsMarkdown()  - parse Accept, including q-values
  2. markdownPath()   - the .md beside a given URL
  3. fetch()          - try the variant, fall back to HTML
  4. withVary()       - Accept on every negotiated response

Deploy:  cd worker && npx wrangler deploy
============================================================
*/

/* Extensions that are already their own format. Negotiating on top of
   these would mean handing an agent a markdown file where it asked for
   a stylesheet. */
var PASSTHROUGH = /\.(css|js|mjs|json|xml|txt|png|jpg|jpeg|gif|svg|webp|ico|woff2?|ttf|pdf|zip|exe|dmg|wav|mp3|mp4|webm|map)$/i;

var MD_TYPE = "text/markdown; charset=utf-8";
var VARY = "Accept, Accept-Encoding";

/* Accept: text/markdown, text/html;q=0.9 means markdown. Accept:
   text/html, text/markdown;q=0.1 does not, and treating a q=0 entry as
   a request is the usual way this gets written wrong. */
function quality(accept) {
  var best = { markdown: 0, json: 0, html: 0 };
  if (!accept) { return best; }

  var parts = accept.split(",");

  for (var i = 0; i < parts.length; i++) {
    var bits = parts[i].trim().split(";");
    var type = bits[0].trim().toLowerCase();
    var q = 1;

    for (var j = 1; j < bits.length; j++) {
      var p = bits[j].trim();
      if (p.indexOf("q=") === 0) {
        var parsed = parseFloat(p.slice(2));
        q = isNaN(parsed) ? 1 : parsed;
      }
    }

    if (type === "text/markdown" || type === "text/x-markdown") {
      best.markdown = Math.max(best.markdown, q);
    } else if (type === "application/json" || type === "application/ld+json") {
      best.json = Math.max(best.json, q);
    } else if (type === "text/html" || type === "application/xhtml+xml") {
      best.html = Math.max(best.html, q);
    }
  }

  return best;
}

function wantsMarkdown(accept) {
  var q = quality(accept);
  return q.markdown > 0 && q.markdown >= q.html && q.markdown >= q.json;
}

/* An agent that asked for JSON and got an HTML error page has to parse
   the page to find out it failed, which it cannot reliably do. */
function wantsJson(accept) {
  var q = quality(accept);
  return q.json > 0 && q.json >= q.html && q.json >= q.markdown;
}

/* Paths whose answer is data whatever the request says it will take. A
   client fetching a .json URL is not asking for a web page, and most of
   them - curl, requests, fetch - send `Accept: * /*` rather than naming
   a type, so waiting to be asked in so many words means answering a
   machine with markup. */
var DATA_PATH = /(\.json$)|(^\/api(\/|$))|(^\/v\d+(\/|$))/i;

/* Explicitly preferring HTML is still honoured: a browser that lands on
   a broken .json link should see the page, not a blob. */
function prefersHtml(accept) {
  var q = quality(accept);
  return q.html > 0 && q.html >= q.json && q.html >= q.markdown;
}

function shouldErrorAsJson(pathname, accept) {
  if (wantsJson(accept)) { return true; }
  return DATA_PATH.test(pathname) && !prefersHtml(accept);
}

/* The shape openapi.json documents under components.schemas.Error. The
   hints are the three places a lost agent can actually recover from. */
function jsonError(pathname, status, code, message) {
  var body = {
    error: {
      code: code,
      message: message,
      status: status,
      path: pathname,
      hints: [
        "Every published path is listed in https://f-keys.com/openapi.json",
        "The full site map is at https://f-keys.com/sitemap.xml",
        "A plain-text catalogue is at https://f-keys.com/llms.txt",
        "Developer resources: https://f-keys.com/developers.html"
      ]
    }
  };
  var headers = new Headers();
  headers.set("Content-Type", "application/json; charset=utf-8");
  headers.set("Vary", VARY);
  headers.set("Cache-Control", "no-store");
  return new Response(JSON.stringify(body, null, 2) + "\n",
                      { status: status, statusText: "Not Found", headers: headers });
}

/* The .md that buildmd.py wrote beside this page, or null when the path
   is not one of the generated pages. */
function markdownPath(pathname) {
  if (PASSTHROUGH.test(pathname)) { return null; }
  if (pathname.slice(-3) === ".md") { return null; }

  if (pathname === "" || pathname === "/") { return "/index.md"; }
  if (pathname.slice(-5) === ".html") { return pathname.slice(0, -5) + ".md"; }
  if (pathname.slice(-1) === "/") { return pathname + "index.md"; }
  return pathname + "/index.md";
}

/* Every response this Worker touches is a negotiated one, including the
   HTML it decided not to replace. A cache that stored the HTML without
   this would serve it to the next agent asking for markdown. */
function withVary(response, contentType) {
  var headers = new Headers(response.headers);
  headers.set("Vary", VARY);
  if (contentType) { headers.set("Content-Type", contentType); }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: headers
  });
}

/* A version prefix that resolves to the same bytes as the bare path.

   There is no server here to route a /v1/, so the usual objection is
   that the prefix would be decoration. It is not, because the promise
   behind it is one a folder of static files can actually keep: what is
   served under /v1 keeps the shape it has today. If a document ever has
   to change shape, /v2 appears beside it and /v1 is served with the
   Deprecation and Sunset headers of RFC 8594 and RFC 9745 for the 180
   days the policy commits to.

   Callers who would rather track the data than a path can keep using
   the bare URL and pin on the sha256 each document carries. Both are
   supported; the prefix exists so that an integrator who wants the
   guarantee has somewhere to point at. */
var VERSION_PREFIX = /^\/v(\d+)(\/|$)/;
var CURRENT_VERSION = "1";

function stripVersion(pathname) {
  var m = pathname.match(VERSION_PREFIX);
  if (!m) { return null; }
  var rest = pathname.slice(m[0].length - (m[2] === "/" ? 1 : 0));
  return { version: m[1], pathname: rest === "" ? "/" : rest };
}

/* The maintenance view of the status page.

   Nothing behind this is secret - the snapshot it renders is a file in a
   public repository, and raw.githubusercontent.com will serve that file
   to anyone who asks. The gate exists because the page is the workshop
   rather than the shop front, not because the contents are sensitive.
   Anything that genuinely must not be published is excluded from the
   snapshot at the source by snapshot.PUBLISHABLE_SITES.

   The password is a Worker secret, never a literal in this file, because
   this file is public:

       cd worker && npx wrangler secret put STATUS_PASSWORD

   With no secret set this denies everything rather than falling back to
   a default. A gate whose password is printed beside it is not a gate. */
var GATED = /^\/status\/detail(\/|$)/i;

function unauthorised(reason) {
  var headers = new Headers();
  headers.set("WWW-Authenticate",
              'Basic realm="F-Keys status", charset="UTF-8"');
  headers.set("Content-Type", "text/plain; charset=utf-8");
  headers.set("Cache-Control", "no-store");
  return new Response(reason + "\n\nThe public status page is at " +
                      "https://f-keys.com/status/\n",
                      { status: 401, headers: headers });
}

function authorised(request, env) {
  var expected = env && env.STATUS_PASSWORD;
  if (!expected) { return "no password is configured for this Worker"; }

  var header = request.headers.get("Authorization") || "";
  if (header.slice(0, 6).toLowerCase() !== "basic ") {
    return "this page needs a password";
  }

  var decoded;
  try { decoded = atob(header.slice(6).trim()); } catch (e) { decoded = ""; }
  var password = decoded.slice(decoded.indexOf(":") + 1);

  /* Compared over the whole length rather than short-circuiting on the
     first wrong character. */
  if (password.length !== expected.length) { return "that password is wrong"; }
  var diff = 0, i;
  for (i = 0; i < expected.length; i++) {
    diff |= password.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return diff === 0 ? null : "that password is wrong";
}

/* The version prefix is peeled off here and nowhere else, so everything
   below only ever sees a real path. */
async function handle(request, env) {
  var gate = new URL(request.url);
  if (GATED.test(gate.pathname)) {
    var refused = authorised(request, env);
    if (refused) { return unauthorised(refused); }
  }
  return route(request);
}

async function route(request) {
  var url = new URL(request.url);
  var versioned = stripVersion(url.pathname);

  if (!versioned) { return serve(request, url); }

  if (versioned.version !== CURRENT_VERSION) {
    return jsonError(url.pathname, 404, "unknown_version",
                     "Version v" + versioned.version + " does not exist. " +
                     "The current version is v" + CURRENT_VERSION + ".");
  }

  var bare = new URL(url.toString());
  bare.pathname = versioned.pathname;

  /* Anything asked for under /v1 is the data surface by definition, so
     a miss there answers as JSON whatever the Accept header says - the
     bare path might be an HTML page, but nobody reaches it through a
     version prefix to read it in a browser. */
  var response = await serve(new Request(bare.toString(), {
    method: request.method,
    headers: request.headers,
    redirect: "manual"
  }), bare, true, url.pathname);

  var stamped = new Headers(response.headers);
  stamped.set("X-API-Version", "v" + versioned.version);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: stamped
  });
}

/* `asked` is the path the client actually typed. Under a version
   prefix that differs from the path we fetch, and an error that
   reports a URL the caller never used is a worse answer than no
   error at all. */
async function serve(request, url, versioned, asked) {
  if (request.method !== "GET" && request.method !== "HEAD") {
    return fetch(request);
  }

  var htmlResponse = null;

  if (wantsMarkdown(request.headers.get("Accept"))) {
    var target = markdownPath(url.pathname);

    if (target) {
      var mdUrl = new URL(url.toString());
      mdUrl.pathname = target;

      var md = await fetch(new Request(mdUrl.toString(), {
        method: request.method,
        headers: request.headers,
        redirect: "manual"
      }));

      if (md.status === 200) {
        return withVary(md, MD_TYPE);
      }

      /* A missing page should still answer in the format that was asked
         for, and it must keep its 404 rather than becoming a 200. */
      htmlResponse = await fetch(request);
      if (htmlResponse.status === 404) {
        var notFound = new URL(url.toString());
        notFound.pathname = "/404.md";
        var body = await fetch(notFound.toString());
        if (body.status === 200) {
          var headers = new Headers();
          headers.set("Content-Type", MD_TYPE);
          headers.set("Vary", VARY);
          headers.set("Cache-Control", "no-store");
          return new Response(await body.text(), {
            status: 404,
            statusText: "Not Found",
            headers: headers
          });
        }
      }
    }
  }

  if (!htmlResponse) { htmlResponse = await fetch(request); }

  /* A JSON file that exists is served by the origin as JSON already;
     this is only for the case where nothing is there. */
  if (htmlResponse.status === 404 &&
      (versioned ||
       shouldErrorAsJson(url.pathname, request.headers.get("Accept")))) {
    var shown = asked || url.pathname;
    return jsonError(shown, 404, "not_found",
                     "No resource exists at " + shown);
  }

  return withVary(htmlResponse, null);
}

export default {
  fetch: function (request, env) { return handle(request, env); }
};
