/*
============================================================
f-keys-vanity - a product name that is also an address
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
A product is easier to say than a path. "saydo dot f-keys dot
com" survives being read out; "f-keys.com slash saydo" does
not. So each product answers to its own name.

What it is NOT is a second site. Every vanity host redirects,
permanently, to the one canonical page:

    saydo.f-keys.com/anything?q=1
      -> https://f-keys.com/saydo/anything?q=1

That direction matters. A subdomain that SERVED the page
would be a second copy of it, and search engines treat a
subdomain as a separate site starting from no reputation at
all. Redirecting keeps one canonical URL and lends the name
to the page rather than splitting it away from it.

This is deliberately a separate Worker from f-keys-markdown.
That one negotiates Accept in front of GitHub Pages and has
one job; this one has a different job, and two jobs in one
file is how both of them get harder to read.

WORKFLOW STACK
  1. label()    - the first dot-separated piece of the host
  2. fetch()    - 301 to the product page, path and query kept

Deploy:  cd vanity && npx wrangler deploy
Check:   curl -sSI https://saydo.f-keys.com/
         -> location: https://f-keys.com/saydo/
============================================================
*/

var CANONICAL = "https://f-keys.com";

/* Hosts that do a real job of their own and must never be
   redirected, even if a route is ever pointed here by mistake.
   A redirect loop on the apex would take the whole site down,
   so the apex is named here rather than assumed absent. */
var RESERVED = {
  "f-keys.com": true, "www.f-keys.com": true, "qv.f-keys.com": true,
  "prompt.f-keys.com": true, "dp.f-keys.com": true, "wiki.f-keys.com": true,
  "pay.f-keys.com": true, "email.f-keys.com": true
};

/* "saydo.f-keys.com" -> "saydo". Everything this Worker is
   routed to is a *.f-keys.com host, so the first label is the
   product slug and the rest is the zone. */
function label(host) {
  var dot = host.indexOf(".");
  return dot === -1 ? host : host.slice(0, dot);
}

export default {
  fetch: function (request) {
    var url = new URL(request.url);
    var host = url.hostname.toLowerCase();

    /* Not ours to redirect: hand it straight back to the origin
       rather than guessing. */
    if (RESERVED[host]) {
      return fetch(request);
    }

    var slug = label(host);
    if (!slug) {
      return Response.redirect(CANONICAL + "/", 301);
    }

    /* url.pathname always begins with "/", so trimming the leading
       slash keeps "/saydo/" + "" for a bare host and
       "/saydo/" + "manual/" for a deeper one. */
    var rest = url.pathname.slice(1);
    var target = CANONICAL + "/" + slug + "/" + rest + url.search;

    return Response.redirect(target, 301);
  }
};
