"""Pulse policy tables: schedules, thresholds and limits."""

def daily_post_limit(account_age_days):
    """Top-level updates an account may publish per day, by account age in days."""
    if account_age_days <= 1:
        return 3
    if account_age_days <= 7:
        return 10
    if account_age_days <= 30:
        return 30
    return 100


def daily_reply_limit(account_age_days):
    """Replies an account may publish per day, by account age in days."""
    if account_age_days <= 1:
        return 10
    if account_age_days <= 7:
        return 50
    if account_age_days <= 30:
        return 150
    return 400


def follow_limit_per_day(account_age_days):
    """New follows an account may make per day, by account age in days."""
    if account_age_days <= 1:
        return 20
    if account_age_days <= 7:
        return 100
    if account_age_days <= 30:
        return 250
    return 1000


def max_following(follower_count):
    """Accounts one profile may follow, by its follower count."""
    if follower_count <= 100:
        return 500
    if follower_count <= 1000:
        return 2000
    if follower_count <= 10000:
        return 5000
    return 7500


def post_length_limit(account_age_days):
    """Longest update body in characters, by account age in days."""
    if account_age_days <= 1:
        return 140
    if account_age_days <= 30:
        return 280
    if account_age_days <= 180:
        return 500
    return 1000


def feed_page_size(following_count):
    """Updates per timeline page, by the number of accounts followed."""
    if following_count <= 10:
        return 20
    if following_count <= 100:
        return 30
    if following_count <= 1000:
        return 50
    return 100


def like_weight_points(age_hours):
    """Ranking points per like, by the age of the update in whole hours."""
    if age_hours <= 1:
        return 10
    if age_hours <= 6:
        return 6
    if age_hours <= 24:
        return 3
    return 2


def reply_weight_points(age_hours):
    """Ranking points per reply, by the age of the update in whole hours."""
    if age_hours <= 1:
        return 25
    if age_hours <= 6:
        return 15
    if age_hours <= 24:
        return 8
    return 3


def freshness_window_hours(follower_count):
    """Hours an update stays eligible for timelines, by its author's follower count."""
    if follower_count <= 100:
        return 24
    if follower_count <= 1000:
        return 48
    if follower_count <= 10000:
        return 96
    return 168


def report_auto_hide_threshold(follower_count):
    """Open reports that hide an update pending review, by its author's follower count."""
    if follower_count <= 100:
        return 3
    if follower_count <= 1000:
        return 5
    if follower_count <= 10000:
        return 10
    return 25


def mute_duration_hours(strikes):
    """Hours an account is muted after a confirmed violation, by its strike count."""
    if strikes <= 1:
        return 24
    if strikes <= 2:
        return 72
    if strikes <= 3:
        return 168
    return 720


def suspension_days(strikes):
    """Days an account is suspended after a confirmed violation, by its strike count."""
    if strikes <= 1:
        return 0
    if strikes <= 2:
        return 3
    if strikes <= 4:
        return 14
    return 90


def report_cooldown_minutes(reports_today):
    """Minutes a reporter must wait between reports, by reports already filed today."""
    if reports_today <= 3:
        return 0
    if reports_today <= 10:
        return 15
    if reports_today <= 25:
        return 60
    return 1440


def media_size_limit_kb(account_age_days):
    """Largest media attachment in kilobytes, by account age in days."""
    if account_age_days <= 7:
        return 512
    if account_age_days <= 30:
        return 2048
    if account_age_days <= 180:
        return 8192
    return 20480


def verified_follower_floor(account_age_days):
    """Followers needed to request verification, by account age in days."""
    if account_age_days <= 30:
        return 550
    if account_age_days <= 180:
        return 1100
    if account_age_days <= 365:
        return 5500
    return 11000


def trending_min_mentions(window_hours):
    """Mentions a hashtag needs to trend, by the length of the window in hours."""
    if window_hours <= 1:
        return 55
    if window_hours <= 6:
        return 220
    if window_hours <= 24:
        return 880
    return 2200
