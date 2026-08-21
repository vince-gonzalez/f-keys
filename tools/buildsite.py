#!/usr/bin/env python3
"""
============================================================
buildsite — generates every page of f-keys.com
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
Thirteen hand-written pages each carried their own copy of
the chrome, so they drifted into different websites. The
catalogue below is the single source of truth; the shell is
written once; every page is generated. Two pages cannot
disagree about the navigation because there is only one
navigation.

WORKFLOW STACK
  1. CATALOGUE  — every product, its category, status, blurb
  2. PAGES      — the long-form detail for each product
  3. shell()    — Explorer window: tree left, content right
  4. main()     — writes index.html, a page per category, and
                  a page per product

Run:  python tools/buildsite.py
============================================================
"""

import html
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── status vocabulary ────────────────────────────────────────
READY = ("Ready", "st-ready")
DISCORD = ("In Discord", "st-plat")
FORTNITE = ("In Fortnite", "st-plat")
SETUP = ("Needs setup", "st-setup")
ALPHA = ("Alpha", "st-setup")
PIP = ("pip install", "st-ready")
PUBLISHED = ("Published", "st-ready")
LIVE = ("Live", "st-ready")

# ── the catalogue ────────────────────────────────────────────
# (slug, name, category, type, status, one-line, href)
CATALOGUE = [
    ("keyj", "Key-J", "apps", "Application", READY,
     "Every keystroke plays a note, in any application. Live staff, WAV export.", "/keyj/"),
    ("pixelstaff", "Pixel Staff", "apps", "Application", READY,
     "An 8-bit composer. Piano roll, waveform per channel, WAV or ringtone out.", "/pixelstaff/"),
    ("opticquiz", "OpticQuiz", "apps", "Web app", READY,
     "Colour-vision and acuity tests that run entirely in the browser.", "https://opticquiz.com"),
    ("qv", "QV", "apps", "Web app", READY,
     "Live ballots. Put a question to a room and watch the count move.", "/qv/"),
    ("remapwrap", "RemapWrap", "apps", "Application", ALPHA,
     "Any smartphone becomes a programmable macro pad. No app, no dongle.", "/remapwrap/"),

    ("trailer-load", "Trailer Load", "games", "Simulator", READY,
     "Warehouse load training that plays like a game. Institutional licensing.", "https://trailer-load.com"),
    ("prompt", "PROMPT", "games", "Discord activity", DISCORD,
     "A multiplayer word game inside Discord, in a 90s CRT shell.", "https://prompt.f-keys.com"),
    ("daisupop", "DaisuPop", "games", "Discord activity", DISCORD,
     "A dice popper. Everyone in the room sees the same roll at the same moment.", "https://dp.f-keys.com"),
    ("micdrop", "MICDROP", "games", "Fortnite island", FORTNITE,
     "A live open-mic arena. 120 seconds to win the crowd. Code 1534-0440-5810.", "/micdrop/"),
    ("fytecraft", "FyteCraft", "games", "Game", ALPHA,
     "An RTS built around combat rather than base-building. Early, and openly so.", "https://github.com/zengineco/fytecraft.com"),

    ("wikipolish", "WikiPolish", "tools", "Web tool", READY,
     "Grammar scout for Wikipedia. Finds a first edit nobody will revert.", "/wikipolish/"),
    ("leadseer", "LeadSeer", "tools", "Desktop tool", SETUP,
     "Finds the local businesses that still have no website.", "/leadseer/"),
    ("plumhud", "PlumHUD", "tools", "Python package", PIP,
     "Miner fleet monitor. Overlay HUD, alerts, and local history.", "/plumhud/"),

    ("streamsniper", "Stream Sniper", "hardware", "Appliance", SETUP,
     "A spare mini PC shows a channel fullscreen the moment it goes live.", "/streamsniper/"),
    ("moonbeam", "Moonbeam", "hardware", "Python package", PIP,
     "Finds the NerdMiners on your network and reads their vitals.", "/moonbeam/"),

    ("gonzalgo", "gonzalgo", "research", "Research tool", PUBLISHED,
     "Which axioms a Lean 4 or Metamath theorem spends rather than inherits.", "/gonzalgo/"),
    ("papers", "Papers", "research", "Publications", PUBLISHED,
     "Where formal libraries spend their axioms. Full text, DOIs, archives.", "/papers/"),
    ("modulign", "Modulign", "research", "Standard", PUBLISHED,
     "A dimensional address grammar for observable reality. DAG-OR v3.", "https://modulign.org"),

    ("5best2buy", "5Best2Buy", "properties", "Website", LIVE,
     "A sourcing map for independent American food.", "https://www.5best2buy.com"),
    ("poticas", "Poticas", "properties", "Website", LIVE,
     "The home of potica. History, method, and who still ships one.", "https://poticas.com"),
    ("tipstreams", "TipStreams", "properties", "Website", LIVE,
     "Branded tip pages and OBS overlays. The widget never touches money.", "https://tipstreams.com"),
    ("fundoge", "FunDoge", "properties", "Website", LIVE,
     "Free isometric mini-golf in the browser.", "https://dogefundme.com"),
]

