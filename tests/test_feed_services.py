import datetime as dt

from django.test import TestCase

from feed import services
from feed.models import Like, Update
from follows import services as follow_services
from profiles import services as profile_services
from socialkit import rules

from . import factories as f


class PublishTests(TestCase):
    def setUp(self):
        self.rookie = f.newcomer()

    def test_publish_strips_and_stores(self):
        update = services.publish(self.rookie, "  first words  ", f.NOW)
        self.assertEqual((update.body, update.created_at, update.parent), ("first words", f.NOW, None))

    def test_empty_body_is_rejected(self):
        for body in ("", "   ", None):
            with self.assertRaises(services.PostError) as caught:
                services.publish(self.rookie, body, f.NOW)
            self.assertEqual(caught.exception.code, "empty")

    def test_length_limit_boundary(self):
        limit = rules.post_length_limit(0)
        self.assertTrue(services.publish(self.rookie, "a" * limit, f.NOW).pk)
        with self.assertRaises(services.PostError) as caught:
            services.publish(self.rookie, "a" * (limit + 1), f.NOW + dt.timedelta(minutes=1))
        self.assertEqual(caught.exception.code, "too_long")

    def test_older_accounts_may_write_longer_updates(self):
        veteran = f.profile("veteran_x", joined=dt.date(2024, 6, 1))
        longest_new = rules.post_length_limit(0)
        self.assertGreaterEqual(rules.post_length_limit(profile_services.age_days(veteran, f.TODAY)), longest_new)

    def test_daily_post_limit(self):
        limit = rules.daily_post_limit(0)
        Update.objects.bulk_create([Update(author=self.rookie, body=f"p{i}", created_at=f.NOW - dt.timedelta(minutes=i + 1)) for i in range(limit)])
        with self.assertRaises(services.PostError) as caught:
            services.publish(self.rookie, "one too many", f.NOW)
        self.assertEqual(caught.exception.code, "daily_limit")

    def test_the_limit_is_per_day(self):
        limit = rules.daily_post_limit(0)
        yesterday = f.NOW - dt.timedelta(days=1)
        Update.objects.bulk_create([Update(author=self.rookie, body=f"p{i}", created_at=yesterday) for i in range(limit)])
        self.assertTrue(services.publish(self.rookie, "fresh day", f.NOW).pk)

    def test_replies_have_their_own_allowance(self):
        parent = f.update(f.profile("poster_z"))
        limit = rules.daily_post_limit(0)
        Update.objects.bulk_create([Update(author=self.rookie, body=f"p{i}", created_at=f.NOW - dt.timedelta(minutes=i + 1)) for i in range(limit)])
        reply = services.publish(self.rookie, "still allowed to reply", f.NOW, parent=parent)
        self.assertEqual(reply.parent_id, parent.pk)
        parent.refresh_from_db()
        self.assertEqual(parent.reply_count, 1)

    def test_muted_and_suspended_accounts_cannot_post(self):
        muted = f.profile("muted_q", muted_until=f.NOW + dt.timedelta(hours=1))
        suspended = f.profile("susp_q", suspended_until=f.NOW + dt.timedelta(days=1))
        for who, code in ((muted, "muted"), (suspended, "suspended")):
            with self.assertRaises(services.PostError) as caught:
                services.publish(who, "hello", f.NOW)
            self.assertEqual(caught.exception.code, code)

    def test_blocked_terms_are_refused(self):
        with self.assertRaises(services.PostError) as caught:
            services.publish(self.rookie, "click-here-to-win a prize", f.NOW)
        self.assertEqual(caught.exception.code, "blocked_term")

    def test_cannot_reply_to_a_hidden_update(self):
        hidden = f.update(f.profile("poster_h"), hidden=True)
        with self.assertRaises(services.PostError) as caught:
            services.publish(self.rookie, "hi", f.NOW, parent=hidden)
        self.assertEqual(caught.exception.code, "hidden")


class LikeTests(TestCase):
    def setUp(self):
        self.author, self.fan = f.profile("author_l"), f.profile("fan_ll")
        self.update = f.update(self.author)

    def test_like_is_recorded_once(self):
        self.assertTrue(services.like(self.fan, self.update))
        self.assertFalse(services.like(self.fan, self.update))
        self.assertEqual((Like.objects.count(), self.update.like_count), (1, 1))

    def test_unlike(self):
        services.like(self.fan, self.update)
        self.assertTrue(services.unlike(self.fan, self.update))
        self.assertFalse(services.unlike(self.fan, self.update))
        self.assertEqual(self.update.like_count, 0)

    def test_hidden_updates_cannot_be_liked(self):
        self.update.hidden = True
        with self.assertRaises(services.PostError):
            services.like(self.fan, self.update)

    def test_liked_ids(self):
        other = f.update(self.author, "second")
        services.like(self.fan, other)
        self.assertEqual(services.liked_ids(self.fan, [self.update, other]), {other.pk})


