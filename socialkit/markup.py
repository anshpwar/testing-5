"""Mentions, hashtags and safe HTML for post bodies."""
import html
import re

MENTION = r"(?<![\w@])@([a-z][a-z0-9_]{2,19})\b"
HASHTAG = r"(?<![\w#&])#([A-Za-z][A-Za-z0-9_]{1,29})"
TOKEN_RE = re.compile(f"{MENTION}|{HASHTAG}")
URL_RE = re.compile(r"https?://[^\s<>\"]+")


def _unique(items):
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def mentions(text):
    """Handles mentioned in text, lower case, in order of first appearance."""
    return _unique(m.group(1) for m in TOKEN_RE.finditer(text) if m.group(1))


def hashtags(text):
    """Hashtags in text without the #, lower case, in order of first appearance."""
    return _unique(m.group(2).lower() for m in TOKEN_RE.finditer(text) if m.group(2))


def links(text):
    return URL_RE.findall(text)


def to_html(text, known_handles=None):
    """Escape text and link mentions and hashtags. Unknown handles stay plain when a known set is given."""
    out, pos = [], 0
    for m in TOKEN_RE.finditer(text):
        out.append(html.escape(text[pos:m.start()], quote=False))
        if m.group(1):
            handle = m.group(1)
            if known_handles is None or handle in known_handles:
                out.append(f'<a class="mention" href="/profiles/{handle}/">@{handle}</a>')
            else:
                out.append(html.escape(m.group(0), quote=False))
        else:
            tag = m.group(2)
            out.append(f'<a class="hashtag" href="/feed/tags/{tag.lower()}/">#{tag}</a>')
        pos = m.end()
    out.append(html.escape(text[pos:], quote=False))
    return "".join(out)