CATEGORIES = [
    ("apps", "Apps", "Things you sit in front of and use."),
    ("games", "Games", "Things you play."),
    ("tools", "Tools", "Things that do the work for you."),
    ("hardware", "Hardware", "Software that makes a box do one thing forever."),
    ("research", "Research", "Things you read. Every claim carries a DOI."),
    ("properties", "Properties", "Sites that stand on their own."),
]



# ── long-form detail, one entry per product ──────────────────
PAGES = {
 "keyj": dict(
  title="Key-J", tagline="Every keystroke plays a note, in any application.",
  facts=[("Version","1.6.0"),("Licence","Proprietary"),("Platforms","Browser, Windows, Linux"),
         ("Source","zengineco/f-keys")],
  body="""
<h2>What it does</h2>
<p>Your keyboard becomes an instrument. Every keystroke plays a note, the notes land
on a staff as you go, and the session exports as a WAV. With global capture on it
hears your keys in any application.</p>
<h2>Tablature import</h2>
<p>Paste guitar tablature, choose a tuning, and Key-J converts the frets to notes.
Sequence mode then plays that run one note per keystroke, so the pitches are handled
and what is left to you is timing and feel.</p>
<p>Eight tunings including drop D, Eb, DADGAD, seven-string and bass, with a capo
offset. Hammer-ons, slides and bends are read as the notes they land on. A block with
the wrong number of strings produces no notes and says how many it found, rather than
guessing a tuning silently.</p>
<h2>The keyboard</h2>
<p>An on-screen keyboard shows which computer key plays which note, printed on the
key it triggers, so a wrong binding is visible rather than something you find by
ear. Keys light as they sound, from a keystroke or from a sequence.</p>
<p>Turn Build on and click keys to enter a run without typing a single note name -
which is the part that made entering a sequence miserable.</p>
<h2>Also</h2>
<p>Seven tone presets from clean guitar to shred. MIDI import. Six play styles, four
waveforms, remappable keys and scale switching.</p>
<h2>On the command line</h2>
<p>Once a song is in, the workbench is in the way. <code>pip install keyj</code> gives you
the same converter and the same player without the window.</p>
<pre><b>pip install keyj</b>
keyj tab solo.txt -o song.txt    tablature in, note names out
keyj render song.txt out.wav     the sequence, at a tempo
keyj show song.txt               what is in a sequence
keyj play song.txt               any keystroke plays the next note</pre>
<p><code>tab</code>, <code>render</code> and <code>show</code> are standard library only and
never touch your keyboard. <code>play</code> is the one part that needs a global hook, so it
is a separate install: <code>pip install "keyj[play]"</code>. It runs in the foreground and
stops when you stop it &mdash; nothing is added to startup.</p>
<p>It never learns which key you pressed. In sequence mode any key advances, so the player
asks whether a key went down and discards everything else. There is no keystroke buffer in
it, which is the difference between an instrument and a keylogger.</p>
<p>The CLI is MIT. The desktop and browser apps are not &mdash; see
<a href="https://github.com/zengineco/f-keys/blob/main/keyj/LICENSE">the licence</a>.</p>
<div class="btnrow">
  <a class="btn default" href="/keyj/app.html">Open in browser</a>
  <a class="btn" href="https://github.com/zengineco/f-keys/releases/latest">Download</a>
  <a class="btn" href="/keyj/manual/">Manual</a>
  <a class="btn" href="https://pypi.org/project/keyj/">PyPI</a>
  <a class="btn" href="/keyj/privacy/">Privacy</a>
</div>"""),

 "pixelstaff": dict(
  title="Pixel Staff", tagline="An 8-bit composer with no DAW anywhere in it.",
  facts=[("Licence","MIT"),("Platform","Browser"),("Install","None"),("Exports","WAV, ringtone")],
  body="""
<h2>What it does</h2>
<p>Draw notes onto a 96-row piano roll, pick a waveform per channel, set the tempo and
press play. When it sounds right, take it away as a WAV or as a ringtone.</p>
<h2>Controls</h2>
<p>Draw and erase, play, stop and rewind, tempo in BPM, zoom from 1x to 8x, extend the
board and clear it. Square, saw, triangle and sine per channel.</p>
<p>One page, no dependencies. It opens and it works.</p>
<div class="btnrow"><a class="btn default" href="/pixelstaff/app.html">Open Pixel Staff</a></div>"""),

 "qv": dict(
  title="QV", tagline="Live ballots. One tap, one vote, no account.",
  facts=[("Version","0.1.0"),("Platform","Browser"),("Accounts","None required")],
  body="""
<h2>What it does</h2>
<p>Put a question to a room and watch the count move as people answer. A voter token
is issued on arrival, so there is nothing to sign up for and nothing to remember.</p>
<h2>Also</h2>
<p>Opt in to be told when a new ballot opens, so a room can be gathered without chasing
anyone. Creators can apply to run ballots for their own audience.</p>
<div class="btnrow"><a class="btn default" href="https://zengineco.github.io/qv/">Open QV</a></div>"""),

 "micdrop": dict(
  title="MICDROP", tagline="Grab the mic. Survive the room.",
  facts=[("Island code","1534-0440-5810"),("Creator","d00b"),("Platform","Fortnite (UEFN)"),
         ("Support","vincegonzalez@me.com")],
  body="""
<h2>What it does</h2>
<p>A live open-mic arena. Take the stage for 120 seconds and win the crowd, or eat three
boos and get buzzed off to a sad trombone. Out in the crowd you laugh, boo, throw
tomatoes and work the soundboard; spam it and it is off to club jail.</p>
<p>Stack up sets and climb from Open Mic Rookie to Legend of the Mic. Public rooms for
strangers, private ones for bombing among friends.</p>
<h2>Support</h2>
<p>Use Fortnite's in-game reporting for player conduct, since that reaches Epic's
moderation directly. For anything else, write in and a person reads it.</p>
<p class="muted">Not affiliated with or endorsed by Epic Games. Fortnite and UEFN are
trademarks of Epic Games, Inc.</p>
<div class="btnrow">
  <a class="btn default" href="https://www.fortnite.com/@d00b/1534-0440-5810">Play now</a>
  <a class="btn" href="mailto:vincegonzalez@me.com">Contact</a>
</div>"""),

 "wikipolish": dict(
  title="WikiPolish", tagline="Grammar scout for Wikipedia.",
  facts=[("Platform","Browser"),("Install","None"),("Reads","Wikipedia API"),
         ("Checks","LanguageTool")],
  body="""
<h2>What it does</h2>
<p>The hardest part of becoming a Wikipedia editor is finding a first edit you are sure
about. Point WikiPolish at an article and it pulls the current text straight from the
Wikipedia API, runs it through LanguageTool, and shows each language problem where it
occurs.</p>
<p>Language fixes are the safest way in: uncontroversial, easy to justify, and genuinely
useful to the encyclopedia.</p>
<div class="btnrow"><a class="btn default" href="https://zengineco.github.io/wikiscout/">Open WikiPolish</a></div>"""),

 "leadseer": dict(
  title="LeadSeer", tagline="Find who is not online yet.",
  facts=[("Licence","MIT"),("Runtime","Node 18+"),("Needs","Google Maps API key"),
         ("Builds","Electron desktop, React browser")],
  body="""
<h2>What it does</h2>
<p>Every town has businesses doing fine without a website. LeadSeer asks Google Places
which ones they are, filters out the chains, and hands you the list.</p>
<h2>Filters</h2>
<p>Search by category and ZIP. Exclude chains, set a minimum review count and rating, or
narrow to high-value results. Export to CSV, or save automatically after every search.
Past searches persist with session stats.</p>
<p>It runs on your own API key, so the quota and the data are yours.</p>
<div class="btnrow"><a class="btn default" href="https://github.com/zengineco/LeadSeer">Get LeadSeer</a></div>"""),

 "plumhud": dict(
  title="PlumHUD", tagline="Watch the fleet, not the screen.",
  facts=[("Version","4.1.0"),("Licence","MIT"),("Install","pip install plumhud"),
         ("Requires","Python 3.8+, Tk"),("Depends on","moonbeam-miner")],
  body="""
<h2>What it does</h2>
<p>A borderless overlay HUD that sits on top of whatever you are doing, with four display
modes, an opacity slider and five skins. A five-tab command center for miners, analytics,
alerts, skin and settings. Every poll is written to a local database with thirty-day
retention.</p>
<h2>Alerts</h2>
<p>Rules for offline, hashrate below a floor, temperature above a ceiling and reject
spikes, delivered to Discord or Telegram with a per-rule cooldown.</p>
<h2>What version 4 changed</h2>
<p>Nothing is invented any more. Version 3 filled missing readings with random numbers, so
a miner that answered without a hashrate displayed a believable figure you had no way to
identify as fake. A field the miner did not send is now shown as a dash and stored as
null, and alert rules stay quiet rather than reporting an absent measurement as a low one.</p>
<p>The config also stopped moving. It lives in one per-user directory, created owner-only,
because it holds a Discord webhook and a Telegram token.</p>
<pre><b>pip install plumhud</b>
plumhud          the overlay HUD
plumhud check    poll once, print, exit
plumhud where    where config and history live</pre>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/plumhud/">View on PyPI</a>
  <a class="btn" href="https://github.com/zengineco/f-keys/tree/main/plumhud">Source</a>
</div>"""),

 "streamsniper": dict(
  title="Stream Sniper", tagline="They go live. It is on the TV.",
  facts=[("Licence","MIT"),("Platform","Debian or Ubuntu"),
         ("Needs","Streamlink, VLC, pygame"),("Starts","systemd, on boot")],
  body="""
<h2>What it does</h2>
<p>Point a spare mini PC at the television and give it a list of Twitch channels. It shows
a clock until someone goes live, then puts them fullscreen with the ads out of the path.
When the stream ends, the clock comes back.</p>
<h2>How it behaves</h2>
<p>One username per line in a text file, and order is priority: if two are live, the one
nearer the top gets the screen. A stream already playing runs to the end, so nobody higher
in the list can cut in halfway through. Edits apply at the next check, with no restart.</p>
<pre>bash install.sh
<b>sudo systemctl start streamsniper@USER</b></pre>
<div class="btnrow"><a class="btn default" href="https://github.com/zengineco/f-keys/tree/main/streamsniper">Get the source</a></div>"""),

 "moonbeam": dict(
  title="Moonbeam", tagline="Find the NerdMiners on your network.",
  facts=[("Version","1.0.0"),("Licence","MIT"),("Install","pip install moonbeam-miner"),
         ("Requires","Python 3.8+"),("Dependencies","None")],
  body="""
<h2>What it does</h2>
<p>Sweeps your subnet for ESP-Miner and AxeOS devices, NerdMiner and Bitaxe and relatives,
and reads their vitals in a terminal. Whatever answers is remembered, so the next run just
polls them.</p>
<pre><b>pip install moonbeam-miner</b>
moonbeam            the miners it knows, polled now
moonbeam scan       sweep the subnet
moonbeam watch      refresh until you stop it
moonbeam show ip    everything one miner reported</pre>
<h2>A dash means the miner did not say</h2>
<p>It does not mean zero, and it is never a plausible number standing in for one that never
arrived. The summary counts how many devices declined to report rather than quietly
averaging them in.</p>
<p>Standard library only, so the install cannot fail on someone else's package.</p>
<div class="btnrow">
  <a class="btn default" href="https://pypi.org/project/moonbeam-miner/">View on PyPI</a>
  <a class="btn" href="https://github.com/zengineco/f-keys/tree/main/moonbeam">Source</a>
</div>"""),

 "remapwrap": dict(
  title="RemapWrap", tagline="Your phone is already the extra row of keys.",
  facts=[("Version","0.1.0 alpha"),("Runtime","Node.js 16+"),
         ("Phone needs","A browser"),("Install","None on the phone"),
         ("Source","zengineco/f-keys")],
  body="""
<p><img src="/remapwrap/assets/logo-256.png" alt="RemapWrap"
   style="width:132px;height:132px;float:right;margin:0 0 14px 20px"></p>
<h2>What it does</h2>
<p>Runs a small server on your PC. Scan the QR code with your phone and the phone becomes a
drag-and-drop grid of keys that fire <b>real OS-level keystrokes</b>. The software you are
driving does not know RemapWrap exists, which is the whole point: it works with everything,
because it is indistinguishable from a keyboard.</p>
<p>No app on the phone. No hardware. A Stream Deck costs $150 and lives in a drawer; this is
the device already in your hand.</p>

<h2>The company is named after this</h2>
<p>RemapWrap began as <b>F-Keys</b> &mdash; an extra row of keys, on glass you already own.
The name outgrew the product and became the company. The product then went missing for five
months, surviving in a single zip file in a folder called "zip to sort".</p>

<h2>Running it</h2>
<pre>npm install
<b>npm start</b>
scan the QR with your phone</pre>
<p>Both devices need to be on the same network. Ports 7331 and 7332 must be open locally.
Keystroke injection is handled by <code>@nut-tree-fork/nut-js</code>.</p>

<h2>Alpha, and said plainly</h2>
<p>This is v0.1.0 and has never been packaged. It runs from source, layouts are JSON edited
live, and nothing about it has been hardened. It is published because a design that exists
only in a zip file is a design that gets lost &mdash; and this one nearly was.</p>
<div class="btnrow">
  <a class="btn default" href="https://github.com/zengineco/f-keys/tree/main/remapwrap">Get the source</a>
</div>"""),

}


