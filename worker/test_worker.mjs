/*
============================================================
test_worker - the negotiation, without deploying it
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The two things this Worker can get wrong are both silent.
Reading `text/html, text/markdown;q=0` as a request for
markdown hands every browser a text file. Mapping /keyj/ to
the wrong .md hands an agent the homepage and it has no way
to know. Neither shows up in a deploy log.

So both are tested here against a fake origin, with no
network and no wrangler, and run in CI beside the site gate.

Run:  node worker/test_worker.mjs
============================================================
*/

import worker from "./index.js";

var failures = [];

function check(name, actual, expected) {
  var ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) {
    failures.push(name + "\n      got:      " + JSON.stringify(actual) +
                  "\n      expected: " + JSON.stringify(expected));
  }
}

/* A stand-in for GitHub Pages: the pages that exist, and a 404 for
   everything else, so the fallback path is exercised rather than
   assumed. */
var ORIGIN = {
  "/": "<html>home</html>",
  "/index.md": "# F-Keys\n",
  "/keyj/": "<html>keyj</html>",
  "/keyj/index.md": "# Key-J\n",
  "/apps.html": "<html>apps</html>",
  "/apps.md": "# Apps\n",
  "/404.md": "# 404\n",
  "/win98.css": "body{}",
  "/llms.txt": "# F-Keys\n"
};

globalThis.fetch = async function (input) {
  var url = new URL(typeof input === "string" ? input : input.url);
  var body = ORIGIN[url.pathname];
  if (body === undefined) {
    return new Response("<html>not found</html>", {
      status: 404,
      headers: { "Content-Type": "text/html; charset=utf-8" }
    });
  }
  var type = url.pathname.endsWith(".md") ? "text/markdown"
    : url.pathname.endsWith(".css") ? "text/css"
    : url.pathname.endsWith(".txt") ? "text/plain"
    : "text/html; charset=utf-8";
  return new Response(body, { status: 200, headers: { "Content-Type": type } });
};

async function get(path, accept) {
  var headers = {};
  if (accept) { headers.Accept = accept; }
  var res = await worker.fetch(
    new Request("https://f-keys.com" + path, { headers: headers }));
  return {
    status: res.status,
    type: res.headers.get("Content-Type"),
    vary: res.headers.get("Vary"),
    body: await res.text()
  };
}

var MD = "text/markdown; charset=utf-8";
var HTML = "text/html; charset=utf-8";
var VARY = "Accept, Accept-Encoding";

var cases = [
  // an agent asking for markdown gets markdown, at every path shape
  ["/ with markdown", "/", "text/markdown",
   { status: 200, type: MD, vary: VARY, body: "# F-Keys\n" }],
  ["/keyj/ with markdown", "/keyj/", "text/markdown",
   { status: 200, type: MD, vary: VARY, body: "# Key-J\n" }],
  ["/apps.html with markdown", "/apps.html", "text/markdown",
   { status: 200, type: MD, vary: VARY, body: "# Apps\n" }],
  ["/keyj without a slash", "/keyj", "text/markdown",
   { status: 200, type: MD, vary: VARY, body: "# Key-J\n" }],

  // a browser gets HTML, and the response still says what it varied on
  ["a browser", "/",
   "text/html,application/xhtml+xml,image/avif,*/*;q=0.8",
   { status: 200, type: HTML, vary: VARY, body: "<html>home</html>" }],
  ["no Accept at all", "/", null,
   { status: 200, type: HTML, vary: VARY, body: "<html>home</html>" }],

  // q-values decide, and q=0 is a refusal rather than a request
  ["markdown preferred by q", "/", "text/html;q=0.8, text/markdown;q=1.0",
   { status: 200, type: MD, vary: VARY, body: "# F-Keys\n" }],
  ["html preferred by q", "/", "text/markdown;q=0.1, text/html;q=0.9",
   { status: 200, type: HTML, vary: VARY, body: "<html>home</html>" }],
  ["markdown refused by q=0", "/", "text/html, text/markdown;q=0",
   { status: 200, type: HTML, vary: VARY, body: "<html>home</html>" }],

  // a file that is already its own format is never negotiated away
  ["a stylesheet", "/win98.css", "text/markdown",
   { status: 200, type: "text/css", vary: VARY, body: "body{}" }],
  ["llms.txt", "/llms.txt", "text/markdown",
   { status: 200, type: "text/plain", vary: VARY, body: "# F-Keys\n" }],

  // a missing page answers in the format asked for and keeps its status
  ["a missing page, markdown", "/nope", "text/markdown",
   { status: 404, type: MD, vary: VARY, body: "# 404\n" }],
  ["a missing page, browser", "/nope", "text/html",
   { status: 404, type: HTML, vary: VARY, body: "<html>not found</html>" }]
];

/* An agent that asked for JSON cannot parse an HTML error page to find
   out that it failed. These check the envelope openapi.json documents,
   and that html still wins a tie so a browser never gets JSON. */
var JSON_TYPE = "application/json; charset=utf-8";

var jsonCases = [
  ["a missing .json path", "/nope.json", "application/json", "not_found"],
  ["a missing page, json", "/nope", "application/json", "not_found"],
  ["json preferred by q", "/nope", "text/html;q=0.2, application/json;q=0.9",
   "not_found"],
  ["json refused by q=0", "/nope", "text/html, application/json;q=0", null],
  ["a browser still gets html", "/nope", "text/html", null],

  /* curl, requests and fetch all send `Accept: * /*` unless told
     otherwise, so an auditor probing for JSON errors never names the
     type. A .json path answering that with markup is the whole defect
     this exists to prevent. */
  [".json under */*", "/nope.json", "*/*", "not_found"],
  [".json with no Accept at all", "/nope.json", null, "not_found"],
  ["/api under */*", "/api/v1/thing", "*/*", "not_found"],
  ["/v1 under */*", "/v1/anything", "*/*", "not_found"],

  /* but a page path is still a page, and an explicit browser request
     for a .json path still gets the page rather than a blob */
  ["a page path under */* stays html", "/nope", "*/*", null],
  ["a browser on a .json path", "/nope.json", "text/html", null]
];

for (var i = 0; i < cases.length; i++) {
  var c = cases[i];
  check(c[0], await get(c[1], c[2]), c[3]);
}

for (var k = 0; k < jsonCases.length; k++) {
  var jc = jsonCases[k];
  var res = await get(jc[1], jc[2]);

  if (jc[3] === null) {
    check(jc[0], { type: res.type, status: res.status },
                 { type: HTML, status: 404 });
    continue;
  }

  var parsed = null;
  try { parsed = JSON.parse(res.body); } catch (e) { parsed = null; }
  var err = parsed && parsed.error;

  check(jc[0], {
    status: res.status,
    type: res.type,
    vary: res.vary,
    code: err && err.code,
    path: err && err.path,
    message: !!(err && err.message),
    hints: !!(err && err.hints && err.hints.length >= 3)
  }, {
    status: 404,
    type: JSON_TYPE,
    vary: VARY,
    code: jc[3],
    path: jc[1],
    message: true,
    hints: true
  });
}

if (failures.length) {
  console.log("test_worker: " + failures.length + " FAILED\n");
  for (var f = 0; f < failures.length; f++) {
    console.log("  - " + failures[f] + "\n");
  }
  process.exit(1);
}

console.log("test_worker: " + (cases.length + jsonCases.length) + " cases ok");
