"""Runtime configuration lookups with explicit defaults."""

DEFAULTS = {
    "RETRY_LIMIT": 3,
    "TIMEOUT_SECONDS": 30,
    "BATCH_SIZE": 100,
}


def get_setting(name, overrides=None):
    """Return a setting, preferring overrides over DEFAULTS."""
    if overrides and name in overrides:
        return overrides[name]
    return DEFAULTS[name]
