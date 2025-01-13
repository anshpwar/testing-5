import datetime as dt

from django.conf import settings
from django.db import transaction
from django.db.models import F

from follows import services as follow_services
from profiles import services as profile_services
from socialkit import pagination, quota, ranking, rules, screening

from .models import Like, Update

DAY = dt.timedelta(days=1)


class PostError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class TimelinePage:
    def __init__(self, items, next_cursor):
        self.items = items
        self.next_cursor = next_cursor


def _day_bounds(now):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + DAY


def posts_today(author, now, replies=False):
    start, end = _day_bounds(now)
    qs = Update.objects.filter(author=author, created_at__gte=start, created_at__lt=end)
    return qs.filter(parent__isnull=not replies).count()


def publish(author, body, now, parent=None):
    """Create an update or a reply. Raises PostError with a machine-readable code when it is not allowed."""
    text = (body or "").strip()
    if not text:
        raise PostError("empty")
    reason = profile_services.posting_block(author, now)
    if reason:
        raise PostError(reason)
    age = profile_services.age_days(author, now.date())
    if len(text) > rules.post_length_limit(age):
        raise PostError("too_long")
    is_reply = parent is not None
    limit = rules.daily_reply_limit(age) if is_reply else rules.daily_post_limit(age)
    try:
        quota.require(limit, posts_today(author, now, replies=is_reply))
    except quota.QuotaExceeded:
        raise PostError("daily_limit")
    if "blocked_term" in screening.flags(text):
        raise PostError("blocked_term")
    if is_reply and parent.hidden:
        raise PostError("hidden")
    with transaction.atomic():
        update = Update.objects.create(author=author, body=text, created_at=now, parent=parent)
        if is_reply:
            Update.objects.filter(pk=parent.pk).update(reply_count=F("reply_count") + 1)
    return update


def like(profile, update):
    """Like an update once; returns True when a new like was recorded."""
    if update.hidden:
        raise PostError("hidden")
    with transaction.atomic():
        _, created = Like.objects.get_or_create(profile=profile, update=update)
        if created:
            Update.objects.filter(pk=update.pk).update(like_count=F("like_count") + 1)
    update.refresh_from_db(fields=["like_count"])
    return created


def unlike(profile, update):
    with transaction.atomic():
        deleted, _ = Like.objects.filter(profile=profile, update=update).delete()
        if deleted:
            Update.objects.filter(pk=update.pk).update(like_count=F("like_count") - 1)
    update.refresh_from_db(fields=["like_count"])
    return bool(deleted)


def liked_ids(profile, updates):
    return set(Like.objects.filter(profile=profile, update__in=updates).values_list("update_id", flat=True))


def timeline(profile, now, cursor=None, size=None):
    """Ranked page of updates from the profiles this profile follows (and its own), freshest and most engaged first."""
    visible = set(follow_services.following_ids(profile)) | {profile.pk}
    visible -= follow_services.blocked_ids(profile)
    since = now - dt.timedelta(days=getattr(settings, "TIMELINE_LOOKBACK_DAYS", 30))
    rows = list(Update.objects.filter(author_id__in=visible, parent__isnull=True, hidden=False,
                                      created_at__gte=since, created_at__lte=now).select_related("author"))
    candidates = []
    for row in rows:
        age = (now - row.created_at).total_seconds() / 3600
        if ranking.is_fresh(age, row.author.follower_count):
            candidates.append(ranking.Candidate(row.pk, age, row.like_count, row.reply_count))
    by_id = {row.pk: row for row in rows}
    chunk, next_cursor = pagination.page(ranking.rank(candidates), cursor, size or rules.feed_page_size(profile.following_count))
    return TimelinePage([by_id[pk] for pk in chunk], next_cursor)


def replies_for(update):
    return list(update.replies.filter(hidden=False).select_related("author").order_by("created_at", "id"))


def trending(now, window_hours=24):
    since = now - dt.timedelta(hours=window_hours)
    bodies = Update.objects.filter(created_at__gte=since, created_at__lte=now, hidden=False).values_list("body", flat=True)
    return ranking.trending_tags(bodies, window_hours)
