import datetime as dt

from django.test import TestCase

from profiles import services
from profiles.models import Profile
from socialkit import rules

from . import factories as f


class RegisterTests(TestCase):
    def test_register_normalises_the_handle(self):
        profile = services.register("@Marisol_V", "  Marisol Vega ", f.TODAY, bio=" trail runner ")
        self.assertEqual((profile.handle, profile.display_name, profile.bio), ("marisol_v", "Marisol Vega", "trail runner"))
        self.assertEqual(str(profile), "@marisol_v")

    def test_register_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            services.register("no", "Short", f.TODAY)
        with self.assertRaisesRegex(ValueError, "display name"):
            services.register("valid_one", "   ", f.TODAY)
        with self.assertRaisesRegex(ValueError, "bio"):
            services.register("valid_two", "Name", f.TODAY, bio="x" * (services.BIO_LIMIT + 1))

    def test_register_rejects_duplicates_case_insensitively(self):
        services.register("tobias_k", "Tobias", f.TODAY)
        with self.assertRaisesRegex(ValueError, "taken"):
            services.register("Tobias_K", "Another Tobias", f.TODAY)
        self.assertEqual(Profile.objects.count(), 1)


class StateTests(TestCase):
    def test_age_days(self):
        self.assertEqual(services.age_days(f.profile("aged", joined=dt.date(2025, 2, 21)), f.TODAY), 10)
        self.assertEqual(services.age_days(f.newcomer(), f.TODAY), 0)

    def test_posting_block_reports_the_active_restriction(self):
        muted = f.profile("muted_one", muted_until=f.NOW + dt.timedelta(hours=1))
        suspended = f.profile("susp_one", suspended_until=f.NOW + dt.timedelta(days=2), muted_until=f.NOW + dt.timedelta(hours=1))
        self.assertEqual(services.posting_block(muted, f.NOW), "muted")
        self.assertEqual(services.posting_block(suspended, f.NOW), "suspended")

    def test_posting_block_ends_at_the_expiry_instant(self):
        profile = f.profile("expiring", muted_until=f.NOW)
        self.assertIsNone(services.posting_block(profile, f.NOW))
        self.assertIsNone(services.posting_block(f.profile("free_one"), f.NOW))


class VerificationTests(TestCase):
    def test_status_compares_followers_with_the_floor(self):
        profile = f.newcomer()
        needed = rules.verified_follower_floor(0)
        self.assertEqual(services.verification_status(profile, f.TODAY), {"followers": 0, "needed": needed, "eligible": False})
        profile.follower_count = needed
        self.assertTrue(services.verification_status(profile, f.TODAY)["eligible"])

    def test_apply_verification_only_flips_eligible_profiles(self):
        profile = f.newcomer()
        services.apply_verification(profile, f.TODAY)
        profile.refresh_from_db()
        self.assertFalse(profile.verified)
        profile.follower_count = rules.verified_follower_floor(0)
        profile.save()
        services.apply_verification(profile, f.TODAY)
        profile.refresh_from_db()
        self.assertTrue(profile.verified)


class LimitsTests(TestCase):
    def test_limits_mirror_the_policy_tables(self):
        profile = f.profile("limited", joined=dt.date(2025, 2, 21), follower_count=150)
        self.assertEqual(services.limits(profile, f.TODAY), {
            "post_length": rules.post_length_limit(10),
            "posts_per_day": rules.daily_post_limit(10),
            "replies_per_day": rules.daily_reply_limit(10),
            "follows_per_day": rules.follow_limit_per_day(10),
            "max_following": rules.max_following(150),
            "media_kb": rules.media_size_limit_kb(10),
        })

    def test_summary(self):
        profile = f.profile("summed", joined=dt.date(2025, 3, 1), follower_count=2, following_count=3)
        self.assertEqual(services.summary(profile, f.TODAY), {
            "handle": "summed", "display_name": "Summed", "bio": "", "verified": False,
            "followers": 2, "following": 3, "age_days": 2,
        })
