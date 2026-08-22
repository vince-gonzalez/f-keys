/*
============================================================
status.js - the page keeps up with the file behind it
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The status page was rendered once a day into static HTML, so
a refresh showed whatever the build had baked in - and a CDN
holding that HTML meant a reader could be looking at numbers
from days ago with nothing on the page admitting it.

This re-reads status/latest.json on load and repaints from it.
The server-rendered page is the fallback and is complete on
its own, so with JavaScript off nothing is lost but the
freshness.

It does NOT own the layout. The table spec is emitted into the
page by tools/statuspage.py and read back here, so there is
one description of what the page is. The formatters below are
the only thing written twice, and tools/test_statuspage.py
runs this file under node against the same snapshot and fails
the build if the two renderings differ by one character.

No cookies, no beacons, no third party: one same-origin GET of
a file that is already public.
============================================================
*/

(function () {
  "use strict";

  // ── the shared vocabulary, twin of FORMATS in statuspage.py ──
  function group(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  var FORMATS = {
    num: function (v) {
      return (v === null || v === undefined) ? "—" : group(v);
    },
    text: function (v) {
      return (v === null || v === undefined || v === "") ? "—" : String(v);
    },
    ms: function (v) {
      return (v === null || v === undefined) ? "—" : group(v) + "ms";
    },
    date: function (v) { return !v ? "—" : String(v).slice(0, 10); },
    ver: function (v) { return !v ? "—" : "v" + String(v); },
    up: function (v) { return v ? "UP" : "DOWN"; }
  };

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function dig(obj, path) {
    var cur = obj, parts = path.split("."), i;
    for (i = 0; i < parts.length; i++) {
      if (cur === null || typeof cur !== "object" || !(parts[i] in cur)) {
        return null;
      }
      cur = cur[parts[i]];
    }
    return cur;
  }

  function rowsFor(snap, source) {
    if (source === "packages") {
      return (snap.npm || []).concat(snap.pypi || []);
    }
    var got = dig(snap, source);
    return Object.prototype.toString.call(got) === "[object Array]" ? got : [];
  }

  function n(v) { return v || 0; }

  // twin of sort_rows() in statuspage.py
  function sortRows(id, rows) {
    var out = rows.slice();
    if (id === "papers") {
      out.sort(function (a, b) { return n(b.downloads) - n(a.downloads); });
    } else if (id === "repos") {
      out.sort(function (a, b) {
        if (n(b.stars) !== n(a.stars)) { return n(b.stars) - n(a.stars); }
        var x = a.full_name || "", y = b.full_name || "";
        return x < y ? -1 : (x > y ? 1 : 0);
      });
    } else if (id === "packages") {
      out.sort(function (a, b) { return n(b.weekly) - n(a.weekly); });
    } else if (id === "traffic") {
      out.sort(function (a, b) { return n(b.page_views) - n(a.page_views); });
    }
    return out;
  }

  function renderBody(section, snap) {
    var rows = sortRows(section.id, rowsFor(snap, section.source));
    var html = "", i, j, col, cells;
    for (i = 0; i < rows.length; i++) {
      cells = "";
      for (j = 0; j < section.columns.length; j++) {
        col = section.columns[j];
        cells += '<td class="' + col[3] + '">' +
                 esc(FORMATS[col[2]](rows[i][col[1]])) + "</td>";
      }
      html += "<tr>" + cells + "</tr>";
    }
    return html || '<tr><td class="dim">no data</td></tr>';
  }

  // Exported for the parity test, which has no DOM to paint into.
  var api = { FORMATS: FORMATS, renderBody: renderBody, sortRows: sortRows,
              rowsFor: rowsFor, esc: esc };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; }
  if (typeof window === "undefined") { return; }
  window.__statusRender = api;

  // ── the live half ────────────────────────────────────────────
  function spec() {
    var el = document.getElementById("status-spec");
    if (!el) { return null; }
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  function paint(snap, sp) {
    var i, el, key, fmt, nodes;

    nodes = document.querySelectorAll("[data-k]");
    for (i = 0; i < nodes.length; i++) {
      el = nodes[i];
      key = el.getAttribute("data-k");
      fmt = el.getAttribute("data-f") || "num";
      el.textContent = FORMATS[fmt]((snap.summary || {})[key]);
    }

    for (i = 0; i < sp.sections.length; i++) {
      var body = document.querySelector('[data-body="' + sp.sections[i].id + '"]');
      if (body) { body.innerHTML = renderBody(sp.sections[i], snap); }
    }

    var stamp = document.getElementById("generated-at");
    if (stamp && snap.generated_at) { stamp.textContent = snap.generated_at; }
  }

  function note(text, cls) {
    var el = document.getElementById("live-note");
    if (!el) { return; }
    el.textContent = text;
    el.className = cls || "dim";
  }

  function load() {
    var sp = spec();
    if (!sp) { return; }
    // cache: no-store, because the whole point is not to be served the
    // copy the CDN kept from the last person who looked
    fetch("/status/latest.json", { cache: "no-store" })
      .then(function (r) {
        if (!r.ok) { throw new Error("HTTP " + r.status); }
        return r.json();
      })
      .then(function (snap) {
        paint(snap, sp);
        note("Live — re-read " + (snap.generated_at || "just now") +
             " on this page load.", "ok");
      })
      .catch(function (e) {
        // the server-rendered numbers are still on the page and still
        // true as of the build; say which it is rather than pretending
        note("Showing the numbers built into this page. Could not re-read " +
             "status/latest.json (" + e.message + ").", "down");
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", load);
  } else {
    load();
  }
}());