ABOUT_DOC = """
<div class="doc"><h1>About F-Keys</h1>
<p class="sub">Independent products built by Vincent Gonzalez.</p>
<table class="facts">
<tr><th>Entity</th><td>F-Keys Creative LLC (Florida)</td></tr>
<tr><th>Trading as</th><td>F-Keys</td></tr>
<tr><th>ORCID</th><td>0009-0005-3640-014X</td></tr>
<tr><th>Contact</th><td>vincegonzalez@me.com</td></tr>
</table>
<h2>What this is</h2>
<p>F-Keys is Vince Gonzalez, working alone. Twenty-two products are live, from
browser games to formal proof tooling, and each is built end to end by the same
person: architecture, both ends, database, deployment, documentation.</p>
<h2>The recurring interest</h2>
<p>Provenance - what a result actually rests on. gonzalgo reads a compiled Lean 4
or Metamath library and reports which axioms a theorem spends rather than quietly
inherits. OpticQuiz runs one colour-vision engine across eight distribution
channels, with its JavaScript and Python implementations verified identical to six
decimal places, and publishes the calibration limits that keep its own results
honest.</p>
<p>More than thirty works are deposited with DOIs. The packages are installed
several hundred times a week.</p>
<h2>Current interests</h2>
<p>Accessibility &middot; hardware interfaces &middot; creator tools &middot; gaming
&middot; formal methods &middot; the open web.</p>
<div class="btnrow">
  <a class="btn default" href="/papers/">Read the papers</a>
  <a class="btn" href="/log/">Working log</a>
  <a class="btn" href="/status/">Status</a>
</div>
</div>
"""

