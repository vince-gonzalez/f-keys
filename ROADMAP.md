# Roadmap

Everything measured on 2026-08-22, from the repositories and the live
properties rather than from memory. Each item says what is true now, so the
work can be checked off against something.

Nothing here is a guess about priority except the ordering, which is mine and
is arguable. Items marked **decision** need Vince, not code.

---

## 0. The standing rule

A product is not shipped because it runs. It is shipped when a stranger can
find it, see it, understand what it costs them, get the source, and file a bug.
By that test, 8 of 22 products are not shipped.

---

## 1. Portfolio entries — 10 products have no page at all

f-keys.com lists 22 products. Twelve have a real page. **Ten are a table row
whose link goes straight off-site**, so the site never makes a case for them.

| Needs a page | Where it goes today |
|---|---|
| OpticQuiz | opticquiz.com |
| Trailer Load | trailer-load.com |
| PROMPT | prompt.f-keys.com |
| DaisuPop | dp.f-keys.com |
| FyteCraft | github |
| Modulign | modulign.org |
| 5Best2Buy | 5best2buy.com |
| Poticas | poticas.com |
| TipStreams | tipstreams.com |
| FunDoge | dogefundme.com |

And the twelve that do have pages are prose only:

- [ ] **9 of 10 generated product pages have zero screenshots.** Not one page
      shows the product.
- [ ] **All 22 products share one og:image.** Every product unfurls
      identically in every chat client and social card.
- [ ] No per-product changelog or release history on any page.

### What an entry contains

Screenshot or short demo · its own og card · what it is, who it is for, what
it costs · version, licence, platform, requirements · install or run in one
command · source and issues link · **a named limitation** · SoftwareApplication
schema (already done).

- [ ] Agree the template on **Key-J** first — most distributed, most exposed.
- [ ] Clone it across the other 21.

---

## 2. Repositories — 8 products have none of their own

| Product | State now | Action |
|---|---|---|
| **Key-J** | no repo; ships installers, winget, PyPI | new public repo, move `keyj/` + `keyj-cli/` |
| **PlumHUD** | archived repo; live on PyPI | unarchive or recreate, repoint `project.urls` |
| **Moonbeam** | **two live sources** — `Moonbeam-NerdMiner` unarchived *and* `f-keys/moonbeam` at 1.0.2 | pick one, redirect the other |
| **FunDoge** | **live site served from an archived repo** | unarchive; cannot ship a fix as-is |
| Pixel Staff | archived repo, code in monorepo | decide: own repo or stay |
| LeadSeer | archived repo, code in monorepo | decide |
| RemapWrap | no repo — *the company is named after it* | new public repo |
| Stream Sniper | no repo | new public repo |

- [ ] **Every PyPI package points into a monorepo subdirectory.** `keyj`,
      `plumhud`, `moonbeam-miner` all resolve to
      `github.com/zengineco/f-keys/tree/main/<dir>`. No stars, no issues, no
      releases, no watchers land anywhere.
- [ ] **4 of 21 tracked repositories have no licence** — nobody who finds them
      can legally reuse them. Now surfaced on `/status/`.
      Unlicensed: `trailer-load.com`, `Moonbeam-NerdMiner`, `fkeys`, and the
      retired `.site` repo (plus `icd`, `ionics`, `awesome-twitch` outside the
      tracked set). The live list is the "Repos without a licence" figure on
      [/status/](https://f-keys.com/status/).
- [ ] `zengineco/fkeys` (no hyphen) is a stale duplicate of the site repo.
      Archive it.

---

## 3. Icons — 1 of 22 products has one

Only RemapWrap has a mark (`icon.ico`, `logo.png`, `logo-256.png`).

- [ ] A mark per product, at 512/256/64/32 plus `.ico`.
- [ ] Generate the og card per product from the mark, the way
      `tools/ogimage.py` already does for the company card.
- [ ] Favicon per property (see §4).

---

## 4. The properties — measured 2026-08-22

| Property | Missing |
|---|---|
| tipstreams.com | favicon |
| modulign.org | favicon, **robots.txt, sitemap.xml, llms.txt** |
| dogefundme.com | favicon, JSON-LD, llms.txt |
| prompt.f-keys.com | favicon, og:image, canonical, JSON-LD, h1, robots, sitemap |
| dp.f-keys.com | favicon, og:image, canonical, JSON-LD, h1, robots, sitemap |

- [ ] **`security.txt` exists on 2 of 10 properties** (opticquiz, 5b2b only).
- [ ] **No web manifest on any of the 10.** Key-J, QV, OpticQuiz and Pixel
      Staff are installable-web-app shaped and none of them can be installed.
- [ ] **modulign.org is the academic-legitimacy play and has no robots.txt,
      no sitemap and no llms.txt at all.**
- [ ] The two Discord Activities have no landing layer — a browser visitor
      gets the game shell and search engines get nothing.

---

## 5. Documentation and house standards

- [ ] **6 product directories have no README** — `keyj`, `pixelstaff`, `qv`,
      `micdrop`, `wikipolish`, `leadseer`, against the house standard that
      every repo opens with the banner.
- [ ] `Docs.html` is capital-D at the site root. Predictable URLs matter to
      both crawlers and agents.
- [ ] No CHANGELOG anywhere; releases are invisible.

---

## 6. Agent readiness — done, and what remains

Done and live: SSR homepage, contact/privacy/404, JSON-LD, self-hosted fonts,
`llms.txt` with when-to-use, `openapi.json` with 31 inline typed schemas,
Markdown and JSON content negotiation, `/v1` prefix, developer page. Score
67 → 90 → pending rescan.

- [ ] **Brand-name search.** "F-Keys" competes with "function keys" and the
      domain does not appear. Not a markup problem — needs inbound links.
- [ ] **Developer-resource search.** `/developers.html` is new and unindexed.
      Time, plus links.
- [ ] **decision — rate limits.** There is none, and I will not publish a
      `RateLimit` header for a limit nobody enforces. The alternative is a
      real limit in the Worker (Cloudflare rate-limiting binding, e.g. 1,000
      req/min/IP), which passes the check by making the service genuinely more
      restrictive. Vince's call.

---

## 7. Infrastructure and risk

- [ ] **decision — iCloud.** `f-keys.com` mail routes through iCloud, and the
      subscription is known to be full and possibly replaced. `hello@f-keys.com`
      is now printed across the whole site. The durable fix is the Cloudflare
      Email Routing catch-all already proven on epistemend.org.
- [ ] Worker redeploy is a manual step. Two rounds of work sat undeployed
      because a push does not carry it. Consider a deploy job on the workflow.
- [ ] `typefloor` reports 72+ font sizes under the floor (RemapWrap dashboard,
      Pixel Staff piano keys). Not a CI gate. Decide whether it should be.

---

## 8. The house-ad idea

An F-Keys-branded ad unit that looks like an ad network but every impression
is a cross-promotion for another property. Cheap now that the AdSense slot
markup is gone from Docs. Eligibility rules apply: trailer-load / LOCK IN is
walled off from cross-promotion.

---

## Suggested order

1. **Key-J end to end** — repo, icon, screenshot, og card, full entry. It is
   the most distributed and least supported thing here, and it becomes the
   template.
2. **The cheap sitewide sweep** — favicons, manifests, `security.txt`,
   modulign.org's robots/sitemap/llms. Hours, not days, and it closes a whole
   column of the table above.
3. **Repos and licences** — the four unlicensed, the two Moonbeams, the
   archived repo serving a live site.
4. **The other 21 product entries**, template first.
