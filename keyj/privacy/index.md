# Key-J Privacy

> Key-J collects nothing. What the global keyboard hook sees, what is kept, and how to verify it.

Canonical: https://f-keys.com/keyj/privacy/

What a program with a global keyboard hook does with what it can see.

## The short version

Key-J does not collect anything. No account, no telemetry, no analytics, no
crash reports, no network calls of any kind while it runs. Nothing you type is
stored, and nothing leaves your machine.

That is worth stating in detail rather than in a sentence, because Key-J
installs a global keyboard hook, and you should not have to take that on
trust.

## What the desktop application can see

With **Global Capture** switched on, Key-J receives a signal from the
operating system each time any key is pressed or released, in any application.
That is what makes it play while you type elsewhere, and there is no version of
that feature which sees less.

What it does with that signal is the part that matters:

| Field | Value |
| --- | --- |
| Held in memory | Which key is currently down, so the note can be released when you let go. Discarded immediately after. |
| Written to disk | Nothing. No log, no history, no buffer of keystrokes. |
| Sent anywhere | Nothing. The application makes no outbound network requests. |

**Global Capture starts switched off** every time the application launches,
and the header shows which state it is in: **Window only** or **Global**.
It is never enabled without you enabling it.

## Sequence mode does not need to know what you typed

When a sequence is loaded, every key plays the next note of it, so which key
you pressed stops being information Key-J needs. The command line player takes
this further and never reads the key identity at all — it asks whether a
key went down and discards the rest. There is no keystroke buffer in it to
leak, subpoena or lose.

## What the browser version can see

Only what you type into its own page. A web page cannot read keystrokes
outside itself; that is a boundary enforced by the browser, not a promise made
by us. Sequences and settings are kept in your browser's local storage on your
own machine.

## Files Key-J writes

| Field | Value |
| --- | --- |
| Settings | Your tone, tuning and last-used tab, in the standard per-user application data directory. |
| Exports | Only where you choose to save them. |

Uninstalling removes the application. Anything you exported is yours and stays
where you put it.

## Verifying this rather than believing it

The Key-J source is published. It is not free to copy — see
[the
licence](https://github.com/vince-gonzalez/f-keys/blob/main/keyj/LICENSE) — but it is readable precisely so that a program which installs
a keyboard hook can be audited by the people running it. The global hook lives in
keyj/desktop/src/main.js; the handler is a few lines long and you can
read every one of them.

You can also check from the outside: run Key-J with any network monitor and
watch it make no requests.

## Children

Key-J is not directed at children under 13 and collects no information from
anyone, of any age.

## Changes and contact

If this ever stops being true, this page changes before the behaviour does.
Questions: [hello@f-keys.com](mailto:hello@f-keys.com).

F-Keys Creative LLC · last reviewed 20 August 2026

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
