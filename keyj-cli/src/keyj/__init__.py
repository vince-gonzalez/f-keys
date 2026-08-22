"""Key-J on the command line. See keyj.cli for the entry point."""

from .notes import Note, midi_to_freq, midi_to_name, name_to_freq, name_to_midi

__version__ = "0.1.2"
__all__ = ["Note", "midi_to_freq", "midi_to_name", "name_to_freq",
           "name_to_midi", "__version__"]
