import datetime as dt

from django.test import TestCase

from moderation import services
from moderation.models import Action, Report
from socialkit import rules

from . import factories as f


class ReportTests(TestCase):
    def setUp(self):
        self.author = f.profile("author_m")
        self.update = f.update(self.author)

    def reporters(self, count):
        return [f.profile(f"rep{i:03d}") for i in range(count)]

    def test_report_is_recorded_open(self):
        reporter = f.profile("reporter_m")
        report = services.file_report(reporter, self.update, "spam", f.NOW)
        self.assertEqual((report.status, report.reason, report.created_at), ("open", "spam", f.NOW))

    def test_cannot_report_your_own_update(self):
        with self.assertRaises(services.ReportError) as caught:
            services.file_report(self.author, self.update, "spam", f.NOW)
        self.assertEqual(caught.exception.code, "own_update")

    def test_duplicate_reports_are_refused(self):
        reporter = f.profile("reporter_m")
        services.file_report(reporter, self.update, "spam", f.NOW)
        with self.assertRaises(services.ReportError) as caught:
            services.file_report(reporter, self.update, "abuse", f.NOW + dt.timedelta(hours=1))
        self.assertEqual(caught.exception.code, "duplicate")

    def test_update_is_hidden_exactly_at_the_threshold(self):
        threshold = rules.report_auto_hide_threshold(self.author.follower_count)
        for reporter in self.reporters(threshold - 1):
            services.file_report(reporter, self.update, "abuse", f.NOW)
        self.update.refresh_from_db()
        self.assertFalse(self.update.hidden)
        services.file_report(f.profile("last_one"), self.update, "abuse", f.NOW)
        self.update.refresh_from_db()
        self.assertTrue(self.update.hidden)
        self.assertEqual(Action.objects.filter(profile=self.author, kind="hide").count(), 1)

    def test_cooldown_applies_after_the_free_reports(self):
        free = next(k for k in range(1, 100) if rules.report_cooldown_minutes(k) > 0)
        reporter = f.profile("busy_rep")
        for i in range(free):
            target = f.update(f.profile(f"target{i:03d}"), f"post {i}")
            services.file_report(reporter, target, "spam", f.NOW)
        extra = f.update(f.profile("target_last"), "one more")
        with self.assertRaises(services.ReportError) as caught:
            services.file_report(reporter, extra, "spam", f.NOW)
        self.assertEqual(caught.exception.code, "cooldown")
        later = f.NOW + dt.timedelta(minutes=rules.report_cooldown_minutes(free))
        self.assertTrue(services.file_report(reporter, extra, "spam", later).pk)

    def test_cooldown_counts_only_todays_reports(self):
        reporter = f.profile("daily_rep")
        old = f.update(f.profile("target_old"), "old")
        Report.objects.create(update=old, reporter=reporter, reason="spam", created_at=f.NOW - dt.timedelta(days=1))
        self.assertEqual(services.reports_today(reporter, f.NOW).count(), 0)


class ResolveTests(TestCase):
    def setUp(self):
        self.author = f.profile("author_r")
        self.update = f.update(self.author)
        for i in range(2):
            services.file_report(f.profile(f"rep{i:03d}"), self.update, "abuse", f.NOW)

    def test_actioned_adds_a_strike_and_applies_the_penalty(self):
        services.resolve(self.update, "actioned", f.NOW)
        self.author.refresh_from_db()
        self.update.refresh_from_db()
        self.assertEqual(self.author.strikes, 1)
        self.assertEqual(self.author.muted_until, f.NOW + dt.timedelta(hours=rules.mute_duration_hours(1)))
        days = rules.suspension_days(1)
        expected = f.NOW + dt.timedelta(days=days) if days else None
        self.assertEqual(self.author.suspended_until, expected)
        self.assertTrue(self.update.hidden)
        self.assertEqual(Report.objects.filter(status="actioned").count(), 2)
        self.assertEqual(Action.objects.filter(kind="suspend").count(), 1 if days else 0)

    def test_repeat_offenders_get_the_penalty_for_their_strike_count(self):
        services.resolve(self.update, "actioned", f.NOW)
        second = f.update(self.author, "again", ago_minutes=5)
        services.file_report(f.profile("rep_late"), second, "abuse", f.NOW)
        services.resolve(second, "actioned", f.NOW)
        self.author.refresh_from_db()
        self.assertEqual(self.author.strikes, 2)
        self.assertEqual(self.author.muted_until, f.NOW + dt.timedelta(hours=rules.mute_duration_hours(2)))

    def test_dismissed_restores_the_update(self):
        self.update.hidden = True
        self.update.save()
        services.resolve(self.update, "dismissed", f.NOW)
        self.author.refresh_from_db()
        self.update.refresh_from_db()
        self.assertFalse(self.update.hidden)
        self.assertEqual(self.author.strikes, 0)
        self.assertEqual(Report.objects.filter(status="dismissed").count(), 2)

    def test_resolve_rejects_bad_decisions_and_closed_updates(self):
        with self.assertRaises(services.ReportError) as caught:
            services.resolve(self.update, "banish", f.NOW)
        self.assertEqual(caught.exception.code, "bad_decision")
        services.resolve(self.update, "dismissed", f.NOW)
        with self.assertRaises(services.ReportError) as caught:
            services.resolve(self.update, "dismissed", f.NOW)
        self.assertEqual(caught.exception.code, "nothing_open")


class QueueTests(TestCase):
    def test_most_reported_updates_come_first(self):
        author = f.profile("author_q")
        quiet, busy = f.update(author, "quiet"), f.update(author, "busy")
        services.file_report(f.profile("rep_a"), quiet, "spam", f.NOW)
        for i in range(2):
            services.file_report(f.profile(f"rep_b{i}"), busy, "spam", f.NOW)
        rows = services.queue()
        self.assertEqual([row["update"].pk for row in rows], [busy.pk, quiet.pk])
        self.assertEqual([len(row["reports"]) for row in rows], [2, 1])

    def test_resolved_reports_leave_the_queue(self):
        author = f.profile("author_q2")
        update = f.update(author)
        services.file_report(f.profile("rep_c"), update, "spam", f.NOW)
        services.resolve(update, "dismissed", f.NOW)
        self.assertEqual(services.queue(), [])
