"""Tests for the MCP server.

Each of these was a bug that shipped in a working-looking build, so each one
is written to fail if the bug comes back rather than to describe the feature.
"""

import json

import pytest

from remapwrap import mcp_server as M


def call(_tool, **kw):
    """Invoke a tool through whatever the decorator wrapped it in."""
    t = getattr(M, _tool)
    for attr in ("fn", "func", "__wrapped__", "handler"):
        inner = getattr(t, attr, None)
        if callable(inner):
            return inner(**kw)
    return t(**kw)


def profile_of(result):
    return result.get("profile") or result


GOOD = [
    {"label": "Yes", "command": "speak.text", "arg": "Yes"},
    {"label": "Copy", "command": "win.keystroke", "arg": "ctrl+c"},
    {"label": "Type", "type": "input"},
]


def test_a_good_board_builds():
    r = call("build_board", name="Everyday", entries=GOOD)
    assert r["usable"], r["problems"]
    keys = profile_of(r)["pages"][0]["keys"]
    assert len(keys) == 3


def test_every_key_carries_a_label():
    """A key a screen reader cannot announce is not usable on an AAC board."""
    r = call("build_board", name="Everyday", entries=GOOD)
    assert all(k.get("label") for k in profile_of(r)["pages"][0]["keys"])


def test_a_picture_without_a_label_is_refused():
    r = call("build_board", name="Bad",
             entries=[{"command": "speak.text", "arg": "hi", "image": "cat.png"}])
    assert not r["usable"]
    assert "screen reader" in " ".join(r["problems"])


@pytest.mark.parametrize("entry", [
    {"label": "Yes"},                          # nothing at all
    {"label": "Yes", "text": "Yes"},           # the field a model reaches for
    {"label": "Copy", "action": "ctrl+c"},     # the other one
    {"label": "Vol", "type": "dial"},          # a dial with nothing to turn
])
def test_a_key_that_would_do_nothing_is_refused(entry):
    """These all built happily once and produced a board of dead keys."""
    r = call("build_board", name="Dead", entries=[entry])
    assert not r["usable"]
    assert "do nothing" in " ".join(r["problems"])


def test_the_speak_or_type_ambiguity_is_not_guessed():
    r = call("build_board", name="Amb",
             entries=[{"label": "Yes", "text": "Yes"}])
    said = " ".join(r["problems"])
    assert "speak.text" in said and "win.text" in said


@pytest.mark.parametrize("entry", [
    {"label": "Type", "type": "input"},
    {"label": "5 min", "type": "timer", "arg": "300"},
])
def test_self_contained_controls_need_no_command(entry):
    assert call("build_board", name="Fine", entries=[entry])["usable"]


def test_an_unknown_command_is_refused():
    r = call("build_board", name="X",
             entries=[{"label": "X", "command": "win.nonsense", "arg": "a"}])
    assert not r["usable"]


def test_a_planned_command_is_refused_as_planned():
    r = call("build_board", name="X",
             entries=[{"label": "S", "command": "obs.scene", "arg": "Live"}])
    assert not r["usable"]
    assert "planned" in " ".join(r["problems"])


def test_check_layout_reads_what_build_board_returns():
    """These disagreed: the builder emitted a profile, the checker read only
    a bare layout, so the server's own rule could not be followed."""
    built = call("build_board", name="Everyday", entries=GOOD)
    checked = call("check_layout", layout=json.dumps(profile_of(built)))
    assert checked["usable"] == built["usable"] == True
    assert checked["pages_checked"] == 1


def test_check_layout_still_catches_a_broken_profile():
    """The unwrapping must not have turned the check into a rubber stamp."""
    built = profile_of(call("build_board", name="Everyday", entries=GOOD))
    broken = json.loads(json.dumps(built))
    broken["pages"][0]["keys"][0]["command"] = "win.nonsense"
    assert not call("check_layout", layout=json.dumps(broken))["usable"]


def test_check_layout_still_reads_a_bare_layout():
    built = profile_of(call("build_board", name="Everyday", entries=GOOD))
    page = built["pages"][0]
    bare = {"cols": page["cols"], "rows": page["rows"], "keys": page["keys"]}
    assert call("check_layout", layout=bare)["usable"]


def test_save_board_refuses_a_broken_board():
    """Never write a board that would reach a phone with dead controls."""
    r = call("save_board", profile={"keys": [
        {"label": "X", "type": "key", "command": "win.nonsense",
         "col": 0, "row": 0, "w": 2, "h": 2}]})
    assert r["written"] is False


def test_save_board_refuses_rather_than_reporting_a_false_success():
    """Under a sandboxed Python the write lands somewhere the application
    never reads. It reported written: True with a plausible path."""
    built = profile_of(call("build_board", name="Everyday", entries=GOOD))
    r = call("save_board", profile=built)
    if M._redirected(M._profiles_dir()):
        assert r["written"] is False
        assert "venv" in json.dumps(r)
    else:
        assert r["written"] is True


def test_scope_reports_whether_this_python_is_sandboxed():
    s = call("scope")
    assert "redirected" in s["where_boards_are_saved"]


def test_the_mixer_generator_produces_a_usable_board():
    r = call("build_mixer", applications=["Chrome", "Discord"])
    assert r["usable"], r.get("problems")


def test_the_soundboard_generator_produces_a_usable_board(tmp_path):
    for n in ("clap.wav", "horn.wav", "notes.txt"):
        (tmp_path / n).write_bytes(b"")
    r = call("build_soundboard", folder=str(tmp_path))
    assert r["usable"], r.get("problems")


def test_a_soundboard_from_a_folder_with_no_sounds_is_not_a_silent_success(tmp_path):
    """An empty board is not a board. Saying so beats handing back a page of
    nothing that looks like it worked."""
    r = call("build_soundboard", folder=str(tmp_path))
    assert not r["usable"]


def test_a_soundboard_from_a_missing_folder_says_so():
    r = call("build_soundboard", folder=str("no-such-folder-anywhere"))
    assert not r["usable"]
