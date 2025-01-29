from django.test import RequestFactory, TestCase

from feed import digest_100
from follows import services as follow_services

from . import factories as f


class DigestTests(TestCase):
    def test_digest_lists_the_followed_updates(self):
        viewer, friend = f.profile("viewer_d"), f.profile("friend_d")
        follow_services.follow(viewer, friend, f.TODAY)
        f.update(friend, "first digest item", ago_minutes=20)
        f.update(friend, "second digest item", ago_minutes=40)
        request = RequestFactory().get("/digest/viewer_d/", {"now": "2025-03-03T12:00:00"})
        html = digest_100.digest(request, "viewer_d").content.decode()
        self.assertIn("2 updates", html)
        self.assertIn("friend_d: first digest item", html)
        self.assertIn("friend_d: second digest item", html)
