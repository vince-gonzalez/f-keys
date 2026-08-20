# F-Keys log

Newest entry at the top. To add one, copy the date line format and write
underneath it. Blank line between paragraphs. `**bold**`, `` `code` `` and
[links](https://f-keys.com) work; nothing else is needed.

CI renders this into `log/index.html` on push. Do not edit that file by hand.

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
