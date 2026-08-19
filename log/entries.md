# F-Keys log

Newest entry at the top. To add one, copy the date line format and write
underneath it. Blank line between paragraphs. `**bold**`, `` `code` `` and
[links](https://f-keys.com) work; nothing else is needed.

CI renders this into `log/index.html` on push. Do not edit that file by hand.

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
