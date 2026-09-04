# RemapWrap

> Your phone is already the extra row of keys.

Canonical: https://f-keys.com/remapwrap/

Turn the phone in your hand into a drag-and-drop control surface that fires real OS-level keystrokes. No app to install, no hardware to buy, and the software you are driving never knows it is not a keyboard.

**0.1.0 alpha** · Windows, macOS, Linux · Node.js 16+ · pip install remapwrap for the layout builder · free, no account, unlimited keys

## Zero to a deck in fifteen seconds

Run the server, scan the QR code, and the phone in your hand is a control surface that
fires real OS-level keystrokes. The software you are driving never knows RemapWrap exists,
which is the point: it works with everything, because it is indistinguishable from a
keyboard.

A Stream Deck is a hundred and fifty dollars and a drawer you have to find it in. This
is the glass you are already holding.

## Then sixty seconds to make it yours

The default layout is the fifteen-second answer. The real one is a mock screen you draw
on: drop a control anywhere, size it, colour it, and decide what it sends.

| Field | Value |
| --- | --- |
| Buttons | Any shape and size, from a single key to a full-width bar |
| Sliders | Continuous values — a volume, a zoom, an exposure |
| Dials | Rotary control, for the things a knob suits better than a bar |
| Scrollers | Wheel input, for timelines and long documents |
| Trackpad | An area that moves the pointer, because the phone already tracks a finger |

Every input a mouse has, on a surface with no fixed shape. A deck for editing does not
have to look anything like a deck for streaming, and neither has to look like a keyboard.

## Where it actually is

**The alpha is buttons.** The recovered v0.1.0 pairs over a QR code, serves a grid of
keys, fires them through the OS, and buzzes the phone on press. Layouts are JSON, edited
live in the dashboard. That much works today.

The sliders, dials, scrollers and trackpad above are the design and are not written yet.
They are on this page because they are what the product is for, and marked plainly so
nobody downloads the alpha expecting them.

## The company is named after this

RemapWrap began as **F-Keys** — an extra row of keys, on glass you already own.
The name outgrew the product and became the company. The product then went missing for five
months, surviving in a single zip file in a folder called "zip to sort".

## Running it

npm install
**npm start**
scan the QR with your phone
Both devices on the same network. Ports 7331 and 7332 open locally. Keystroke injection
via @nut-tree-fork/nut-js.

## How it works

## What the free version does

## Specifications

| Field | Value |
| --- | --- |
| Version | 0.1.0 alpha |
| Runtime | Node.js 16+ |
| Phone needs | A browser |
| Install | None on the phone |
| Layout builder | pip install remapwrap — 0.6.0, MIT |
| Source | vince-gonzalez/f-keys |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
