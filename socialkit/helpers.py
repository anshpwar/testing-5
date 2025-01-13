"""Small text helpers shared by services."""


def clip(text, limit):
    """Shorten text to at most limit characters, ending with an ellipsis."""
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
