# Privacy

> No advertising, no analytics, no cookies and no accounts. What the servers log anyway, and the one third-party request.

Canonical: https://f-keys.com/privacy.html

Every page here takes nothing, except one that has to. This
describes both.

## The short version

| Field | Value |
| --- | --- |
| Advertising | None. No ad network, no ad tags, no affiliate tracking. |
| Analytics | None. No Google Analytics, no tag manager, no pixel, and no first-party analytics script of any kind. |
| Cookies | None. This site sets no cookies, so there is no consent banner to dismiss. |
| Accounts | None. Nothing on f-keys.com asks you to sign up or sign in. |
| Third-party code | None. No page on this site loads anything from another company's server — not a script, not a stylesheet, not a font. |
| Forms | One. The [website intake form](https://f-keys.com/intake/form/) collects what you type into it, because it cannot do its job otherwise. Every other page on this site collects nothing. [What that one does with it](https://f-keys.com#intake). |

These are checkable rather than promised. The site is a folder of static files
in a public repository, and a test in that repository fails the build if an ad
tag, a tracking script or a cookie write appears anywhere in it.

## What the servers see anyway

The pages are served by GitHub Pages through Cloudflare. Both keep ordinary
web-server logs, which means your IP address, the page you asked for, your
browser's user-agent string and the time are recorded by those companies as a
side effect of the request being delivered at all. F-Keys does not receive those
logs and does not know who visited.

It does read one thing: Cloudflare's aggregate counts for its own zones
— page views, unique visitors, and threats blocked, per site, per day.
That is where the numbers on the [status page](https://f-keys.com/status/) come from.
It is a daily total and nothing else. It is not tied to a person, it cannot be,
and no script on this page produces it — the count is made by Cloudflare
while delivering the request, and read afterwards through their API.

Their handling is
governed by
[GitHub's privacy statement](https://docs.github.com/site-policy/privacy-policies/github-privacy-statement)
and
[Cloudflare's privacy policy](https://www.cloudflare.com/privacypolicy/).

## The fonts are ours too

The [Docs](https://f-keys.com/Docs.html) page used to load two typefaces from Google
Fonts. A font request looks harmless and is not: it reports the IP address of
everyone who opens the page, on every visit, to a company whose business is
knowing things about people. Both faces are under the SIL Open Font License,
which permits hosting them, so they are served from this domain and that request
no longer leaves. Nothing else on this site loads from a third party either.

## The products are not this site

Several products store their settings in your own browser or on your own
machine, where they never leave it and are not visible here. Where a product does
more than that it carries its own privacy document, and the strongest claims are
tested rather than asserted — [Key-J](https://f-keys.com/keyj/privacy/) installs a
system-wide keyboard hook, so its page describes exactly what that hook can see,
and a test in the repository asserts that the function a keypress calls cannot
retain a key. Products hosted elsewhere, and the separate
[properties](https://f-keys.com/properties.html), are governed by their own policies
rather than this one.

## The one form that does collect

[f-keys.com/intake/form/](https://f-keys.com/intake/form/) is a quote request for
website work. Filling it in is the only way to hand this site personal
information, and it is optional in the ordinary sense: nobody reaches it by
accident, and leaving the page loses everything typed.

**What it takes.** Your business name, your name, your email
address, your phone number, your business address and hours, what you sell and
what you charge for it, your domain, and whatever else you choose to type into
the notes. If you attach a logo or photographs, it takes those too. It also
records the date and time, the country the request came from, and a
**salted hash** of the IP address — a fingerprint of the
address rather than the address, kept because a form that is also a signature
has to be able to say where it was signed.

**Where it goes.** Straight to a Cloudflare Worker on
orders.f-keys.com, into a Cloudflare D1 database, with any files into a private
Cloudflare R2 bucket. The bucket is not public and nothing in it is readable by
a URL anyone could guess. A notification email is then sent through
[Resend](https://resend.com/legal/privacy-policy), which carries your
answers so that the enquiry lands in an inbox. Resend and Cloudflare are the
only two companies that see it. It is not sold, it is not shared with anyone
else, and it is not used to advertise anything to you.

**How long it stays.** Until you ask for it to go. There is no
automatic deletion, because a quote request is the record of what was agreed and
throwing it away on a timer would serve nobody. Ask and it is deleted, both the
row and any files, and that is the whole procedure.

**What it does not do.** It sets no cookie. It writes nothing to
your browser's storage. It creates no account, builds no profile, and adds you to
no mailing list — there is no mailing list. Submitting it does not sign you
up for anything.

## Your rights, and how little there is to exercise them on

Rights of access, correction, deletion and portability under the GDPR, the
CCPA and similar laws attach to personal data held by the operator. Browsing
these pages hands over nothing for those rights to attach to: no mailing list is
gathered here and no profile of you is built. If you have sent the intake form,
the answers you sent are yours — ask and you get a copy, a correction, or
deletion, and asking is enough. There is no form to fill in and no identity to
prove beyond replying from the address you used. If you send an email it exists
in a mailbox until you ask for it to be deleted. This site is not directed at
children, and the intake form is a business-to-business document.

Questions, or a challenge to any claim above, go to
[hello@f-keys.com](mailto:hello@f-keys.com). If a claim here
ever stops being true, the page changes first and the change is dated in the
[working log](https://f-keys.com/log/).

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
