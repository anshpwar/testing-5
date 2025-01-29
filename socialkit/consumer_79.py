"""Consumer added independently of the base-side change (scenario 79)."""


from .conf import get_setting


def attempts():
    return get_setting("RETRY_LIMIT") + 1