class TimelineTests(TestCase):
    def setUp(self):
        self.viewer = f.profile("viewer_t")
        self.friend = f.profile("friend_t")
        self.stranger = f.profile("stranger_t")
        follow_services.follow(self.viewer, self.friend, f.TODAY)
        self.viewer.refresh_from_db()

    def ids(self, page):
        return [u.pk for u in page.items]

    def test_includes_followed_and_own_updates_only(self):
        mine = f.update(self.viewer, "mine", ago_minutes=10)
        theirs = f.update(self.friend, "theirs", ago_minutes=20)
        f.update(self.stranger, "unrelated", ago_minutes=5)
        self.assertEqual(sorted(self.ids(services.timeline(self.viewer, f.NOW))), sorted([mine.pk, theirs.pk]))

    def test_hidden_replies_and_future_updates_are_left_out(self):
        shown = f.update(self.friend, "shown")
        f.update(self.friend, "hidden", hidden=True)
        f.update(self.friend, "reply", parent=shown)
        f.update(self.friend, "from the future", ago_minutes=-30)
        self.assertEqual(self.ids(services.timeline(self.viewer, f.NOW)), [shown.pk])

    def test_stale_updates_expire_with_the_authors_freshness_window(self):
        window = rules.freshness_window_hours(self.friend.follower_count)
        fresh = f.update(self.friend, "fresh", ago_minutes=int(window * 60) - 30)
        f.update(self.friend, "stale", ago_minutes=int(window * 60) + 30)
        self.assertEqual(self.ids(services.timeline(self.viewer, f.NOW)), [fresh.pk])

    def test_blocked_authors_disappear(self):
        f.update(self.friend, "gone soon")
        follow_services.block(self.viewer, self.friend, f.TODAY)
        self.assertEqual(self.ids(services.timeline(self.viewer, f.NOW)), [])

    def test_engagement_orders_the_page(self):
        quiet = f.update(self.friend, "quiet", ago_minutes=30)
        loud = f.update(self.friend, "loud", ago_minutes=40, like_count=9)
        self.assertEqual(self.ids(services.timeline(self.viewer, f.NOW)), [loud.pk, quiet.pk])

    def test_pages_are_chained_by_cursor(self):
        made = [f.update(self.friend, f"u{i}", ago_minutes=10 + i) for i in range(5)]
        first = services.timeline(self.viewer, f.NOW, size=2)
        second = services.timeline(self.viewer, f.NOW, cursor=first.next_cursor, size=2)
        third = services.timeline(self.viewer, f.NOW, cursor=second.next_cursor, size=2)
        seen = self.ids(first) + self.ids(second) + self.ids(third)
        self.assertEqual(seen, [u.pk for u in made])
        self.assertIsNone(third.next_cursor)

    def test_default_page_size_comes_from_policy(self):
        size = rules.feed_page_size(self.viewer.following_count)
        Update.objects.bulk_create([Update(author=self.friend, body=f"b{i}", created_at=f.NOW - dt.timedelta(minutes=10 + i)) for i in range(size + 1)])
        page = services.timeline(self.viewer, f.NOW)
        self.assertEqual(len(page.items), size)
        self.assertIsNotNone(page.next_cursor)

    def test_bad_cursor_raises(self):
        with self.assertRaises(ValueError):
            services.timeline(self.viewer, f.NOW, cursor="!!")


class MiscTests(TestCase):
    def test_replies_for_skips_hidden_and_orders_oldest_first(self):
        author = f.profile("thread_a")
        root = f.update(author, "root", ago_minutes=100)
        late = f.update(author, "late", ago_minutes=10, parent=root)
        early = f.update(author, "early", ago_minutes=50, parent=root)
        f.update(author, "gone", ago_minutes=30, parent=root, hidden=True)
        self.assertEqual([u.pk for u in services.replies_for(root)], [early.pk, late.pk])
        self.assertNotIn("gone", [u.body for u in services.replies_for(root)])
        self.assertEqual(late.parent_id, root.pk)

    def test_trending_counts_recent_visible_updates(self):
        author = f.profile("tagger_a")
        floor = rules.trending_min_mentions(1)
        Update.objects.bulk_create([Update(author=author, body="out on the #lakeside", created_at=f.NOW - dt.timedelta(minutes=5)) for _ in range(floor)])
        Update.objects.bulk_create([Update(author=author, body="old #lakeside news", created_at=f.NOW - dt.timedelta(hours=3)) for _ in range(floor)])
        Update.objects.bulk_create([Update(author=author, body="hidden #spamtag", created_at=f.NOW - dt.timedelta(minutes=5), hidden=True) for _ in range(floor)])
        self.assertEqual(services.trending(f.NOW, window_hours=1), [("lakeside", floor)])
