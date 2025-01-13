"""Profile handle rules: normalisation, validation and suggestions."""
import re

HANDLE_RE = re.compile(r"^[a-z][a-z0-9_]{2,19}$")
RESERVED = frozenset({"admin", "api", "root", "support", "moderator", "system", "help", "about", "me", "null"})


def normalize(raw):
    """Canonical form of a handle: no leading @, no spaces, lower case."""
    return (raw or "").strip().lstrip("@").lower()


def validate(raw):
    """Return the normalised handle or raise ValueError describing the problem."""
    handle = normalize(raw)
    if not handle:
        raise ValueError("handle required")
    if handle in RESERVED:
        raise ValueError("handle reserved")
    if not HANDLE_RE.match(handle):
        raise ValueError("handle must be 3-20 characters: letters, digits, underscore, starting with a letter")
    return handle


def is_valid(raw):
    try:
        validate(raw)
    except ValueError:
        return False
    return True


def suggest(display_name, taken=()):
    """Derive a free handle from a display name, appending a counter when needed."""
    base = re.sub(r"[^a-z0-9_]+", "_", display_name.strip().lower()).strip("_")
    if not base or not base[0].isalpha():
        base = "user_" + base
    base = base[:16].rstrip("_") or "user"
    if len(base) < 3:
        base = base + "_" * (3 - len(base))
    taken = set(taken)
    candidate, counter = base, 1
    while candidate in taken or candidate in RESERVED:
        counter += 1
        candidate = f"{base[:16]}{counter}"
    return candidate
