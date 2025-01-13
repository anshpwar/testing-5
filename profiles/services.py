from django.db import IntegrityError, transaction

from socialkit import handles, quota, rules

from .models import Profile

BIO_LIMIT = 160


def register(handle, display_name, joined_on, bio=""):
    """Create a profile. Raises ValueError for a bad or taken handle, a blank name or an over-long bio."""
    normal = handles.validate(handle)
    name = display_name.strip()
    if not name:
        raise ValueError("display name required")
    if len(bio) > BIO_LIMIT:
        raise ValueError("bio too long")
    try:
        with transaction.atomic():
            return Profile.objects.create(handle=normal, display_name=name, bio=bio.strip(), joined_on=joined_on)
    except IntegrityError:
        raise ValueError("handle taken")


def age_days(profile, today):
    return quota.age_in_days(profile.joined_on, today)


def posting_block(profile, now):
    """Why this profile cannot post right now ("suspended" or "muted"), or None."""
    if profile.suspended_until and profile.suspended_until > now:
        return "suspended"
    if profile.muted_until and profile.muted_until > now:
        return "muted"
    return None


def verification_status(profile, today):
    needed = rules.verified_follower_floor(age_days(profile, today))
    return {"followers": profile.follower_count, "needed": needed, "eligible": profile.follower_count >= needed}


def apply_verification(profile, today):
    status = verification_status(profile, today)
    if status["eligible"] and not profile.verified:
        profile.verified = True
        profile.save(update_fields=["verified"])
    return status


def limits(profile, today):
    """The allowances the clients show to the user, keyed for the JSON API."""
    age = age_days(profile, today)
    return {
        "post_length": rules.post_length_limit(age),
        "posts_per_day": rules.daily_post_limit(age),
        "replies_per_day": rules.daily_reply_limit(age),
        "follows_per_day": rules.follow_limit_per_day(age),
        "max_following": rules.max_following(profile.follower_count),
        "media_kb": rules.media_size_limit_kb(age),
    }


def summary(profile, today):
    return {
        "handle": profile.handle,
        "display_name": profile.display_name,
        "bio": profile.bio,
        "verified": profile.verified,
        "followers": profile.follower_count,
        "following": profile.following_count,
        "age_days": age_days(profile, today),
    }
