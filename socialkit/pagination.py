"""Opaque offset cursors for ranked lists."""
import base64


def encode_cursor(offset):
    return base64.urlsafe_b64encode(f"o{offset}".encode()).decode().rstrip("=")


def decode_cursor(text):
    """Offset encoded in a cursor; an empty cursor means the start. Raises ValueError for anything else."""
    if not text:
        return 0
    try:
        raw = base64.urlsafe_b64decode(text + "=" * (-len(text) % 4)).decode()
    except (ValueError, UnicodeDecodeError):
        raise ValueError("bad cursor")
    if not raw.startswith("o") or not raw[1:].isdigit():
        raise ValueError("bad cursor")
    return int(raw[1:])


def page(items, cursor, size):
    """(chunk, next_cursor) for a list; next_cursor is None on the last page."""
    if size < 1:
        raise ValueError("page size must be positive")
    start = decode_cursor(cursor)
    chunk = list(items[start:start + size])
    end = start + size
    return chunk, (encode_cursor(end) if end < len(items) else None)
