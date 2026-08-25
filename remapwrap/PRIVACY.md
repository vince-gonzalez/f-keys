# What RemapWrap knows about you

**DRAFT — not published. This needs your words and your sign-off before it
goes on a page.** Everything in it has been checked against the code, and
each claim names the file it is true in, so you can verify any line rather
than take it on trust.

---

## The short version

Nothing leaves your computer.

RemapWrap has no account, no sign-in, and no server of ours to talk to. It
does not phone home when it starts, when you pair a phone, when you buy a
licence, or ever. Unplug the internet and every part of it still works.

## What it does on your machine

RemapWrap runs a small web server on your own computer and your phone
connects to it over your own network. The two devices talk directly. We are
not in the middle, because there is no middle.

It stores three things, all in `%APPDATA%\RemapWrap` on your PC:

- **Your boards**, one JSON file per profile. You can read them, edit them,
  copy them, and delete them with any text editor.
- **A pairing secret and a six-digit PIN**, so a phone you have approved can
  reconnect and one you have not cannot connect at all.
- **Your licence key, if you bought one**, which is the key you were sent
  and nothing else.

That is the complete list. Delete the folder and RemapWrap knows nothing
about you again.

## What it deliberately does not send to your phone

RemapWrap reads which window is in front, so a profile can switch itself
when you change program. **That reading never leaves the PC.** A window
title can contain a document name, an email subject, or a client's name,
and your phone has no use for any of it, so it is removed before anything
is sent.

*(Verifiable: `remapwrap-server.js`, the `forPhone` object in `pollState`.
There is a test named "the phone is not told what window is in front".)*

## What we collect

Nothing. There is no analytics, no crash reporting, no telemetry, no update
check, and no unique identifier. We cannot tell how many people use
RemapWrap, and that is a consequence of the design rather than a promise
about our intentions.

## Your licence

A licence key is a signed statement that is checked on your own machine.
Buying one does not create an account. Entering one does not contact us.
If we vanished tomorrow, every licence already issued would keep working.

If you bought a licence, we hold whatever our payment processor gave us
about that sale — your name and email — because we have to in order to
re-send you a key you have lost. That is a record of a purchase, not a
record of your usage, and we have no way to connect the two.

## Your rights

If you are in the UK or EU, you can ask us what we hold about a purchase,
ask for it to be corrected, or ask for it to be deleted. Write to
[EMAIL — YOUR CHOICE] and we will do it.

Because RemapWrap collects nothing, there is nothing to export and nothing
to delete on the software side. The folder on your PC is yours already.

## Children

RemapWrap has no account, collects nothing, and shows no advertising, so it
does not gather data from anybody of any age.

---

**Open questions for you before this ships:**

1. **Which email address.** The house rule is `@me.com`, not the gmail.
2. **Do you want to name the payment processor?** Saying "Stripe holds your
   card details, we never see them" is stronger than leaving it vague, but
   it commits you to that processor in writing.
3. **Company identification.** F-KEYS CREATIVE LLC and a contact address
   are normally required on a privacy notice. A PO box is acceptable and
   your home address is not something you have to publish.