EXTRA_NODES = [("/about.html", "About"), ("/log/", "Log"), ("/status/", "Status"), ("/papers/", "Papers")]


def esc(s):
    return html.escape(str(s), quote=True)


# ── the shell ────────────────────────────────────────────────

# The Key-J manual. Written because an FL Studio veteran needed a solid
# session of tinkering to find sequence mode, and a feature nobody can
# find is a feature nobody has.
KEYJ_MANUAL = """
<h2>Which Key-J are you holding</h2>
<p>There are two, and the difference decides what the app can do at all.</p>
<table class="facts">
<tr><th>In a browser</th><td>Notes play while the Key-J tab has focus. Nothing else.</td></tr>
<tr><th>The desktop app</th><td>Notes play while you type in any application, once
Global Capture is switched on.</td></tr>
</table>
<p>A browser cannot see keystrokes outside its own page, and it should not be able
to &mdash; a page that could read what you type into your bank would be a keylogger.
So the browser version is not a crippled desktop version, it is at its permanent
ceiling. The header tells you which one you have.</p>

<h2>Turning it on</h2>
<p><b>Browser:</b> click anywhere on the page and type. There is no switch, because
there is nothing to switch.</p>
<p><b>Desktop:</b> the titlebar carries a <b>Global Capture</b> toggle with a badge
beside it. The badge reads <b>Window only</b> until you flip it, then <b>Global</b>.
If it reads <b>Hook unavailable</b>, the native key hook did not load and only the
Key-J window will be heard &mdash; on Linux that usually means the app needs
permission to read input devices, on Windows that a security tool blocked it.</p>
<p>Closing the window does not quit the desktop app. It keeps running in the tray so
your keys keep playing. Quit from the tray menu.</p>

<h2>The three tools</h2>
<p>The centre of the window is tabbed, and one tool shows at a time. That is
deliberate: stacked, the three of them made the page four thousand pixels tall.</p>
<table class="facts">
<tr><th>Keyboard</th><td>Sixty-one keys, C2 to C7. Click them to hear them, or turn on
<b>Build</b> and click a run in.</td></tr>
<tr><th>Grid</th><td>A step grid with nine kits, drums among them. Draw a pattern, then
<b>Use as sequence</b>.</td></tr>
<tr><th>Tab &amp; Sequence</th><td>Paste guitar tablature, or type note names. This is
where a song gets in.</td></tr>
</table>

<h2>Sequence mode, which is the part people miss</h2>
<p>Normally each key holds a fixed pitch: Q is one note, W is the next. That is fine
for noise and useless for a song.</p>
<p><b>With a sequence loaded, every key plays the next note of it.</b> Which key you
press stops mattering. You are no longer playing pitches, you are playing
<em>rhythm</em>, and the melody is already handled. That is how typing an email
produces a solo.</p>
<p>The status line shows how many notes are loaded, where you are in them and what
comes next. <b>Restart</b> returns to the first note. <b>Sequence OFF</b> puts the
fixed bindings back.</p>

<h2>Getting a song in</h2>
<p><b>From tablature.</b> Paste it in, pick the tuning, set a capo if there is one,
press <b>Convert</b>. Eight tunings including drop D, E flat, DADGAD, seven string
and bass.</p>
<p>The importer states what it read: the tuning it used, how many strings it found,
how many notes it produced, and the name of anything it could not read. A block with
the wrong number of lines produces no notes and says so rather than guessing, because
a wrong note you cannot see is worse than a missing one you can.</p>
<p>What it cannot catch is a tab that is internally consistent and simply wrong. Bad
frets convert cleanly into bad notes, and nothing but your ear will find that.</p>
<p><b>From note names.</b> Type or paste them into the note box:
<code>E5 G5 B5 E6</code>. Sharps and flats both work.</p>
<p><b>From a file.</b> <b>Load .txt</b> takes a saved sequence, or any list of note
names. <b>Import MIDI</b> takes a MIDI file and uses its note order.</p>
<p><b>From the keyboard or the grid.</b> Click a run in, then <b>Use as sequence</b>.</p>

<h2>Saving what you built</h2>
<table class="facts">
<tr><th>Save .txt</th><td>The sequence as note names. The file pastes straight back
into the note box, so saving and loading are one format.</td></tr>
<tr><th>Export WAV</th><td>The sequence rendered one note per beat at the BPM you set,
through the tone you chose.</td></tr>
<tr><th>Export Session</th><td>A recording of what you actually typed, with your
timing. A different thing, and rarely the one you want.</td></tr>
</table>
<p>Export WAV renders the <em>sequence</em>. Export Session renders <em>your typing</em>.
If you imported a tab and want to hear the song, you want Export WAV.</p>

<h2>Updates</h2>
<p>Key-J does not check for updates on its own, and that is deliberate: it makes
no network requests at all, which is a promise worth more than the convenience.
The tray menu has <b>Check for updates</b>, which opens the releases page in your
browser when you ask it to.</p>

<h2>Sound</h2>
<p>Seven tone presets, four waveforms, and sliders for attack, release, volume, reverb
and pitch. Six play styles: normal, staccato, vibrato, tremolo, arpeggio, legato. The
tone you have set is the tone the WAV export uses.</p>

<h2>The staff</h2>
<p>Notes land on a treble staff as you play, scrolling to keep the newest in view.
Key-J spans C2 to C7, which no single treble staff shows at a readable size, so a note
outside the drawable range is pinned to the edge in orange with an arrow pointing the
way it went and its name beside it. A note that will not fit is reported, not dropped.</p>

<h2>When something is wrong</h2>
<table class="facts">
<tr><th>No sound at all</th><td>Browsers will not start audio until you interact with
the page. Click the page, then type.</td></tr>
<tr><th>Nothing plays outside the window</th><td>You are in the browser version, or
Global Capture is off. Check the badge in the header.</td></tr>
<tr><th>Every key plays the same run</th><td>Sequence mode is on, and that is what it
does. Press <b>Sequence OFF</b> for fixed pitches.</td></tr>
<tr><th>Notes cut off sharply</th><td>Release is low. Raise the Release slider, or pick
a tone with a longer tail such as Bell or Pad.</td></tr>
<tr><th>The tab imported nothing</th><td>The status line names what it skipped. Most
often the block has a different number of string lines than the tuning expects.</td></tr>
<tr><th>Two Key-J entries in Add/Remove Programs</th><td>Only if you installed
1.4.0. That build carried a different application identifier, which Windows uses
to recognise an upgrade, so anything newer installs beside it rather than over
it. Uninstall both, then install the current version once. Nothing installed
from 1.4.1 onward does this.</td></tr>
<tr><th>The installer says it cannot continue</th><td>Key-J is running. Close it
&mdash; including from the tray &mdash; and install again. It stops rather than
replacing the files it can reach and leaving the ones Windows has open, which
would give you half of each version.</td></tr>
</table>

<h2>What it can see</h2>
<p>With Global Capture on, Key-J receives a signal each time any key is pressed
anywhere. It holds which key is currently down so it can release the note, and
discards it. Nothing is written to disk, nothing is sent anywhere, and the
switch starts off every time the app launches. The
<a href="/keyj/privacy/">privacy page</a> says all of this in detail, including
how to check it rather than believe it.</p>

<h2>The key map</h2>
<p>The left rail lists every key and the note it plays, and <b>clicking a row rebinds
it</b>. Scale and octave sit underneath: pick a scale and the whole keyboard is
constrained to it, which makes playing something that sounds wrong difficult.</p>
"""


