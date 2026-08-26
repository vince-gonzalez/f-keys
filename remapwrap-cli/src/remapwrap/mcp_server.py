#!/usr/bin/env python3
"""
============================================================
remapwrap.mcp_server - describe a surface, get a working one
F-Keys | www.f-keys.com
------------------------------------------------------------
An MCP server exposing remapwrap to language models. Run it
with `remapwrap-mcp`, or add it to a client's configuration.
It speaks stdio.

WHY THE FIRST TOOL IS A REFUSAL

The likeliest failure is not a crash. It is a model asked for
a communication board, writing plausible JSON, and handing
back something that will not work: a dial bound to a command
that takes no value, a key bound to a command nothing runs, a
symbol with no label so a screen reader has nothing to say,
two controls on top of each other.

Every one of those looks correct. `check` is what tells them
apart, and it runs on everything this server produces before
anything is returned or written. A layout that would not work
is never handed back as though it would.

WHAT THIS IS FOR

RemapWrap is assistive software that also suits streamers.
The board is a document, so a board can be GENERATED - and a
description of what somebody needs is exactly the input a
model is good at turning into one.

Somebody describing a person in prose - what they can reach,
what they want to say, what they cannot read - and getting a
validated board that appears on the phone is the whole point
of the format being open.

WHAT IT WILL NOT DO

It will not decide what somebody needs. A board for a person
is built with that person, and a plausible board generated
from a paragraph is a starting point for a conversation, not
a prescription.
============================================================
"""

from __future__ import annotations

import json
import os
from typing import Any

from . import __version__
from . import generate
from .layout import (COMMANDS, IMPLEMENTED, PLANNED, SELF_CONTAINED, SHAPES,
                     TYPES, board, check, control, describe, place, save)

try:
    from mcp.server import MCPServer
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "The MCP server needs the optional dependency:\n"
        "    pip install 'remapwrap[mcp]'\n"
    ) from e


INSTRUCTIONS = """\
remapwrap builds RemapWrap control surfaces: boards of keys, dials, sliders,
timers and symbols that a phone shows and a PC obeys.

It is assistive software that also suits streamers, so the two things it is
most used for are a communication board and a stream deck, and they are the
same format.

Never hand back a layout you have not checked. `check_layout` catches the
failures that look correct: a dial bound to something that takes no value, a
key bound to a command nothing runs, a symbol with no label, two controls
overlapping. Everything this server generates is checked before it is
returned.

`save_board` writes into the profiles folder, where the running application
picks it up - so a board can go from a description to a phone without anybody
importing anything. That is a real change to somebody's device. Say what you
wrote and where.
"""

server = MCPServer(name="remapwrap", version=__version__,
                   instructions=INSTRUCTIONS)


def _profiles_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "RemapWrap", "profiles")


def _redirected(path: str) -> str:
    """Where a write to *path* will REALLY land, if that is somewhere else.

    Python installed from the Microsoft Store - the default on a clean
    Windows - runs in an app container that redirects %APPDATA% into its own
    package sandbox. A write reports success, the file exists, os.path.exists
    agrees, and the application it was written for never sees it.

    That is the worst failure available here: a confident false success. The
    board does not appear, nothing says why, and the obvious conclusion is
    that RemapWrap is broken.

    realpath resolves the redirection, so comparing it to the intended path
    detects it.
    """
    try:
        real = os.path.realpath(path)
    except OSError:
        return ""
    if os.path.normcase(real) == os.path.normcase(os.path.abspath(path)):
        return ""
    return real


def _checked(layout: dict, note: str = "") -> dict[str, Any]:
    """Never return a layout without saying whether it would work."""
    problems = check(layout)
    out: dict[str, Any] = {
        "layout": layout,
        "usable": not problems,
        "problems": problems,
        "summary": describe(layout),
    }
    if note:
        out["note"] = note
    if problems:
        out["do_not_use"] = (
            "This layout has problems and would not work as written. Fix them "
            "before saving it or showing it to anybody as finished."
        )
    return out


# --------------------------------------------------------------------------
# The guard.
# --------------------------------------------------------------------------

