from collections import Counter

from django.db import transaction
from django.db.models import F

from profiles import services as profile_services
from profiles.models import Profile
from socialkit import rules

from .models import Block, Follow


class FollowError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _adjust_counts(follower, followee, delta):
    Profile.objects.filter(pk=follower.pk).update(following_count=F("following_count") + delta)
    Profile.objects.filter(pk=followee.pk).update(follower_count=F("follower_count") + delta)
    follower.refresh_from_db(fields=["following_count"])
    followee.refresh_from_db(fields=["follower_count"])


def is_blocked(a, b):
    """True when either profile has blocked the other."""
    return Block.objects.filter(blocker=a, blocked=b).exists() or Block.objects.filter(blocker=b, blocked=a).exists()


def follows_today(follower, today):
    return Follow.objects.filter(follower=follower, created_on=today).count()


def follow(follower, followee, today):
    """Start following; returns False when the follow already existed. Raises FollowError otherwise on a violation."""
    if follower.pk == followee.pk:
        raise FollowError("self_follow")
    if is_blocked(follower, followee):
        raise FollowError("blocked")
    if Follow.objects.filter(follower=follower, followee=followee).exists():
        return False
    age = profile_services.age_days(follower, today)
    if follows_today(follower, today) >= rules.follow_limit_per_day(age):
        raise FollowError("daily_limit")
    if follower.following_count >= rules.max_following(follower.follower_count):
        raise FollowError("following_cap")
    with transaction.atomic():
        Follow.objects.create(follower=follower, followee=followee, created_on=today)
        _adjust_counts(follower, followee, 1)
    return True


def unfollow(follower, followee):
    deleted, _ = Follow.objects.filter(follower=follower, followee=followee).delete()
    if deleted:
        _adjust_counts(follower, followee, -1)
    return bool(deleted)


def block(blocker, blocked, today):
    """Block a profile and drop the follows in both directions."""
    if blocker.pk == blocked.pk:
        raise FollowError("self_block")
    with transaction.atomic():
        _, created = Block.objects.get_or_create(blocker=blocker, blocked=blocked, defaults={"created_on": today})
        unfollow(blocker, blocked)
        unfollow(blocked, blocker)
    return created


def following_ids(profile):
    return list(Follow.objects.filter(follower=profile).values_list("followee_id", flat=True))


def follower_ids(profile):
    return list(Follow.objects.filter(followee=profile).values_list("follower_id", flat=True))


def blocked_ids(profile):
    """Profiles whose updates this profile must not see: ones it blocked and ones that blocked it."""
    mine = Block.objects.filter(blocker=profile).values_list("blocked_id", flat=True)
    theirs = Block.objects.filter(blocked=profile).values_list("blocker_id", flat=True)
    return set(mine) | set(theirs)


def mutuals(profile):
    return sorted(set(following_ids(profile)) & set(follower_ids(profile)))


def suggestions(profile, limit=5):
    """Profiles followed by the people this profile follows, most shared first, never already followed or blocked."""
    mine = set(following_ids(profile))
    excluded = mine | blocked_ids(profile) | {profile.pk}
    counts = Counter()
    for other in mine:
        for candidate in Follow.objects.filter(follower_id=other).values_list("followee_id", flat=True):
            if candidate not in excluded:
                counts[candidate] += 1
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return [pk for pk, _ in ranked[:limit]]
