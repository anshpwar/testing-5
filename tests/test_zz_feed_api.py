import datetime as dt
import json
import pathlib

from django.test import TestCase

from feed.models import Update
from follows import services as follow_services
from socialkit import rules

from . import factories as f

FIXTURE = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "tests" / "fixtures" / "timeline.json"
NOW = "now=2025-03-03T12:00:00"


class FeedApiBase(TestCase):
    def setUp(self):
        self.viewer = f.profile("viewer_a")
        self.friend = f.profile("friend_a", name="Friend A")
        follow_services.follow(self.viewer, self.friend, f.TODAY)

    def get(self, path, handle="viewer_a"):
        sep = "&" if "?" in path else "?"
        return self.client.get(f"{path}{sep}{NOW}", HTTP_X_HANDLE=handle)

    def send(self, method, path, body=None, handle="viewer_a"):
        call = getattr(self.client, method)
        data = json.dumps(body) if body is not None else ""
        return call(f"{path}?{NOW}", data, content_type="application/json", HTTP_X_HANDLE=handle)


class TimelineApiTests(FeedApiBase):
    def test_requires_a_known_handle(self):
        self.assertEqual(self.client.get("/feed/timeline/").status_code, 401)
        self.assertEqual(self.get("/feed/timeline/", handle="ghost_a").status_code, 401)

    def test_payload_shape(self):
        update = f.update(self.friend, "shape check", ago_minutes=30, like_count=3, reply_count=1)
        body = self.get("/feed/timeline/").json()
        self.assertEqual(set(body), {"items", "next_cursor"})
        item = body["items"][0]
        self.assertEqual(item["id"], update.pk)
        self.assertEqual(item["author"], {"handle": "friend_a", "display_name": "Friend A", "verified": False})
        self.assertEqual(item["body"], "shape check")
        self.assertEqual(item["created_at"], update.created_at.isoformat())
        self.assertEqual(item["likes"], 3)
        self.assertEqual(item["reply_count"], 1)
        self.assertFalse(item["liked"])
        self.assertIsNone(body["next_cursor"])

    def test_payload_keys_match_the_recorded_frontend_fixture(self):
        recorded = json.loads(FIXTURE.read_text())
        f.update(self.friend, "contract", ago_minutes=30)
        live = self.get("/feed/timeline/").json()
        self.assertEqual(set(live), set(recorded))
        self.assertEqual(set(live["items"][0]), set(recorded["items"][0]))
        self.assertEqual(set(live["items"][0]["author"]), set(recorded["items"][0]["author"]))

    def test_liked_flag_reflects_the_caller(self):
        update = f.update(self.friend, "likeable", ago_minutes=30)
        self.send("post", f"/feed/{update.pk}/like/")
        self.assertTrue(self.get("/feed/timeline/").json()["items"][0]["liked"])
        self.assertFalse(self.get("/feed/timeline/", handle="friend_a").json()["items"][0]["liked"])

    def test_cursor_paging(self):
        for i in range(3):
            f.update(self.friend, f"p{i}", ago_minutes=10 + i)
        size = rules.feed_page_size(self.viewer.following_count)
        body = self.get("/feed/timeline/").json()
        self.assertEqual(len(body["items"]), min(3, size))
        self.assertEqual(self.get("/feed/timeline/?cursor=%21%21").status_code, 400)


class PublishApiTests(FeedApiBase):
    def test_publish_returns_the_new_update(self):
        resp = self.send("post", "/feed/publish/", {"body": " hello from the api "})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["body"], "hello from the api")
        self.assertEqual(resp.json()["author"]["handle"], "viewer_a")
        ids = [i["id"] for i in self.get("/feed/timeline/").json()["items"]]
        self.assertIn(resp.json()["id"], ids)

    def test_validation_errors(self):
        self.assertEqual(self.send("post", "/feed/publish/", {"nope": 1}).status_code, 400)
        empty = self.send("post", "/feed/publish/", {"body": "  "})
        self.assertEqual((empty.status_code, empty.json()), (422, {"error": "empty"}))
        parent = self.send("post", "/feed/publish/", {"body": "x", "parent": 9999})
        self.assertEqual(parent.status_code, 404)

    def test_daily_limit_is_429(self):
        rookie = f.newcomer()
        for i in range(rules.daily_post_limit(0)):
            self.assertEqual(self.send("post", "/feed/publish/", {"body": f"n{i}"}, handle="newbie").status_code, 201)
        resp = self.send("post", "/feed/publish/", {"body": "more"}, handle="newbie")
        self.assertEqual((resp.status_code, resp.json()["error"]), (429, "daily_limit"))
        self.assertEqual(rookie.updates.count(), rules.daily_post_limit(0))

    def test_reply_increments_the_parent(self):
        parent = f.update(self.friend, "root", ago_minutes=20)
        resp = self.send("post", "/feed/publish/", {"body": "reply", "parent": parent.pk})
        self.assertEqual(resp.status_code, 201)
        parent.refresh_from_db()
        self.assertEqual(parent.reply_count, 1)


class LikeApiTests(FeedApiBase):
    def test_like_and_unlike_round_trip(self):
        update = f.update(self.friend, "like me", ago_minutes=30)
        liked = self.send("post", f"/feed/{update.pk}/like/").json()
        self.assertEqual((liked["likes"], liked["liked"]), (1, True))
        again = self.send("post", f"/feed/{update.pk}/like/").json()
        self.assertEqual(again["likes"], 1)
        unliked = self.send("delete", f"/feed/{update.pk}/like/").json()
        self.assertEqual((unliked["likes"], unliked["liked"]), (0, False))

    def test_unknown_update_is_404_and_hidden_is_409(self):
        self.assertEqual(self.send("post", "/feed/9999/like/").status_code, 404)
        hidden = f.update(self.friend, "hidden", hidden=True)
        self.assertEqual(self.send("post", f"/feed/{hidden.pk}/like/").status_code, 409)


class TrendingApiTests(FeedApiBase):
    def test_trending_lists_hot_tags(self):
        floor = rules.trending_min_mentions(24)
        self.assertEqual(self.get("/feed/trending/").json(), {"tags": []})
        Update.objects.bulk_create([Update(author=self.friend, body="#lakeside again", created_at=f.NOW - dt.timedelta(minutes=5)) for _ in range(floor)])
        self.assertEqual(self.get("/feed/trending/").json(), {"tags": [{"tag": "lakeside", "count": floor}]})
