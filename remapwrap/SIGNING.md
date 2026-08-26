# Signing RemapWrap

**DRAFT — the account does not exist yet. This is the checklist for creating
it, written from Microsoft's current documentation rather than from memory,
because the rules changed twice in three years.**

---

## The decision, and a correction

Earlier advice in this project said to budget an **EV certificate**. That is
out of date, and Microsoft now says so directly:

> EV certificates no longer bypass SmartScreen. […] Paying a premium for EV
> solely to avoid SmartScreen warnings is no longer justified.
> — [SmartScreen reputation for Windows app developers](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)

So the recommendation is **Azure Artifact Signing** (called Trusted Signing
until the 2026 rename), which is Microsoft's own recommended option for
distributing outside the Store.

| | Artifact Signing | Traditional OV | Traditional EV |
|---|---|---|---|
| Cost | **from $9.99/month** | ~$200–400/yr | ~$400+/yr |
| Hardware token | **none** | required since 2023 | required |
| SmartScreen on day one | warning | warning | **warning** |
| CI/CD | direct | token must be plugged in | token must be plugged in |

The three columns behave identically on the thing everyone buys a
certificate for. Only the price and the physical object differ.

## What signing actually buys

Be clear about this before spending anything, and before writing it on a
download page:

- **It does not remove the first-run warning.** Nothing does except
  publishing through the Microsoft Store, which re-signs with a Microsoft
  certificate and is never subject to the prompt.
- **The publisher name appears** in the dialog instead of *Unknown
  publisher*. For a program that injects keystrokes, a stranger seeing
  F-KEYS CREATIVE LLC rather than nothing is most of the decision.
- **Reputation accumulates on the certificate** and carries to the next
  release. Unsigned files start from zero every single version, forever.
- **Windows 11 Smart App Control blocks unsigned executables outright.** Not
  a warning — a block. This is the part that makes signing non-optional.

Reputation takes *weeks and hundreds of clean installs*. Plan the launch
around that rather than expecting a clean first day.

## What it will cost to be wrong about the free tier

Nothing here affects the free tier of RemapWrap. Signing is a cost of
distribution, not a feature.

## Prerequisites, from the official list

Organization validation needs an Azure subscription and a Microsoft Entra
tenant. There is **no minimum organization age** in the current
prerequisites — a claim that organizations need three years of tax history
circulates widely and traces back to an AI-generated forum answer citing a
different product's guidance. A Microsoft engineer answered the same
question with *"no minimum org age restrictions."*

Public Trust certificates are available to organizations in the US.

## The checklist

**1. Email — this is the blocker, do it first.**
Organization validation needs a **primary** and a **secondary** monitored
mailbox, both on a domain owned by the legal entity. That means two
addresses at **@f-keys.com**. They must accept mail from external senders
containing links, and the verification links expire in **seven days**.

This is the same Cloudflare Email Routing setup already done for
epistemend.org.

- [ ] `something@f-keys.com` — primary, monitored
- [ ] `something-else@f-keys.com` — secondary, different address, same domain

**2. Azure account, with the name exactly right.**
The billing account's legal name and address must match what should appear
on the certificate. A mismatch puts wrong information on the certificate and
requires starting over.

- [ ] Azure subscription
- [ ] Billing account type set to **Organization**, not Individual
- [ ] Legal name on the billing account: **F-KEYS CREATIVE LLC**

**3. The identity validation form.**

- [ ] Organization Name — F-KEYS CREATIVE LLC
- [ ] Website — https://f-keys.com
- [ ] Business Identifier — the EIN
- [ ] Business address
- [ ] First and last name **exactly as printed on the government ID** that
      will be presented. Not a preferred name.

**4. Individual identity verification.**
A person representing the organization scans a government ID through
AU10TIX on a phone, then presents a Verified ID from Microsoft
Authenticator. Passport, driving licence or state ID. Not a library card.

**5. Wait.**
Processing takes **1 to 20 business days**, longer if more documents are
asked for. Any document supplied must have been issued in the last twelve
months and expire no sooner than two months out.

There is a fallback if organization validation stalls: an **Individual
Developer** path, US and Canada only, which sources details from the Azure
billing account and needs no business mailboxes. The certificate then
carries a personal name rather than the company's, which is worse for
something being sold under an LLC — so it is a fallback, not the plan.

## Then it signs itself

`build.js` already does the signing and the verifying. It is a no-op that
says so out loud until this file exists:

```
%APPDATA%\RemapWrap\signing.json

{ "endpoint": "https://wus2.codesigning.azure.net",
  "account":  "<the Artifact Signing account name>",
  "profile":  "<the certificate profile name>" }
```

and the Azure signing library is placed at `signing/Azure.CodeSigning.Dlib.dll`.

Already present on the build machine and verified:

- `signtool.exe` — Windows Kits 10.0.19041, x64
- `dotnet` 9.0.205

`signing.json` is **not** in this repository and must not be. The build
signs `RemapWrap.exe` *before* the payload is packed — otherwise the copy
inside the installer is the unsigned one and only the installer carries a
signature — then signs the installer itself, and runs `signtool verify /pa`
on both. Signed is not the same as verifiable, and only one of those is
worth reporting.

## The other route

**The Microsoft Store is the only way to get zero warnings**, because Store
apps are re-signed by Microsoft. It is worth considering as a second channel
rather than an alternative — particularly for the assistive audience, where
school and workplace machines are the likely target and enterprise policy
can remove the "Run anyway" option entirely, making an unsigned or
low-reputation download not merely alarming but impossible to run.
