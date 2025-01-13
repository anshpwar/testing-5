"""Composite charges built from the policy tables."""
from . import rules


def combined_charge(x):
    """Total of the two base schedules for x."""
    return rules.daily_post_limit(x) + rules.daily_reply_limit(x)
