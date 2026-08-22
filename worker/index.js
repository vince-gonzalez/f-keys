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

async function handle(request) {
  var url = new URL(request.url);

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
  if (htmlResponse.status === 404 && wantsJson(request.headers.get("Accept"))) {
    return jsonError(url.pathname, 404, "not_found",
                     "No resource exists at " + url.pathname);
  }

  return withVary(htmlResponse, null);
}

export default {
  fetch: handle
};
