# F-Keys log

Newest entry at the top. To add one, copy the date line format and write
underneath it. Blank line between paragraphs. `**bold**`, `` `code` `` and
[links](https://f-keys.com) work; nothing else is needed.

CI renders this into `log/index.html` on push. Do not edit that file by hand.

## 2026-09-24

Rewrote the site's wording and gave it a way in.

`/search/` is the whole catalogue in one table, filtered in the browser as
you type — products, papers, records, the CVs. It is rendered at build time,
so with scripting switched off it is still the complete index. Find sits in
the toolbar and the tree, and the sitemap picked up the eleven pages it had
never been told about: the four CVs, the intake pages, the log, the status
page, and TAG and TAG PRO.

The wording is a field register now. The homepage is forty-one words and a
table. Counts live in the About facts table, where a number is a number; the
build fails if one of them stops matching the catalogue. Contact is the
filing details and four short headings.

Wrote the rules into the gate afterwards, so the register holds without
anyone remembering it.

## 2026-09-15

Built the backend for the intake form. A worker at `orders.f-keys.com` with
D1 behind it, two tables.

The order of operations is the design: validate, write the row, try to
notify, answer the browser. Only the third step is allowed to fail, so a mail
problem costs a notification and never the enquiry, and the response reports
`recorded` and `notified` as two separate facts. Files are recorded by name
and size rather than stored — a 4 MB logo base64s past the row cap, and a
failed write there would take the whole intake down with it. The visitor IP
is kept as a salted hash: the table is evidence of what was agreed and when,
not a list of people's addresses.

Also wrote a gate that scores prose for the patterns a language model leaves
behind — the fingerprint words, the sentence shapes, and the house rules
about this site's voice. It reads the visible text only, so a word that appears
in a variable name is not mistaken for writing.

It found three things. The markdown mirrors had never been regenerated after
August's voice pass, so the retired version was the one `llms.txt` was
pointing crawlers at. Twenty-eight pages were printing the source code of an
em dash instead of an em dash, TAG's first line among them. And the intake
pages were loading two typefaces from Google — the one place that takes a
name, an email and a signature was the one place reporting its readers to a
third party, against a privacy page that promises otherwise. Both typefaces
are open-licensed, so they are served from here now.

The same gate found the same escaping bug on 5best2buy, on twenty pages. One
of those was costing money: an affiliate URL escaped twice arrived with its
parameters renamed, so the id never transmitted.

## 2026-09-14

Rebuilt how the intake form reports a submission.

It now shows the confirmation screen for a delivery that actually happened,
and nothing else. When the send fails the whole intake goes on screen in a
box to copy, with a short mail link beside it, so the answers are never lost
to a transport problem.

It needed rebuilding. With no endpoint configured the form fell back to
handing the intake to the visitor's mail app, and that hand-off was about
five thousand characters against a Windows limit of roughly two thousand —
so it arrived cut in half, or not at all, and the success screen appeared
regardless because it fired on a timer instead of on a delivery.

## 2026-09-11

Published the website offer at `/intake/`. A hundred dollars to build a site,
seventy-five a month to run it, and `intake.f-keys.com` routed to it like
every other product name.

The form behind it is ten sections: the business, its brand, its hours and
service area, what it sells, how it takes bookings, what it wants found for,
and a menu of forty-seven add-ons priced in plain numbers rather than tiers
that mean nothing. The service agreement is inside the form, so the terms are
read before anything is signed rather than arriving later on an invoice.
Submitting it is a quote request: it does not start work and it does not
charge anybody, and clause one says so.

## 2026-09-10

A build day on OpticQuiz.

Added the seventeenth test — stereo depth, by random-dot stereogram — and a
methodology page that answers eight questions about how the engine works,
what it is calibrated against, and where it stops being reliable.

Gave the site one set of chrome. Until now sixty-seven pages each redeclared
their own styles, the navigation used anchors that only worked on the
homepage, and thirty pages carried a footer with no links in it at all. There
is one stylesheet now, one canonical nav with real links, and one footer
carrying twenty internal links in four groups, stamped across all seventy-one
pages along with a 404 and thirty-three redirect stubs for addresses that had
moved.

The colour audit went into that footer. It had been reachable from one page
out of sixty-eight, which meant the path from a test result to the thing that
costs money was invisible from everywhere else — including the page that
receives the most traffic. Never a demand problem. Nobody had been asked.

Rewrote this site in first person the same day, after someone told me it read
like a machine. They were right.

## 2026-09-08

TAG and TAG PRO are published on Fortnite.

Two islands, not one game at two settings. TAG is close quarters and blind
corners, where you duck to slip a tag and the room does the work. TAG PRO is
an open arena where a lunge and a dash decide it, and the edge tags you if
you dash over it. Both run ninety-second rounds and both carry a title
ladder.

TAG is **8134-9047-4850**. TAG PRO is **5571-1708-8987** — the first code I
published for it was wrong, so if you saved one early, that is the one to
use.

Deposited two more axiom papers: Mathlib's reach into choice, unbundled; and
discretionary-axiom reach shown not to be comparable across proof systems.
The collector had been counting both for a while. The register had not been
listing them.

## 2026-08-20

Spent the day taking Key-J apart. It had shipped, it was live, and it was
close to unusable, which I already knew and had said out loud.

The count of things wrong with it is the part worth writing down. Selecting
Vibrato killed the app, because one line starting an oscillator was
duplicated and the exception left every key pressed under it permanently
dead. Export produced one audible second out of thirty-five, because the
session held every note typed before Record at time zero and normalisation
then scaled the rest into silence. Release was declared in seconds where
everything reading it expected milliseconds, so notes clicked off until you
touched the slider, and every tone preset quietly undid it again. Notes were
plotted five staff positions too high, so the whole top octave was drawn off
the top of the picture. And global capture — the entire reason a desktop
build exists — had never once played the right note: the keycode table was
written in macOS codes for a library that emits its own, and of twenty-four
letter mappings, zero were correct.

Most of those came from the same place. The browser build and the desktop
build were two separate implementations of the same product, so a fix to one
never touched the other and nobody noticed the drift. There is one renderer
now, and the desktop copy is generated from it with a check that fails the
build if they diverge.

Then it went out: installers for Windows and Linux, `pip install keyj` on
PyPI, and a winget manifest submitted. Two things nearly went out wrong. The
Windows app identifier was still a personal handle from before any of this
was a company, which Windows writes into the uninstall registry and which
every future installer has to match — changed with an hour to spare and no
downloads on the clock. And installing silently over a running copy exited
zero while leaving half the old version on disk, which is precisely what a
package manager does by default.

The thing I keep circling is that I measured everything I could measure and
missed what anyone sees first. The app shipped through four versions with the
default Electron icon, and PlumHUD has been looking for its logo down a
relative path since the day it was released, so the plum has never once
appeared. Both are fixed. Neither was hard. They were just never checked,
because checking them was nobody's idea of rigour.

Key-J is proprietary from 1.6.0. MIT was never a decision I made; it was
inherited from the top of the repository and then copied outward. The source
stays readable, because a program that installs a global keyboard hook should
be auditable by whoever runs it. Readable and free to resell are different
things, and now the licence says which one this is.

## 2026-08-19

Filed the LLC, though not under the name I wanted. An unrelated F Key LLC has
been active in Florida since 2021, which meant F-Keys LLC wasn't distinguishable
on the record and July's filing was refused. Re-filed as **F-Keys Creative LLC**
at no cost.

Spent a while convinced this meant redoing a month of branding, before working
out that a registered entity name and a trading name are separate things. The
brand is unchanged. The filing cabinet just has a longer label on it.

The snapshot ran on its own for the first time overnight — 464 package installs
for the week, up seven from the day before.

## 2026-08-18

Built a daily snapshot, because the numbers were arriving in six places I never
looked at. The first run reported 457 package installs a week across six
packages, and 35 papers with 859 views and 359 downloads. I would have guessed
lower on every one of those. `@f-keys/tip-widget` on its own is 289 a week,
which is 289 more than I thought it was.

Swept the dissolved company name out of everything a person reads — 65
occurrences across twelve files. Most of it was cosmetic. Two things were not.
FunDoge's terms and privacy pages still named the dissolved entity as the data
controller, the IP owner, the party shielded by the limitation of liability, and
the indemnitee. A liability clause protecting a company that no longer exists
protects nobody. And WikiPolish was stamping a dead domain into the edit summary
of every Wikipedia edit made through it, which would have written it into a
permanent public record every time the tool worked. Checked the account history
first — it had never actually fired. Caught it before it wrote anything.

Found two forgotten repositories still publishing the retired version of
DogeFundMe, both displaying live wallet addresses and asking people to send to
them. Turned their pages off.

Put a check into CI so the old name can't quietly return. It removes the allowed
identifiers from a line first and only then looks for the brand word, because
the GitHub org and a classifier named in a published paper both have to survive.
A blanket find-and-replace would have broken working links on eight pages.

## 2026-08-17

Rebuilt f-keys.com. The old page was one undifferentiated grid, and the version
before it, on the old domain, had 23 cards of which 17 pointed at nothing. It's
six sections now — apps, games, tools, hardware, research, properties — and
every card carries a status badge, so something in alpha can be visible and
honest at the same time rather than hidden or oversold.

Recovering Key-J turned into a rescue. Its Electron entry point was gone from the
working folder and survived in exactly one zip, inside a directory named "zip to
sort". The entire desktop app depended on that file. It lives in a repository
now, along with the browser build.

Pointed the old company domain at f-keys.com. One redirect, no DNS records
touched, email left intact.
