import unittest

from socialkit import rules


class RuleTests(unittest.TestCase):
    def test_daily_post_limit(self):
        self.assertEqual(rules.daily_post_limit(0), 3)
        self.assertEqual(rules.daily_post_limit(1), 3)
        self.assertEqual(rules.daily_post_limit(2), 10)
        self.assertEqual(rules.daily_post_limit(7), 10)
        self.assertEqual(rules.daily_post_limit(8), 30)
        self.assertEqual(rules.daily_post_limit(30), 30)
        self.assertEqual(rules.daily_post_limit(31), 100)

    def test_daily_reply_limit(self):
        self.assertEqual(rules.daily_reply_limit(0), 10)
        self.assertEqual(rules.daily_reply_limit(1), 10)
        self.assertEqual(rules.daily_reply_limit(2), 50)
        self.assertEqual(rules.daily_reply_limit(7), 50)
        self.assertEqual(rules.daily_reply_limit(8), 150)
        self.assertEqual(rules.daily_reply_limit(30), 150)
        self.assertEqual(rules.daily_reply_limit(31), 400)

    def test_follow_limit_per_day(self):
        self.assertEqual(rules.follow_limit_per_day(0), 20)
        self.assertEqual(rules.follow_limit_per_day(1), 20)
        self.assertEqual(rules.follow_limit_per_day(2), 100)
        self.assertEqual(rules.follow_limit_per_day(7), 100)
        self.assertEqual(rules.follow_limit_per_day(8), 250)
        self.assertEqual(rules.follow_limit_per_day(30), 250)
        self.assertEqual(rules.follow_limit_per_day(31), 1000)

    def test_max_following(self):
        self.assertEqual(rules.max_following(0), 500)
        self.assertEqual(rules.max_following(1), 500)
        self.assertEqual(rules.max_following(100), 500)
        self.assertEqual(rules.max_following(101), 500)
        self.assertEqual(rules.max_following(1000), 2000)
        self.assertEqual(rules.max_following(1001), 2000)
        self.assertEqual(rules.max_following(10000), 5000)
        self.assertEqual(rules.max_following(10001), 5000)

    def test_post_length_limit(self):
        self.assertEqual(rules.post_length_limit(0), 140)
        self.assertEqual(rules.post_length_limit(1), 140)
        self.assertEqual(rules.post_length_limit(2), 140)
        self.assertEqual(rules.post_length_limit(30), 280)
        self.assertEqual(rules.post_length_limit(31), 280)
        self.assertEqual(rules.post_length_limit(180), 500)
        self.assertEqual(rules.post_length_limit(181), 500)

    def test_feed_page_size(self):
        self.assertEqual(rules.feed_page_size(0), 22)
        self.assertEqual(rules.feed_page_size(1), 22)
        self.assertEqual(rules.feed_page_size(10), 22)
        self.assertEqual(rules.feed_page_size(11), 33)
        self.assertEqual(rules.feed_page_size(100), 33)
        self.assertEqual(rules.feed_page_size(101), 55)
        self.assertEqual(rules.feed_page_size(1000), 55)
        self.assertEqual(rules.feed_page_size(1001), 110)

    def test_like_weight_points(self):
        self.assertEqual(rules.like_weight_points(0), 11)
        self.assertEqual(rules.like_weight_points(1), 11)
        self.assertEqual(rules.like_weight_points(2), 7)
        self.assertEqual(rules.like_weight_points(6), 7)
        self.assertEqual(rules.like_weight_points(7), 4)
        self.assertEqual(rules.like_weight_points(24), 4)
        self.assertEqual(rules.like_weight_points(25), 3)

    def test_reply_weight_points(self):
        self.assertEqual(rules.reply_weight_points(0), 25)
        self.assertEqual(rules.reply_weight_points(1), 25)
        self.assertEqual(rules.reply_weight_points(2), 15)
        self.assertEqual(rules.reply_weight_points(6), 15)
        self.assertEqual(rules.reply_weight_points(7), 8)
        self.assertEqual(rules.reply_weight_points(24), 8)
        self.assertEqual(rules.reply_weight_points(25), 3)

    def test_freshness_window_hours(self):
        self.assertEqual(rules.freshness_window_hours(0), 24)
        self.assertEqual(rules.freshness_window_hours(1), 24)
        self.assertEqual(rules.freshness_window_hours(100), 24)
        self.assertEqual(rules.freshness_window_hours(101), 48)
        self.assertEqual(rules.freshness_window_hours(1000), 48)
        self.assertEqual(rules.freshness_window_hours(1001), 96)
        self.assertEqual(rules.freshness_window_hours(10000), 96)
        self.assertEqual(rules.freshness_window_hours(10001), 168)

    def test_report_auto_hide_threshold(self):
        self.assertEqual(rules.report_auto_hide_threshold(0), 3)
        self.assertEqual(rules.report_auto_hide_threshold(1), 3)
        self.assertEqual(rules.report_auto_hide_threshold(100), 3)
        self.assertEqual(rules.report_auto_hide_threshold(101), 5)
        self.assertEqual(rules.report_auto_hide_threshold(1000), 5)
        self.assertEqual(rules.report_auto_hide_threshold(1001), 10)
        self.assertEqual(rules.report_auto_hide_threshold(10000), 10)
        self.assertEqual(rules.report_auto_hide_threshold(10001), 25)

    def test_mute_duration_hours(self):
        self.assertEqual(rules.mute_duration_hours(0), 24)
        self.assertEqual(rules.mute_duration_hours(1), 24)
        self.assertEqual(rules.mute_duration_hours(2), 72)
        self.assertEqual(rules.mute_duration_hours(3), 168)
        self.assertEqual(rules.mute_duration_hours(4), 720)

    def test_suspension_days(self):
        self.assertEqual(rules.suspension_days(0), 0)
        self.assertEqual(rules.suspension_days(1), 0)
        self.assertEqual(rules.suspension_days(2), 3)
        self.assertEqual(rules.suspension_days(3), 14)
        self.assertEqual(rules.suspension_days(4), 14)
        self.assertEqual(rules.suspension_days(5), 90)

    def test_report_cooldown_minutes(self):
        self.assertEqual(rules.report_cooldown_minutes(0), 0)
        self.assertEqual(rules.report_cooldown_minutes(1), 0)
        self.assertEqual(rules.report_cooldown_minutes(3), 0)
        self.assertEqual(rules.report_cooldown_minutes(4), 15)
        self.assertEqual(rules.report_cooldown_minutes(10), 15)
        self.assertEqual(rules.report_cooldown_minutes(11), 60)
        self.assertEqual(rules.report_cooldown_minutes(25), 60)
        self.assertEqual(rules.report_cooldown_minutes(26), 1440)

    def test_media_size_limit_kb(self):
        self.assertEqual(rules.media_size_limit_kb(0), 512)
        self.assertEqual(rules.media_size_limit_kb(1), 512)
        self.assertEqual(rules.media_size_limit_kb(7), 512)
        self.assertEqual(rules.media_size_limit_kb(8), 2048)
        self.assertEqual(rules.media_size_limit_kb(30), 2048)
        self.assertEqual(rules.media_size_limit_kb(31), 8192)
        self.assertEqual(rules.media_size_limit_kb(180), 8192)
        self.assertEqual(rules.media_size_limit_kb(181), 20480)

    def test_verified_follower_floor(self):
        self.assertEqual(rules.verified_follower_floor(0), 500)
        self.assertEqual(rules.verified_follower_floor(1), 500)
        self.assertEqual(rules.verified_follower_floor(30), 500)
        self.assertEqual(rules.verified_follower_floor(31), 1000)
        self.assertEqual(rules.verified_follower_floor(180), 1000)
        self.assertEqual(rules.verified_follower_floor(181), 5000)
        self.assertEqual(rules.verified_follower_floor(365), 5000)
        self.assertEqual(rules.verified_follower_floor(366), 10000)

    def test_trending_min_mentions(self):
        self.assertEqual(rules.trending_min_mentions(0), 50)
        self.assertEqual(rules.trending_min_mentions(1), 50)
        self.assertEqual(rules.trending_min_mentions(2), 200)
        self.assertEqual(rules.trending_min_mentions(6), 200)
        self.assertEqual(rules.trending_min_mentions(7), 800)
        self.assertEqual(rules.trending_min_mentions(24), 800)
        self.assertEqual(rules.trending_min_mentions(25), 2000)
