import unittest

from socialkit import ranking, rules


class EngagementTests(unittest.TestCase):
    def test_points_follow_the_policy_weights(self):
        for hours in (0, 3, 12, 48):
            expected = 2 * rules.like_weight_points(hours) + 3 * rules.reply_weight_points(hours)
            self.assertEqual(ranking.engagement_points(2, 3, hours), expected)

    def test_age_is_floored_to_whole_hours(self):
        self.assertEqual(ranking.engagement_points(1, 0, 5.9), rules.like_weight_points(5))
        self.assertEqual(ranking.engagement_points(1, 0, -2), rules.like_weight_points(0))

    def test_no_engagement_scores_zero(self):
        self.assertEqual(ranking.score(ranking.Candidate(1, 3.0, 0, 0)), 0)


class RankTests(unittest.TestCase):
    def test_more_engagement_ranks_first(self):
        a = ranking.Candidate(1, 0.5, 1, 0)
        b = ranking.Candidate(2, 0.5, 5, 0)
        self.assertEqual(ranking.rank([a, b]), [2, 1])

    def test_ties_prefer_the_newer_update(self):
        older = ranking.Candidate(1, 0.8, 2, 0)
        newer = ranking.Candidate(2, 0.2, 2, 0)
        self.assertEqual(ranking.rank([older, newer]), [2, 1])

    def test_final_tie_prefers_the_higher_id(self):
        a, b = ranking.Candidate(3, 0.5, 0, 0), ranking.Candidate(8, 0.5, 0, 0)
        self.assertEqual(ranking.rank([a, b]), [8, 3])

    def test_replies_and_likes_are_ordered_by_their_weights(self):
        liked = ranking.Candidate(1, 0.5, 1, 0)
        replied = ranking.Candidate(2, 0.5, 0, 1)
        like_w, reply_w = rules.like_weight_points(0), rules.reply_weight_points(0)
        expected = [1, 2] if like_w > reply_w else [2, 1]
        self.assertEqual(ranking.rank([liked, replied]), expected)


class FreshnessTests(unittest.TestCase):
    def test_window_edges(self):
        window = rules.freshness_window_hours(50)
        self.assertTrue(ranking.is_fresh(window, 50))
        self.assertFalse(ranking.is_fresh(window + 0.5, 50))

    def test_bigger_accounts_stay_fresh_at_least_as_long(self):
        self.assertTrue(rules.freshness_window_hours(20000) >= rules.freshness_window_hours(10))


class TrendingTests(unittest.TestCase):
    def test_tags_need_the_policy_minimum(self):
        floor = rules.trending_min_mentions(1)
        bodies = ["morning #lakeside run"] * floor + ["#quiet corner"] * (floor - 1)
        self.assertEqual(ranking.trending_tags(bodies, 1), [("lakeside", floor)])

    def test_order_is_by_count_then_name_and_limited(self):
        floor = rules.trending_min_mentions(1)
        bodies = ["#aaa"] * (floor + 2) + ["#bbb"] * (floor + 1) + ["#ccc"] * floor + ["#abc"] * floor
        self.assertEqual(ranking.trending_tags(bodies, 1, limit=3), [("aaa", floor + 2), ("bbb", floor + 1), ("abc", floor)])

    def test_repeated_tag_in_one_body_counts_once(self):
        floor = rules.trending_min_mentions(1)
        self.assertEqual(ranking.trending_tags(["#aaa #aaa #aaa"] * (floor - 1), 1), [])