# Key-J installs a global keyboard hook. A product that does that owes
# its buyer a plain account of what it does with what it sees, and every
# app store requires one before it will list it.
KEYJ_PRIVACY = """
<h2>The short version</h2>
<p>Key-J does not collect anything. No account, no telemetry, no analytics, no
crash reports, no network calls of any kind while it runs. Nothing you type is
stored, and nothing leaves your machine.</p>
<p>That is worth stating in detail rather than in a sentence, because Key-J
installs a global keyboard hook, and you should not have to take that on
trust.</p>

<h2>What the desktop application can see</h2>
<p>With <b>Global Capture</b> switched on, Key-J receives a signal from the
operating system each time any key is pressed or released, in any application.
That is what makes it play while you type elsewhere, and there is no version of
that feature which sees less.</p>
<p>What it does with that signal is the part that matters:</p>
<table class="facts">
<tr><th>Held in memory</th><td>Which key is currently down, so the note can be
released when you let go. Discarded immediately after.</td></tr>
<tr><th>Written to disk</th><td>Nothing. No log, no history, no buffer of
keystrokes.</td></tr>
<tr><th>Sent anywhere</th><td>Nothing. The application makes no outbound network
requests.</td></tr>
</table>
<p><b>Global Capture starts switched off</b> every time the application launches,
and the header shows which state it is in: <b>Window only</b> or <b>Global</b>.
It is never enabled without you enabling it.</p>

<h2>Sequence mode does not need to know what you typed</h2>
<p>When a sequence is loaded, every key plays the next note of it, so which key
you pressed stops being information Key-J needs. The command line player takes
this further and never reads the key identity at all &mdash; it asks whether a
key went down and discards the rest. There is no keystroke buffer in it to
leak, subpoena or lose.</p>

<h2>What the browser version can see</h2>
<p>Only what you type into its own page. A web page cannot read keystrokes
outside itself; that is a boundary enforced by the browser, not a promise made
by us. Sequences and settings are kept in your browser's local storage on your
own machine.</p>

<h2>Files Key-J writes</h2>
<table class="facts">
<tr><th>Settings</th><td>Your tone, tuning and last-used tab, in the standard
per-user application data directory.</td></tr>
<tr><th>Exports</th><td>Only where you choose to save them.</td></tr>
</table>
<p>Uninstalling removes the application. Anything you exported is yours and stays
where you put it.</p>

<h2>Verifying this rather than believing it</h2>
<p>The Key-J source is published. It is not free to copy &mdash; see
<a href="https://github.com/zengineco/f-keys/blob/main/keyj/LICENSE">the
licence</a> &mdash; but it is readable precisely so that a program which installs
a keyboard hook can be audited by the people running it. The global hook lives in
<code>keyj/desktop/src/main.js</code>; the handler is a few lines long and you can
read every one of them.</p>
<p>You can also check from the outside: run Key-J with any network monitor and
watch it make no requests.</p>

<h2>Children</h2>
<p>Key-J is not directed at children under 13 and collects no information from
anyone, of any age.</p>

<h2>Changes and contact</h2>
<p>If this ever stops being true, this page changes before the behaviour does.
Questions: <a href="mailto:vincegonzalez@me.com">vincegonzalez@me.com</a>.</p>
<p class="sub">F-Keys Creative LLC &middot; last reviewed 20 August 2026</p>
"""

