"""Timeline ranking: engagement scores weighted by freshness, and trending tags."""
import math
from collections import Counter
from dataclasses import dataclass

from . import markup, rules


@dataclass(frozen=True)
class Candidate:
    id: int
    age_hours: float
    likes: int
    replies: int


def whole_hours(age_hours):
    return max(0, math.floor(age_hours))


def engagement_points(likes, replies, age_hours):
    """Weighted engagement of one update; recent engagement counts for more."""
    hours = whole_hours(age_hours)
    return likes * rules.like_weight_points(hours) + replies * rules.reply_weight_points(hours)


def is_fresh(age_hours, author_followers):
    """Whether an update of an author with this many followers is still eligible for timelines."""
    return age_hours <= rules.freshness_window_hours(author_followers)


def score(candidate):
    return engagement_points(candidate.likes, candidate.replies, candidate.age_hours)


def rank(candidates):
    """Candidate ids, best first. Ties go to the newer update, then to the higher id."""
    ordered = sorted(candidates, key=lambda c: (-score(c), c.age_hours, -c.id))
    return [c.id for c in ordered]


def trending_tags(bodies, window_hours, limit=10):
    """(tag, count) pairs for hashtags mentioned at least trending_min_mentions(window_hours) times."""
    counts = Counter(tag for body in bodies for tag in markup.hashtags(body))
    floor = rules.trending_min_mentions(window_hours)
    hot = [(tag, n) for tag, n in counts.items() if n >= floor]
    hot.sort(key=lambda pair: (-pair[1], pair[0]))
    return hot[:limit]
