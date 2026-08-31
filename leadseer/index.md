# LeadSeer

> Which businesses near you have no website at all?

Canonical: https://f-keys.com/leadseer/

Answers one question: which businesses near you have no website at all. It is archived, it works, and it runs from source with your own Google Places key.

**Archived, working** · Node 18+ and Electron · needs your own Google Places API key · run from source

## What it does

Search a place and a trade — plumbers in Toledo, salons in Sarasota — and
LeadSeer asks the Google Places API for every match, then keeps only the ones whose record
has no website on it.

That absence is the whole qualification. A business with no website cannot already have
a web designer, which makes it the shortest possible answer to "who would actually take
this call". Everything else about lead lists is guessing; this is a field that is either
empty or not.

## What comes back

Name, phone, address and a Google Maps link for each result, with the ones missing a
website surfaced first. Searches are kept in a local history so you can return to a town
without paying for the same lookups twice, and the list exports to a file.

## The key is yours

LeadSeer has no server and no account. It calls Google Places with **your** API key,
stored in a local config, so the quota and the billing are yours and nothing routes through
anyone else. That is also the catch: without a key it cannot search at all.

## Archived, and honest about it

It works and it is not being developed. There has never been a packaged installer —
it runs from source with Node and Electron. The code stays readable because a tool that
answers a real question is worth keeping.

## How it works

## What it does

## Specifications

| Field | Value |
| --- | --- |
| Status | Archived, working |
| Runtime | Node 18+, Electron |
| Needs | A Google Places API key |
| Install | Run from source |
| Source | vince-gonzalez/LeadSeer |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