@server.tool(
    description=(
        "Report what remapwrap can and cannot do, the control types, and the "
        "commands that actually run. CALL THIS FIRST when a user asks for a "
        "board, a soundboard, a stream deck, a communication board, or an "
        "adapted control surface. Takes no arguments and writes nothing."
    )
)
def scope() -> dict[str, Any]:
    return {
        "what_this_builds": (
            "A RemapWrap layout: a JSON document describing controls on a "
            "board, which a phone renders and a PC obeys. Cells, not pixels, "
            "so the same board fits a phone held either way."
        ),
        "the_two_uses": {
            "assistive": "A communication board, an adapted keyboard, a "
                         "surface someone drives with one switch. Symbols, "
                         "speech, large targets.",
            "streaming": "A stream deck: scenes, audio, soundboard, macros.",
            "note": "Same format. The assistive case came first and the free "
                    "tier is built around it.",
        },
        "control_types": {
            "key": "fires while pressed",
            "toggle": "latches on and off, and can carry a second face",
            "pad": "soundboard trigger",
            "dial": "rotary, reports a value",
            "slider": "linear, reports a value",
            "timer": "counts down from arg seconds, or up when blank",
            "input": "opens the phone's own keyboard; what is written lands "
                     "on the PC",
        },
        "self_contained_types": list(SELF_CONTAINED),
        "commands_that_run": sorted(COMMANDS),
        "planned_and_not_built": sorted(PLANNED),
        "cannot_do": [
            "Decide what a person needs. A board for somebody is built WITH "
            "them; a board generated from a paragraph is a starting point for "
            "a conversation, not a prescription.",
            "Press anything. This writes documents; the RemapWrap application "
            "does the pressing.",
            "Reach a phone directly. Saving a profile is how a board arrives.",
        ],
        "where_boards_are_saved": {
            "folder": _profiles_dir(),
            "redirected": bool(_redirected(_profiles_dir())),
            "note": (
                "If redirected is true, this Python is sandboxed (the Microsoft "
                "Store build does this) and save_board cannot reach the folder "
                "RemapWrap reads. It will refuse rather than report a false "
                "success."
            ),
        },
        "the_rule": (
            "Never hand back a layout without running check_layout. The "
            "failures that matter all look correct on the page: a dial bound "
            "to a command that takes no value, a key bound to something "
            "nothing runs, a symbol with no label so a screen reader has "
            "nothing to say, two controls overlapping."
        ),
        "version": __version__,
    }


# --------------------------------------------------------------------------
# The one that must always be reachable.
# --------------------------------------------------------------------------

@server.tool(
    description=(
        "Check whether a layout would actually work, and say why not in plain "
        "sentences. ALWAYS RUN THIS on any layout before returning it or "
        "saving it -- a broken layout looks exactly like a working one, which "
        "is the entire reason this exists. Takes the layout as a JSON object "
        "or a JSON string."
    )
)
def check_layout(layout: Any) -> dict[str, Any]:
    if isinstance(layout, str):
        try:
            layout = json.loads(layout)
        except ValueError as e:
            return {"usable": False, "problems": ["That is not JSON: " + str(e)]}
    if not isinstance(layout, dict):
        return {"usable": False,
                "problems": ["A layout is an object with a keys list."]}

    # build_board returns a PROFILE -- {name, pages, schema} -- and this only
    # read a bare layout, so the output of the main generator could not be
    # passed to the checker at all. It came back "that is not a layout", which
    # reads as a broken board rather than a mismatched wrapper, and it made
    # the server's own rule ("never hand back a layout without checking it")
    # impossible to follow. save_board already unwrapped pages; this did not.
    pages = layout.get("pages")
    if isinstance(pages, list) and pages:
        results = []
        for n, page in enumerate(pages):
            if not isinstance(page, dict):
                results.append(["Page {} is not an object.".format(n + 1)])
                continue
            results.append(check({"cols": page.get("cols"),
                                  "rows": page.get("rows"),
                                  "keys": page.get("keys", [])}))
        problems = [
            ("Page {}: {}".format(n + 1, p) if len(results) > 1 else p)
            for n, page_problems in enumerate(results) for p in page_problems
        ]
        first = {"cols": pages[0].get("cols"), "rows": pages[0].get("rows"),
                 "keys": pages[0].get("keys", [])}
        return {
            "usable": not problems,
            "problems": problems,
            "pages_checked": len(pages),
            "summary": describe(first) if not problems else None,
        }

    problems = check(layout)
    return {
        "usable": not problems,
        "problems": problems,
        "summary": describe(layout) if not problems else None,
    }


# --------------------------------------------------------------------------
# Generators.
# --------------------------------------------------------------------------

