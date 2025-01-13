"""textfmt: tiny text formatting helpers (vendored copy, version 1.0.0)."""

__version__ = "1.0.0"


def pad_left(text, width, fill=" "):
    """Right-align text in a field of the given width."""
    return text.rjust(width, fill)
