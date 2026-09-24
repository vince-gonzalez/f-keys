# F-Keys log

Newest entry at the top. To add one, copy the date line format and write
underneath it. Blank line between paragraphs. `**bold**`, `` `code` `` and
[links](https://f-keys.com) work; nothing else is needed.

CI renders this into `log/index.html` on push. Do not edit that file by hand.

## 2026-09-24

Rewrote the wording across the site. The homepage was 958 words that
explained the company to the reader: a claim about how much of the work was
mine, the story of a zip file, and 130 words headed "Who it is for" listing
customer types in bold. It is 41 words now. The table was always the content.

About recited the deposit count, the weekly install figure and the number of
merged pull requests. Developers opened with "four command-line tools,
sixteen PyPI packages, nineteen on npm" — and sixteen had been wrong for
weeks. A number written to impress is a number nobody maintains. The live
count sits in the About facts table now, where a number is just a number, and
the build fails if it disagrees with the catalogue.

Cut the tagline I added on the tenth.

The four CVs at `/cv/` were live with no link pointing at them from anywhere
on the site, no entry in the sitemap, and `/cv/` itself returning 404. There
was no search. A recruiter landing on the front page could not reach a
resume by any route, and no crawler knew the pages existed. Neither did any
crawler know about TAG or TAG PRO.

`/search/` is the whole site in one table, filtered in the browser as you
type. It is rendered at build time, so with scripting off it is simply the
full index — which is the thing that was missing. The sitemap went from 166
URLs to 177.

Two errors on the operations CV worth recording. It opened with a tenure
length, which I have ruled against for my own applications and had left
standing on my own site. And it said four of those years were spent
supervising, which is wrong: that began in May 2023. It states dates now.

## 2026-09-15

The intake form has a backend. It writes to a database before it tries to
send mail, so a mail failure costs a notification and never the enquiry, and
the response reports those two things separately. Files are recorded by name
and size rather than stored — a 4 MB logo base64s past the row limit, and a
failed write there would take the whole intake down with it.

Wrote a gate that scores prose for the patterns a language model leaves
behind. It found three things on this site.

The markdown mirrors had never been regenerated after the voice pass in
August. `about.md` still opened with a claim about who does the work that I had
struck from the HTML weeks earlier — and will not repeat here, because those
mirrors are what `llms.txt` points crawlers at, and the retired version was
the one machines had been reading all month.

Twenty-eight pages were showing their own markup. TAG's first line printed
the source code of an em dash instead of an em dash, to anyone who visited,
because the description had been written with an HTML entity in it and was
then escaped a second time on the way out.

And the intake pages loaded two typefaces from Google. The one page that
takes a name, an email and a signature was the one page reporting its
readers to a third party, while the privacy page promised no page does that.
The tool that had fixed this for 61 pages already existed; the intake pages
were written after it and went around it.

Same class of bug on 5best2buy, found by the same gate: 20 pages showing
their own markup. One of them cost money. An affiliate URL had been escaped
twice, so the link arrived with its parameters named `amp;awinaffid` and
`amp;ued` — the affiliate id was not transmitted and the destination was
never read. Two links, one of them live on the tea shelf.

## 2026-09-14

The intake form had been telling people it sent when it had not.

With no endpoint configured it fell back to opening the visitor's mail app,
and the body it handed over was about five thousand characters once encoded
against a Windows limit of roughly two thousand. So the mail app opened
truncated, or did not open. Either way the success screen appeared, because
it fired on a 600-millisecond timer rather than on a delivery.

Somebody could have filled in ten sections, signed a six-clause agreement,
read "you'll hear back within 24–48 business hours", and sent nothing.

Now the success screen appears only for a delivery that happened. Everything
else puts the intake on screen in a box to copy.

## 2026-09-11

Published the website offer at `/intake/`: $100 to build, $75 a month to run
it, with the service agreement inside the form rather than deferred to an
invoice nobody has seen. Submitting is a quote request. It does not start
work and it does not charge anybody, and the agreement says so in its first
clause.

## 2026-09-10

OpticQuiz had a paid audit page reachable from exactly one page out of 68.
The route from a test result to the thing that costs money was invisible at
the second hop from everywhere else, including the page that receives the
most traffic. It is in the footer of all 69 now. That was never a demand
problem. Nobody was ever asked.

Also added the seventeenth test, a random-dot stereogram for stereo depth,
and a methodology page that answers eight questions about how the engine
works and where it stops being reliable.

Rewrote this site in first person after someone told me it read like a
machine. They were right.

## 2026-09-08

TAG and TAG PRO are published on Fortnite.

Two islands rather than one game at two settings. TAG is close quarters,
blind corners, and a duck to slip a tag. TAG PRO is an open arena where a
lunge and a dash decide it and the edge tags you if you dash over it. Both
run 90-second rounds and both carry a title ladder.

Published TAG PRO with the wrong island code and had to correct it. The
right one is **5571-1708-8987**. TAG is **8134-9047-4850**.

Deposited two more axiom papers.

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