@server.tool(
    description=(
        "Build a board of keys from a list of {label, command, arg} entries, "
        "for example {label: 'Yes', command: 'speak.text', arg: 'Yes'} to say "
        "it aloud, or {label: 'Copy', command: 'win.keystroke', arg: 'ctrl+c'}. "
        "There is no 'text' or 'action' field: speaking (speak.text) and "
        "typing into the PC (win.text) are different and are not guessed. "
        "laid out automatically in phone proportions. The general builder: use "
        "it for a communication board (speak.text with the phrase in arg), a "
        "shortcut deck (win.keystroke), or anything else. Call scope() for the "
        "commands that run. Every board is checked before it is returned. For "
        "a symbol board give each entry a label as well as a picture -- a key "
        "with no label is silent to a screen reader."
    )
)
def build_board(entries: list[dict], name: str = "Generated") -> dict[str, Any]:
    if not entries:
        return {"usable": False, "problems": ["Give at least one entry."]}

    kind_for = {}
    for e in entries:
        kind_for[str(e.get("label", ""))] = e

    # Reuse the deck fitter so the board comes out phone-shaped rather than a
    # ribbon; it sizes for 4x4 keys, which is what these are.
    try:
        cols, rows = generate._fit(len(entries), 4, 4)
    except Exception:
        cols, rows = 12, 21

    lay = board(cols, rows)
    palette = generate.PALETTE
    problems: list[str] = []

    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            problems.append("Entry {} is not an object.".format(i + 1))
            continue

        # control() falls back to the type name when a label is missing, so a
        # picture with no label quietly became a key that reads "KEY" to a
        # screen reader. On a symbol board that is worse than no key at all:
        # the person who most needs it spoken is the one who cannot read the
        # picture. Refuse instead of substituting.
        given_label = str(e.get("label") or "").strip()
        if e.get("image") and not given_label:
            problems.append(
                "Entry {} has a picture and no label. A screen reader would "
                "have nothing to say about it, and the person who most needs "
                "it spoken is the one who cannot read the picture."
                .format(i + 1))
            continue
        # A key with no command is a dead key. Unknown and planned commands
        # were already refused below, but a MISSING one sailed through and
        # produced a board that looks finished and does nothing -- the same
        # failure, reached by omission instead of by typo.
        #
        # It happens because the obvious thing to write is {label, text} and
        # the schema wants {label, command, arg}. The synonyms are named
        # rather than guessed: "text" is genuinely ambiguous on a
        # communication board -- speak.text says it aloud, win.text types it
        # into the PC -- and choosing wrong there is choosing for somebody
        # whose whole board is their voice.
        kind = str(e.get("type", "key"))
        if not str(e.get("command", "")).strip() and kind not in SELF_CONTAINED:
            strays = [k for k in ("text", "say", "speak", "action", "keys",
                                  "key", "press") if e.get(k)]
            hint = ""
            if "text" in strays or "say" in strays or "speak" in strays:
                hint = (" To make it SPEAK, use command 'speak.text' with the "
                        "words in arg. To make it TYPE into the PC, use "
                        "'win.text'. These are different things and this will "
                        "not choose between them for you.")
            elif strays:
                hint = (" For a keystroke use command 'win.keystroke' with "
                        "arg like 'ctrl+c'.")
            elif kind in ("dial", "slider"):
                hint = (" A dial or slider needs a command that takes a "
                        "value, such as 'audio.master'.")
            problems.append(
                "Entry {} ({}) has no command, so the key would do nothing "
                "when pressed.{}{}".format(
                    i + 1, given_label or "unlabelled",
                    " Found {} instead of 'command'.".format(
                        " and ".join(repr(k) for k in strays)) if strays else "",
                    hint))
            continue

        kwargs: dict[str, Any] = {
            "type": str(e.get("type", "key")),
            "command": str(e.get("command", "")),
            "label": generate._label(e.get("label", "KEY {}".format(i + 1))),
            "sub": str(e.get("sub", "")),
            "color": str(e.get("color") or palette[i % len(palette)]),
        }
        if e.get("arg") is not None:
            kwargs["arg"] = str(e["arg"])
        if e.get("image"):
            kwargs["image"] = str(e["image"])
        if e.get("whenOn"):
            kwargs["whenOn"] = e["whenOn"]
        try:
            place(lay, control(**kwargs))
        except Exception as err:
            problems.append("{}: {}".format(e.get("label", "entry"), err))

    lay_doc = {"schema": 1, "name": name,
               "pages": [{"name": "Page 1", "cols": lay["cols"],
                          "rows": lay["rows"], "keys": lay["keys"]}]}
    result = _checked(lay)
    result["profile"] = lay_doc
    if problems:
        result["problems"] = list(result["problems"]) + problems
        result["usable"] = False
    return result


