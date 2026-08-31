# changewatch

> A doorbell, not a dashboard.

Canonical: https://f-keys.com/changewatch/

You can already see what you did. What you cannot see is whether anyone else did anything about it &mdash; the first citation, the first star from a stranger, the first time your name appears somewhere you did not put it.

pip install changewatch · MIT · silent unless somebody else acts

## What it does

You can already see what you did. What you cannot see is whether anyone else
did anything about it — the first citation, the first star from a
stranger, the first time your name appears somewhere you did not put it.

**pip install changewatch**
changewatch init
changewatch check
Almost every run says nothing happened and exits. That is the design.

## Why it only reports other people

The first ORCID this was pointed at reported six citations. All six were the
author citing himself, doubled because Zenodo mints a DOI per version. Six is a
number that feels like an audience; the real figure was zero.

A tool that cannot tell your own activity from a stranger's rings on your own
deposits, gets muted inside a week, and is then silent on the day something real
happens. So every source checks your ORCID, your names and your logins.

## It does not trust the search engine

Asked for the exact phrase "openapi-drift", Hacker News returned
a five-month-old thread titled “How do you catch OpenAPI drift before the
UI breaks?” — two words, and not about anybody's package. Every hit
is checked against the text locally, because a search engine's idea of a phrase
is not yours.

## The first run is silent

It has nothing to compare against, so everything looks new. A doorbell that
announces months of history the moment it is plugged in gets unplugged. The
first run learns; the second one rings.

## How it works

## What it watches, and what it refuses to do

## Specifications

| Field | Value |
| --- | --- |
| Install | pip install changewatch |
| Licence | MIT |
| Needs | GITHUB_TOKEN for the GitHub half |
| Source | vince-gonzalez/changewatch |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
