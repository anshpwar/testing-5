"""Content screening and moderation escalation."""
from . import markup, rules

BLOCKED_TERMS = ("buy-followers-now", "free-crypto-giveaway", "click-here-to-win")
MAX_LINKS = 3
MAX_MENTIONS = 5
SHOUTING_RATIO = 0.7
SHOUTING_MIN_LETTERS = 12

SEVERITY = {"blocked_term": 3, "link_flood": 2, "mention_flood": 2, "shouting": 1}


def flags(text):
    """Reasons a body looks abusive, in a fixed order."""
    found = []
    lowered = text.lower()
    if any(term in lowered for term in BLOCKED_TERMS):
        found.append("blocked_term")
    if len(markup.links(text)) > MAX_LINKS:
        found.append("link_flood")
    if len(markup.mentions(text)) > MAX_MENTIONS:
        found.append("mention_flood")
    letters = [ch for ch in text if ch.isalpha()]
    if len(letters) >= SHOUTING_MIN_LETTERS and sum(ch.isupper() for ch in letters) / len(letters) > SHOUTING_RATIO:
        found.append("shouting")
    return found


def severity(found):
    return sum(SEVERITY[f] for f in found)


def should_auto_hide(open_reports, author_followers):
    """Whether enough distinct reports have arrived to hide an update pending review."""
    return open_reports >= rules.report_auto_hide_threshold(author_followers)


def penalty(strikes):
    """Mute hours and suspension days for an account that has accumulated this many strikes."""
    return {"mute_hours": rules.mute_duration_hours(strikes), "suspension_days": rules.suspension_days(strikes)}


def cooldown_minutes(reports_today):
    return rules.report_cooldown_minutes(reports_today)