def tree(active_cat=None, active_slug=None):
    out = ['<ul>', '<li><a class="root" href="/"><span class="ic">&#128421;</span>F-Keys</a>',
           '<ul class="kids">']
    for cid, label, _ in CATEGORIES:
        items = [c for c in CATALOGUE if c[2] == cid]
        on = " on" if (active_cat == cid and not active_slug) else ""
        out.append(f'<li><a class="{("on" if on else "")}" href="/{cid}.html">'
                   f'<span class="ic">&#128193;</span>{esc(label)}</a>')
        if active_cat == cid:
            out.append('<ul class="kids">')
            for slug, name, _c, _t, _s, _d, href in items:
                sel = " on" if slug == active_slug else ""
                out.append(f'<li><a class="{sel.strip()}" href="{esc(href)}">'
                           f'<span class="ic">&#128196;</span>{esc(name)}</a></li>')
            out.append('</ul>')
        out.append('</li>')
    for href, label in EXTRA_NODES:
        out.append(f'<li><a href="{esc(href)}"><span class="ic">&#128220;</span>{esc(label)}</a></li>')
    out.append('</ul></li></ul>')
    return "\n".join(out)


def shell(title, path_label, body, count_label, active_cat=None,
          active_slug=None, description="", canonical=""):
    up = "/" if active_cat is None else f"/{active_cat}.html"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ''}
