import unittest

from socialkit import rules, screening


class FlagTests(unittest.TestCase):
    def test_clean_text_has_no_flags(self):
        self.assertEqual(screening.flags("Lovely walk by the lake today"), [])

    def test_blocked_terms_are_case_insensitive(self):
        self.assertEqual(screening.flags("Visit BUY-FOLLOWERS-NOW today"), ["blocked_term"])

    def test_link_flood(self):
        text = " ".join(f"https://x{i}.example" for i in range(screening.MAX_LINKS + 1))
        self.assertEqual(screening.flags(text), ["link_flood"])
        self.assertEqual(screening.flags(" ".join(text.split()[:screening.MAX_LINKS])), [])

    def test_mention_flood(self):
        names = ["aaa", "bbb", "ccc", "ddd", "eee", "fff"]
        self.assertEqual(screening.flags(" ".join("@" + n for n in names)), ["mention_flood"])
        self.assertEqual(screening.flags(" ".join("@" + n for n in names[:screening.MAX_MENTIONS])), [])

    def test_shouting_needs_enough_letters(self):
        self.assertEqual(screening.flags("THIS IS ALL CAPS TEXT"), ["shouting"])
        self.assertEqual(screening.flags("HELLO"), [])
        self.assertEqual(screening.flags("This is Mostly lower case text"), [])

    def test_flags_come_in_a_fixed_order(self):
        links = " ".join(f"https://x{i}.example" for i in range(5))
        self.assertEqual(screening.flags("free-crypto-giveaway " + links), ["blocked_term", "link_flood"])
        self.assertEqual(screening.flags("FREE-CRYPTO-GIVEAWAY HURRY UP EVERYONE"), ["blocked_term", "shouting"])

    def test_severity_adds_up(self):
        self.assertEqual(screening.severity([]), 0)
        self.assertEqual(screening.severity(["blocked_term", "shouting"]), screening.SEVERITY["blocked_term"] + screening.SEVERITY["shouting"])


class EscalationTests(unittest.TestCase):
    def test_auto_hide_at_the_policy_threshold(self):
        threshold = rules.report_auto_hide_threshold(50)
        self.assertTrue(screening.should_auto_hide(threshold, 50))
        self.assertFalse(screening.should_auto_hide(threshold - 1, 50))

    def test_larger_accounts_need_at_least_as_many_reports(self):
        self.assertTrue(rules.report_auto_hide_threshold(50000) >= rules.report_auto_hide_threshold(5))

    def test_penalty_follows_the_strike_count(self):
        for strikes in (1, 2, 3, 5):
            self.assertEqual(screening.penalty(strikes), {
                "mute_hours": rules.mute_duration_hours(strikes),
                "suspension_days": rules.suspension_days(strikes),
            })

    def test_cooldown_minutes(self):
        self.assertEqual(screening.cooldown_minutes(0), rules.report_cooldown_minutes(0))
        self.assertEqual(screening.cooldown_minutes(12), rules.report_cooldown_minutes(12))