@server.tool(
    description=(
        "Build a soundboard: one pad per sound file in a folder. Takes the "
        "folder path. Labels come from the filenames. Checked before it is "
        "returned."
    )
)
def build_soundboard(folder: str) -> dict[str, Any]:
    try:
        return _checked(generate.soundboard(folder))
    except Exception as e:
        return {"usable": False, "problems": [str(e)]}


@server.tool(
    description=(
        "Build an audio mixer: a slider per named application, plus the master "
        "and the microphone. Applications are named as Windows names them, so "
        "'Discord' rather than 'Discord Voice'. Checked before it is returned."
    )
)
def build_mixer(applications: list[str], master: bool = True,
                mic: bool = True) -> dict[str, Any]:
    try:
        return _checked(generate.mixer(list(applications or []),
                                       master=master, mic=mic))
    except Exception as e:
        return {"usable": False, "problems": [str(e)]}


# --------------------------------------------------------------------------
# The one that changes somebody's device.
# --------------------------------------------------------------------------

@server.tool(
    description=(
        "Save a profile into the RemapWrap profiles folder, where the running "
        "application picks it up and it appears on the phone. THIS CHANGES A "
        "REAL DEVICE -- say what was written and where. The layout is checked "
        "first and a layout with problems is REFUSED rather than written. Give "
        "it a profile (from build_board) or a plain board, and a name."
    )
)
def save_board(profile: Any, name: str = "") -> dict[str, Any]:
    if isinstance(profile, str):
        try:
            profile = json.loads(profile)
        except ValueError as e:
            return {"written": False, "problems": ["That is not JSON: " + str(e)]}
    if not isinstance(profile, dict):
        return {"written": False, "problems": ["Give a profile or a board."]}

    # Check whichever shape arrived, before anything touches the disk.
    pages = profile.get("pages")
    to_check = ({"cols": pages[0].get("cols"), "rows": pages[0].get("rows"),
                 "keys": pages[0].get("keys", [])}
                if isinstance(pages, list) and pages else profile)
    problems = check(to_check)
    if problems:
        return {
            "written": False,
            "problems": problems,
            "refused": (
                "A layout with problems is not written. Writing it would put a "
                "board on somebody's phone with controls that do nothing, and "
                "they would find out by pressing one."
            ),
        }

    if name:
        profile["name"] = name
    profile.setdefault("name", "Generated")
    profile.setdefault("schema", 1)

    folder = _profiles_dir()
    try:
        os.makedirs(folder, exist_ok=True)
        safe = "".join(c for c in str(profile["name"])
                       if c.isalnum() or c in " -_")[:64].strip() or "Generated"
        path = os.path.join(folder, safe + ".json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(profile, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    except OSError as e:
        return {"written": False, "problems": [str(e)]}

    elsewhere = _redirected(path)
    if elsewhere:
        return {
            "written": False,
            "intended_path": path,
            "actually_written_to": elsewhere,
            "problems": [
                "The write was redirected by the sandbox this Python runs in, "
                "so the file is NOT where RemapWrap looks and the board will "
                "not appear."
            ],
            "why": (
                "Python installed from the Microsoft Store runs in an app "
                "container that redirects %APPDATA% into its own package "
                "folder. Everything reports success and the application never "
                "sees the file."
            ),
            "fix": (
                "Install Python from python.org and run the server with that. "
                "A virtual environment does NOT escape this: a venv built from "
                "the Store Python inherits the same redirection, because the "
                "container follows the base installation rather than the "
                "executable. Otherwise, copy the file from "
                "actually_written_to into intended_path by hand -- the file "
                "itself is correct, only its location is wrong."
            ),
        }

    return {
        "written": True,
        "path": path,
        "profile_name": profile["name"],
        "what_happens_now": (
            "The folder is the import path: a running RemapWrap picks this up "
            "and it appears in the profiles list. Tell the person the name to "
            "look for."
        ),
    }


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
