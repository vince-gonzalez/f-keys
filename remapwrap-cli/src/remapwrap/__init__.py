"""
============================================================
remapwrap - control surfaces as data
F-Keys | www.f-keys.com
------------------------------------------------------------
A RemapWrap layout is a JSON document describing controls on a
board. The dashboard writes one by dragging; this writes one
from whatever already describes the work.

    from remapwrap import soundboard, check, save

    board = soundboard("./samples")
    assert not check(board)
    save(board, "board.json")

Then import it in the dashboard and push it to a phone.

No dependencies. Standard library only.
============================================================
"""

#: Kept in step with pyproject.toml. The wheel filename and its metadata
#: both come from pyproject and agree with each other regardless, so a
#: drift here is invisible from outside the wheel.
__version__ = "0.3.0"

from .layout import (LayoutError, board, check, control, describe, load,
                     overlaps, place, save)
from .generate import deck, mixer, soundboard

__all__ = ["LayoutError", "board", "check", "control", "describe", "load",
           "overlaps", "place", "save", "deck", "mixer", "soundboard",
           "__version__"]