<meta name="robots" content="index, follow">
<meta name="llms-txt" content="https://f-keys.com/llms.txt">
<meta name="ai" content="allow">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="/win98.css">
</head>
<body>
<div class="window raised">

  <div class="titlebar">
    <span class="t"><span>{esc(path_label)}</span></span>
    <span class="tbtns"><span class="tbtn">_</span><span class="tbtn">&#9723;</span><span class="tbtn">&#10005;</span></span>
  </div>

  <nav class="menubar">
    <a href="/"><u>F</u>ile</a><a href="/status/"><u>V</u>iew</a>
    <a href="/log/"><u>G</u>o</a><a href="/papers/">F<u>a</u>vorites</a>
    <a href="/about.html"><u>H</u>elp</a>
  </nav>

  <div class="toolbar groove">
    <a class="tool" href="{esc(up)}">&#8592; Back</a>
    <span class="tool off">Forward &#8594;</span>
    <a class="tool" href="{esc(up)}">&#8593; Up</a>
    <span class="sep"></span>
    <a class="tool" href="/">Home</a>
    <a class="tool hide-xs" href="/status/">Status</a>
    <a class="tool hide-xs" href="/log/">Log</a>
  </div>

  <div class="addressbar">
    <span class="lbl">Address</span>
    <span class="path sunken"><span>&#128193; {esc(path_label)}</span></span>
  </div>

  <div class="panes">
    <aside class="tree sunken">
{tree(active_cat, active_slug)}
    </aside>
    <section class="content sunken">
{body}
    </section>
  </div>

  <div class="statusbar">
    <span class="cell groove">{esc(count_label)}</span>
    <span class="cell groove grow"><a href="/log/">Log</a> &nbsp;&middot;&nbsp; <a href="/status/">Status</a></span>
    <span class="cell groove">F-Keys</span>
  </div>

