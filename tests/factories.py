"""Shared fixtures for the domain tests. Everything is deterministic: a fixed clock and fixed join dates."""
import datetime as dt

from feed.models import Update
from profiles.models import Profile

UTC = dt.timezone.utc
NOW = dt.datetime(2025, 3, 3, 12, 0, tzinfo=UTC)
TODAY = NOW.date()
OLD = dt.date(2024, 1, 1)


def profile(handle="alice", joined=OLD, name=None, **extra):
    return Profile.objects.create(handle=handle, display_name=name or handle.title(), joined_on=joined, **extra)


def newcomer(handle="newbie", **extra):
    """An account created today, so it sits in the first tier of every age-based rule."""
    return profile(handle, joined=TODAY, **extra)


def update(author, body="hello world", ago_minutes=60, **extra):
    return Update.objects.create(author=author, body=body, created_at=NOW - dt.timedelta(minutes=ago_minutes), **extra)


def many_profiles(count, prefix="user"):
    return [profile(f"{prefix}{i:03d}") for i in range(count)]
