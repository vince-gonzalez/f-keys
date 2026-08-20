"""
============================================================
test_parity — the Python and the JavaScript must agree
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
keyj-cli and keyj/app.html are two implementations of the same
conversions. Key-J already shipped three defects that existed
only because two copies of one thing drifted apart, so this
does not take the port on trust.

It lifts the real functions out of app.html, runs them under
node against the same inputs as the Python, and diffs the
results. If node is not installed the parity checks skip and
say so - a check that cannot run must not report success.

Run:  python tests/test_parity.py
============================================================
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from keyj import notes, sequence, tab          # noqa: E402

APP = os.path.normpath(os.path.join(HERE, "..", "..", "keyj", "app.html"))

WANTED = ["midiToName", "midiToFreq", "nameToFreq",
          "looksLikeTab", "readFrets", "parseTab", "parseTyped"]

TAB_SAMPLE = """
e|-----------------|
B|-----------------|
G|--9---11--9------|
D|-----------------|
A|--12-------------|
E|-----------------|
"""

TAB_RAGGED = """
e|--5--7--|
B|--5--7--|
G|--------|
"""


def extract(source, name):
    """Slice one function out of the file by matching its braces."""
    key = "function " + name + "("
    i = source.index(key)
    depth, j = 0, source.index("{", i)
    start = j
    while j < len(source):
        if source[j] == "{":
            depth += 1
        elif source[j] == "}":
            depth -= 1
            if depth == 0:
                return source[i:j + 1]
        j += 1
    raise ValueError("unbalanced braces in " + name)


def js_harness():
    """The real functions from app.html, plus a driver that prints JSON."""
    src = open(APP, encoding="utf-8").read()
    parts = [src[src.index("var TUNINGS = {"):src.index("};", src.index("var TUNINGS = {")) + 2],
             src[src.index("var NOTE_NAMES = ['C',"):
                 src.index("\n", src.index("var MAX_CHARS"))]]
    for name in WANTED:
        parts.append(extract(src, name))
    parts.append("""
var input = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
var out = {};
out.midiToName = input.midi.map(midiToName);
out.midiToFreq = input.midi.map(function (m) { return midiToFreq(m); });
out.nameToFreq = input.names.map(function (n) { var f = nameToFreq(n);
  return f === null ? null : f; });
out.typed = parseTyped(input.typed);
out.tabs = input.tabs.map(function (t) {
  var r = parseTab(t.text, t.tuning, t.capo);
  return { error: r.error || null, blocks: r.blocks, strings: r.strings,
           skipped: r.skipped, names: r.notes.map(function (n) { return n.name; }) };
});
process.stdout.write(JSON.stringify(out));
""")
    return "\n".join(parts)


def run_js(payload):
    with tempfile.TemporaryDirectory() as d:
        hp = os.path.join(d, "harness.js")
        ip = os.path.join(d, "input.json")
        open(hp, "w", encoding="utf-8").write(js_harness())
        open(ip, "w", encoding="utf-8").write(json.dumps(payload))
        res = subprocess.run([NODE, hp, ip], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError("node failed: " + res.stderr[:400])
        return json.loads(res.stdout)


def have_node():
    for name in ("node", "node.exe"):
        try:
            subprocess.run([name, "--version"], capture_output=True, check=True)
            return name
        except Exception:
            continue
    return None


NODE = have_node()

FAILURES = []


def check(label, got, want):
    if got == want:
        print("  ok    " + label)
    else:
        FAILURES.append(label)
        print("  FAIL  " + label)
        print("        python: {!r}".format(got)[:200])
        print("        js    : {!r}".format(want)[:200])


def main():
    midi = list(range(24, 109))                    # C1 to C8, past Key-J's range
    names = ["C4", "c4", "A4", "F#5", "Bb3", "G-1", "H4", "", "E5", "Db2"]
    typed = "E5 G5 B5 E6, D5|A4  banana C-1"
    tabs = [
        {"text": TAB_SAMPLE, "tuning": "Standard (EADGBe)", "capo": 0},
        {"text": TAB_SAMPLE, "tuning": "Drop D", "capo": 2},
        {"text": TAB_RAGGED, "tuning": "Standard (EADGBe)", "capo": 0},
        {"text": "not a tab at all", "tuning": "Standard (EADGBe)", "capo": 0},
    ]

    # ── the Python side ──────────────────────────────────────
    py = {
        "midiToName": [notes.midi_to_name(m) for m in midi],
        "midiToFreq": [notes.midi_to_freq(m) for m in midi],
        "nameToFreq": [notes.name_to_freq(n) for n in names],
        "typed": sequence.parse(typed),
        "tabs": [],
    }
    for t in tabs:
        r = tab.parse(t["text"], t["tuning"], t["capo"])
        py["tabs"].append({
            "error": r.error, "blocks": r.blocks, "strings": r.strings,
            "skipped": r.skipped, "names": [n.name for n in r.notes]})

    # ── things true regardless of node ───────────────────────
    print("standalone")
    check("A4 is 440 Hz", round(notes.midi_to_freq(69), 6), 440.0)
    check("middle C is C4", notes.midi_to_name(60), "C4")
    check("name round trip", notes.name_to_midi("F#5"), 78)
    check("unreadable name is None", notes.name_to_midi("H4"), None)
    rt = sequence.parse(sequence.format(py["tabs"][0] and
                                        [notes.Note.from_name(x)
                                         for x in ["E5", "G5", "B5", "E6"]]))
    check("text round trip", [n.name for n in rt.notes], ["E5", "G5", "B5", "E6"])
    check("comments stripped",
          [n.name for n in sequence.parse("# hi\nE5 G5\n").notes], ["E5", "G5"])
    check("ragged block is reported, not guessed",
          len(py["tabs"][2]["skipped"]) > 0, True)

    if NODE is None:
        print("\nparity  SKIPPED - node is not installed, so the JavaScript "
              "side could not be run.")
        print("        This is not a pass. Install node and run again.")
        return 1 if FAILURES else 2

    print("\nparity against keyj/app.html")
    js = run_js({"midi": midi, "names": names, "typed": typed, "tabs": tabs})

    check("midi -> name, 85 pitches", py["midiToName"], js["midiToName"])
    check("midi -> Hz, 85 pitches",
          [round(v, 9) for v in py["midiToFreq"]],
          [round(v, 9) for v in js["midiToFreq"]])
    check("name -> Hz, including the unreadable",
          [None if v is None else round(v, 9) for v in py["nameToFreq"]],
          [None if v is None else round(v, 9) for v in js["nameToFreq"]])
    check("typed sequence, notes",
          [n.name for n in py["typed"].notes],
          [n["name"] for n in js["typed"]["notes"]])
    check("typed sequence, skipped",
          py["typed"].skipped, js["typed"]["skipped"])
    for i, (a, b) in enumerate(zip(py["tabs"], js["tabs"])):
        label = "tab {} ({})".format(i, tabs[i]["tuning"])
        check(label + " notes", a["names"], b["names"])
        check(label + " report",
              (a["blocks"], a["strings"], len(a["skipped"]), bool(a["error"])),
              (b["blocks"], b["strings"], len(b["skipped"]), bool(b["error"])))

    print("")
    if FAILURES:
        print("  {} FAILED: {}".format(len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("  the Python and the JavaScript agree everywhere checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