</div>
</body>
</html>
"""


def details_table(rows):
    out = ['<table class="details"><thead><tr>',
           '<th class="col-name">Name</th><th class="col-type">Type</th>',
           '<th class="col-status">Status</th><th>Description</th>',
           '</tr></thead><tbody>']
    for slug, name, cat, typ, (stext, scls), blurb, href in rows:
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        out.append(
            f'<tr><td><a class="row-name" href="{esc(href)}"{ext}>'
            f'<span class="ic">&#128196;</span>{esc(name)}</a></td>'
            f'<td class="col-type muted">{esc(typ)}</td>'
            f'<td class="col-status"><span class="st {scls}">{esc(stext)}</span></td>'
            f'<td class="muted">{esc(blurb)}</td></tr>')
    out.append('</tbody></table>')
    return "\n".join(out)


def main():
    written = []

    # index: everything, grouped by category heading rows
    body = [details_table(CATALOGUE)]
    written.append(("index.html", shell(
        "F-Keys — Hardware. Software. Ideas Brought to Life.",
        "F-Keys", "\n".join(body), f"{len(CATALOGUE)} object(s)",
        description="Independent hardware, software and internet products built by "
                    "Vincent Gonzalez. Apps, games, tools, hardware and research.",
        canonical="https://f-keys.com")))

    # one page per category
    for cid, label, hint in CATEGORIES:
        rows = [c for c in CATALOGUE if c[2] == cid]
        body = (f'<div class="doc" style="padding-bottom:6px"><h1>{esc(label)}</h1>'
                f'<p class="sub">{esc(hint)}</p></div>' + details_table(rows))
        written.append((f"{cid}.html", shell(
            f"{label} — F-Keys", f"F-Keys\\{label}", body,
            f"{len(rows)} object(s)", active_cat=cid,
            description=hint, canonical=f"https://f-keys.com/{cid}.html")))


    written.append(("about.html", shell(
        "About \u2014 F-Keys", "F-Keys\\About", ABOUT_DOC, "1 item",
        description="F-Keys is Vince Gonzalez, working alone. Twenty-two live "
                    "products and more than thirty deposited works.",
        canonical="https://f-keys.com/about.html")))

    # one document per product that has long-form detail
    for slug, page in PAGES.items():
        row = next((c for c in CATALOGUE if c[0] == slug), None)
        cat = row[2] if row else None
        facts = "".join(
            "<tr><th>{}</th><td>{}</td></tr>".format(esc(k), esc(v))
            for k, v in page["facts"])
        doc = ('<div class="doc"><h1>{}</h1><p class="sub">{}</p>'
               '<table class="facts">{}</table>{}</div>').format(
                   esc(page["title"]), esc(page["tagline"]), facts, page["body"])
        label = dict((c[0], c[1]) for c in CATEGORIES) if False else None
        catname = next((c[1] for c in CATEGORIES if c[0] == cat), "")
        written.append((os.path.join(slug, "index.html"), shell(
            page["title"] + " \u2014 F-Keys",
            "F-Keys\\{}\\{}".format(catname, page["title"]),
            doc, "1 item", active_cat=cat, active_slug=slug,
            description=page["tagline"],
            canonical="https://f-keys.com/{}/".format(slug))))

    written.append((os.path.join("keyj", "privacy", "index.html"), shell(
        "Key-J Privacy \u2014 F-Keys",
        "F-Keys\\Apps\\Key-J\\Privacy",
        '<div class="doc"><h1>Key-J Privacy</h1>'
        '<p class="sub">What a program with a global keyboard hook does '
        'with what it can see.</p>' + KEYJ_PRIVACY +
        '<div class="btnrow"><a class="btn default" href="/keyj/">Key-J</a>'
        '<a class="btn" href="/keyj/manual/">Manual</a></div></div>',
        "1 item", active_cat="apps", active_slug="keyj",
        description="Key-J collects nothing. What the global keyboard hook "
                    "sees, what is kept, and how to verify it.",
        canonical="https://f-keys.com/keyj/privacy/")))

    # the manual, one level under the Key-J document
    written.append((os.path.join("keyj", "manual", "index.html"), shell(
        "Key-J Manual \u2014 F-Keys",
        "F-Keys\\Apps\\Key-J\\Manual",
        '<div class="doc"><h1>Key-J Manual</h1>'
        '<p class="sub">What it does, how to switch it on, and what to check '
        'when it does not.</p>' + KEYJ_MANUAL +
        '<div class="btnrow"><a class="btn default" href="/keyj/app.html">'
        'Open Key-J</a><a class="btn" href="/keyj/">Product page</a></div></div>',
        "1 item", active_cat="apps", active_slug="keyj",
        description="How to use Key-J: sequence mode, tablature import, global "
                    "capture, and what to check when something is not working.",
        canonical="https://f-keys.com/keyj/manual/")))

    for name, content in written:
        target = os.path.join(ROOT, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"buildsite: {len(written)} pages")
    for n, _ in written:
        print("  ", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
