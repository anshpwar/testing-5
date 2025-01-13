import datetime as dt

from django.test import TestCase

from follows import services
from follows.models import Block, Follow
from socialkit import rules

from . import factories as f


class FollowTests(TestCase):
    def setUp(self):
        self.ann, self.bob = f.profile("ann_a"), f.profile("bob_b")

    def counts(self, profile):
        profile.refresh_from_db()
        return profile.follower_count, profile.following_count

    def test_follow_updates_both_counters(self):
        self.assertTrue(services.follow(self.ann, self.bob, f.TODAY))
        self.assertEqual(self.counts(self.ann), (0, 1))
        self.assertEqual(self.counts(self.bob), (1, 0))

    def test_following_twice_is_idempotent(self):
        services.follow(self.ann, self.bob, f.TODAY)
        self.assertFalse(services.follow(self.ann, self.bob, f.TODAY))
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(self.counts(self.bob), (1, 0))

    def test_cannot_follow_yourself(self):
        with self.assertRaises(services.FollowError) as caught:
            services.follow(self.ann, self.ann, f.TODAY)
        self.assertEqual(caught.exception.code, "self_follow")

    def test_unfollow(self):
        services.follow(self.ann, self.bob, f.TODAY)
        self.assertTrue(services.unfollow(self.ann, self.bob))
        self.assertFalse(services.unfollow(self.ann, self.bob))
        self.assertEqual(self.counts(self.bob), (0, 0))

    def test_daily_limit_for_a_new_account(self):
        rookie = f.newcomer()
        limit = rules.follow_limit_per_day(0)
        targets = f.many_profiles(limit + 1)
        for target in targets[:limit]:
            services.follow(rookie, target, f.TODAY)
        with self.assertRaises(services.FollowError) as caught:
            services.follow(rookie, targets[limit], f.TODAY)
        self.assertEqual(caught.exception.code, "daily_limit")
        self.assertEqual(services.follows_today(rookie, f.TODAY), limit)

    def test_limit_resets_on_the_next_day(self):
        rookie = f.newcomer()
        limit = rules.follow_limit_per_day(0)
        targets = f.many_profiles(limit + 1)
        for target in targets[:limit]:
            services.follow(rookie, target, f.TODAY)
        tomorrow = f.TODAY + dt.timedelta(days=1)
        self.assertTrue(services.follow(rookie, targets[limit], tomorrow))
        self.assertEqual(Follow.objects.filter(follower=rookie).count(), limit + 1)

    def test_following_cap_depends_on_followers(self):
        self.ann.following_count = rules.max_following(self.ann.follower_count)
        self.ann.save()
        with self.assertRaises(services.FollowError) as caught:
            services.follow(self.ann, self.bob, f.TODAY)
        self.assertEqual(caught.exception.code, "following_cap")


class BlockTests(TestCase):
    def setUp(self):
        self.ann, self.bob, self.cy = f.profile("ann_a"), f.profile("bob_b"), f.profile("cy_cc")

    def test_block_drops_follows_in_both_directions(self):
        services.follow(self.ann, self.bob, f.TODAY)
        services.follow(self.bob, self.ann, f.TODAY)
        self.assertTrue(services.block(self.ann, self.bob, f.TODAY))
        self.assertFalse(services.block(self.ann, self.bob, f.TODAY))
        self.assertEqual(Follow.objects.count(), 0)
        self.assertEqual(Block.objects.count(), 1)
        self.ann.refresh_from_db()
        self.assertEqual((self.ann.follower_count, self.ann.following_count), (0, 0))

    def test_blocked_pairs_cannot_follow_either_way(self):
        services.block(self.ann, self.bob, f.TODAY)
        for a, b in ((self.ann, self.bob), (self.bob, self.ann)):
            with self.assertRaises(services.FollowError) as caught:
                services.follow(a, b, f.TODAY)
            self.assertEqual(caught.exception.code, "blocked")

    def test_blocked_ids_cover_both_directions(self):
        services.block(self.ann, self.bob, f.TODAY)
        services.block(self.cy, self.ann, f.TODAY)
        self.assertEqual(services.blocked_ids(self.ann), {self.bob.pk, self.cy.pk})
        self.assertEqual(services.blocked_ids(self.bob), {self.ann.pk})


class GraphTests(TestCase):
    def setUp(self):
        self.a, self.b, self.c, self.d, self.e = (f.profile(h) for h in ("aaa_a", "bbb_b", "ccc_c", "ddd_d", "eee_e"))
        for follower, followee in ((self.a, self.b), (self.a, self.c), (self.b, self.d), (self.b, self.e), (self.c, self.d), (self.b, self.a)):
            services.follow(follower, followee, f.TODAY)

    def test_follower_and_following_lists(self):
        self.assertEqual(sorted(services.following_ids(self.a)), sorted([self.b.pk, self.c.pk]))
        self.assertEqual(sorted(services.follower_ids(self.d)), sorted([self.b.pk, self.c.pk]))

    def test_mutuals(self):
        self.assertEqual(services.mutuals(self.a), [self.b.pk])

    def test_suggestions_rank_by_shared_follows(self):
        self.assertEqual(services.suggestions(self.a), [self.d.pk, self.e.pk])
        self.assertEqual(services.suggestions(self.a, limit=1), [self.d.pk])

    def test_suggestions_skip_blocked_profiles(self):
        services.block(self.a, self.d, f.TODAY)
        self.assertEqual(services.suggestions(self.a), [self.e.pk])
