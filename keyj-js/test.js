/*
============================================================
test - the package answers what the app answers
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
index.js is generated from keyj/app.html, so the failure mode
is not a wrong answer - it is a build that lifted half a
function, or dropped a constant the rest depends on, and still
wrote a file. The first build did exactly that: it took
NOTE_NAMES but stopped before MAX_CHARS, so parseTab threw
ReferenceError the moment it was called, and the build had
reported success.

So this calls every exported function. A module that imports
cleanly and throws on use is not a passing build.

Run:  node keyj-js/test.js
============================================================
*/

var k = require("./index.js");

var failures = [];
var NL = String.fromCharCode(10);

function check(name, got, want) {
  if (JSON.stringify(got) !== JSON.stringify(want)) {
    failures.push(name + NL + "      got:      " + JSON.stringify(got) +
                  NL + "      expected: " + JSON.stringify(want));
  }
}

var TAB = [
  "e|-----------------|",
  "B|-----------------|",
  "G|--9---11--9------|",
  "D|-----------------|",
  "A|-----------------|",
  "E|-----------------|"
].join(NL);

function names(result) {
  return result.notes.map(function (n) { return n.name; }).join(" ");
}

// ── every export is callable ─────────────────────────────────
var expected = ["TUNINGS", "NOTE_NAMES", "midiToName", "midiToFreq",
                "nameToFreq", "looksLikeTab", "readFrets", "parseTab",
                "parseTyped"];
expected.forEach(function (name) {
  check("exports " + name, typeof k[name] !== "undefined", true);
});

// ── conversions ──────────────────────────────────────────────
check("midiToName(60) is middle C", k.midiToName(60), "C4");
check("midiToName(69) is A4", k.midiToName(69), "A4");
check("midiToFreq(69) is concert pitch", k.midiToFreq(69), 440);
check("nameToFreq agrees with midiToFreq", k.nameToFreq("A4"), 440);
check("nameToFreq refuses nonsense", k.nameToFreq("not a note"), null);

// ── tablature ────────────────────────────────────────────────
check("looksLikeTab on a tab", k.looksLikeTab(TAB), true);
check("looksLikeTab on prose", k.looksLikeTab("not a tab at all"), false);

check("parseTab in standard tuning", names(k.parseTab(TAB, "Standard (EADGBe)", 0)),
      "E4 F#4 E4");

// A capo raises every note by its fret count. Two frets from E4 is F#4.
check("a capo of 2 raises it a tone",
      names(k.parseTab(TAB, "Standard (EADGBe)", 2)), "F#4 G#4 F#4");

check("an unknown tuning is an error, not a crash",
      k.parseTab(TAB, "no such tuning", 0).error, "Unknown tuning.");

check("prose is not silently read as tablature",
      k.parseTab("not a tab at all", "Standard (EADGBe)", 0).notes.length, 0);

// ── typed input ──────────────────────────────────────────────
check("parseTyped reads note names",
      k.parseTyped("C4 E4 G4").notes.map(function (n) { return n.name; }),
      ["C4", "E4", "G4"]);

// ── the shape of the catalogue ───────────────────────────────
check("eight tunings ship", Object.keys(k.TUNINGS).length, 8);
check("standard tuning is one of them",
      Object.keys(k.TUNINGS).indexOf("Standard (EADGBe)") !== -1, true);

if (failures.length) {
  console.log("keyj-js: " + failures.length + " FAILED" + NL);
  failures.forEach(function (f) { console.log("  - " + f + NL); });
  process.exit(1);
}

console.log("keyj-js: 18 cases ok");
