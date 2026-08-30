# Privacy

> No advertising, no analytics, no cookies and no accounts. What the servers log anyway, and the one third-party request.

Canonical: https://f-keys.com/privacy.html

This site does not want your data, and the shortest way to say so
is to describe every byte it does receive.

## The short version

| Field | Value |
| --- | --- |
| Advertising | None. No ad network, no ad tags, no affiliate tracking. |
| Analytics | None. No Google Analytics, no tag manager, no pixel, and no first-party analytics script of any kind. |
| Cookies | None. This site sets no cookies, so there is no consent banner to dismiss. |
| Accounts | None. Nothing on f-keys.com asks you to sign up or sign in. |
| Third-party code | None. No page on this site loads anything from another company's server — not a script, not a stylesheet, not a font. |

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

## Your rights, and how little there is to exercise them on

Rights of access, correction, deletion and portability under the GDPR, the
CCPA and similar laws attach to personal data held by the operator. F-Keys holds
none from this site: there is no database, no mailing list gathered here, and no
profile of you. If you send an email it exists in a mailbox until you ask for it
to be deleted, and asking is enough. This site is not directed at children and
collects nothing from anyone, of any age.

Questions, or a challenge to any claim above, go to
[hello@f-keys.com](mailto:hello@f-keys.com). If a claim here
ever stops being true, the page changes first and the change is dated in the
[working log](https://f-keys.com/log/).

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
