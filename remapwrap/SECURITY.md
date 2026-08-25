# RemapWrap presses keys on your computer

**DRAFT — not published. Needs your sign-off.**

This page exists because RemapWrap does the same thing a keylogger does,
in the opposite direction, and the honest move is to say so on the tin
rather than have somebody discover it.

---

## What it does, plainly

RemapWrap injects keystrokes into Windows. That is the product. When you
press a key on your phone, your PC behaves exactly as though you had
pressed that combination on the keyboard.

It also:

- opens two ports on your local network (7331 and 7332) so a phone can
  reach it,
- reads and sets your system, microphone and per-application volume,
- reads which window is in front, so a profile can switch itself,
- starts programs, when you bind a key to do that.

Your antivirus may flag it, and that is a reasonable thing for an
antivirus to do about a program with these abilities. We would rather tell
you first than have you find out from a warning dialog.

## What it does not do

**It does not read your keyboard.** RemapWrap installs no keyboard hook of
any kind — nothing at the Windows level ever sees a key you press. The
library it uses is only ever asked to *send* keys: three calls, `type`,
`pressKey` and `releaseKey`, and you can check that yourself with a search
for `keyboard.` in `remapwrap-server.js`.

There is exactly one exception, and it is worth stating rather than
glossing: when you click **PRESS THE KEYS** in the dashboard to bind a
shortcut, that page listens for the next key combination — inside that one
browser tab, only while you have asked it to, and it stops the moment you
press something or hit Escape. It keeps the combination you chose and
nothing else. No buffer of keystrokes exists to leak, because one is never
built.

The one thing it reads about your activity is the name and title of the
window in front, used only to switch profiles, and that never leaves your
PC. See PRIVACY.

## Who can press your keys

Only a phone you have let in. When RemapWrap first runs it generates a
32-byte secret and a six-digit PIN. A phone joins by scanning the QR code,
which carries the secret, or by typing the PIN shown on your screen. Five
wrong PINs and that device is locked out for five minutes.

Anything that cannot present the secret is refused and disconnected. The
dashboard — which builds boards and displays the PIN — only answers to the
machine it is running on; ask for it from another device and you get the
phone page instead.

**This is honest about its limits.** It is protection against somebody else
on your network. It is not protection against somebody sitting at your
unlocked PC, and it is not encryption: RemapWrap speaks plain HTTP on your
local network, so anyone able to watch that network can see which buttons
you press. Do not run it on a network you would not trust with your
browsing.

## Reporting a problem

If you find a way to make RemapWrap press keys without being paired, or to
read anything it should not, write to [EMAIL — YOUR CHOICE]. Tell us what
you did and we will fix it and credit you if you want to be credited.

---

**Open questions for you:**

1. **Which email.**
2. **Should this ship a signed build before it is published?** This page
   invites scrutiny, and the first thing anyone scrutinising will notice is
   that the executable is unsigned. Publishing this before the certificate
   is bought points at the weakest part of the product.
3. **The plain-HTTP paragraph is the most uncomfortable sentence here and
   the most important one.** It can be removed, and it should not be — but
   that is your call, not mine.
