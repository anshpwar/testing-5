from django.test import TestCase

from feed import views
from follows import services as follow_services

from . import factories as f


class TimelinePageTests(TestCase):
    def setUp(self):
        self.viewer = f.profile("viewer_p")
        self.friend = f.profile("friend_p")
        follow_services.follow(self.viewer, self.friend, f.TODAY)
        self.viewer.refresh_from_db()

    def get(self, handle="viewer_p", query=""):
        return self.client.get(f"/feed/page/{handle}/?now=2025-03-03T12:00:00{query}")

    def test_page_lists_followed_updates(self):
        f.update(self.friend, "walked the dog", ago_minutes=15)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Timeline for @viewer_p", html)
        self.assertIn("walked the dog", html)
        self.assertIn("@friend_p", html)

    def test_context_carries_the_updates(self):
        first = f.update(self.friend, "one", ago_minutes=30)
        response = self.get()
        self.assertEqual([u.pk for u in response.context["updates"]], [first.pk])
        self.assertEqual(response.context["profile"], self.viewer)

    def test_empty_timeline_has_a_message(self):
        self.assertIn("Nothing to show yet.", self.get().content.decode())

    def test_bodies_are_escaped(self):
        f.update(self.friend, "<script>alert(1)</script>", ago_minutes=5)
        html = self.get().content.decode()
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert", html)

    def test_unknown_profile_is_404(self):
        self.assertEqual(self.get("nobody_p").status_code, 404)

    def test_context_builder_is_usable_without_a_request(self):
        update = f.update(self.friend, "direct", ago_minutes=5)
        context = views.timeline_context(self.viewer, f.NOW)
        self.assertEqual([u.pk for u in context["updates"]], [update.pk])
        self.assertIsNone(context["next_cursor"])
