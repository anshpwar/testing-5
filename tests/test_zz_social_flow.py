"""End-to-end flows through the JSON API: sign-up, following, posting, reporting and moderation."""
import json

from django.test import TestCase

from feed.models import Update
from profiles.models import Profile
from profiles import services as profile_services
from socialkit import rules

from . import factories as f

NOW = "now=2025-03-03T12:00:00"


class FlowBase(TestCase):
    def call(self, method, path, body=None, handle=None, extra=""):
        kwargs = {"content_type": "application/json"}
        if handle:
            kwargs["HTTP_X_HANDLE"] = handle
        data = json.dumps(body) if body is not None else ""
        if method == "get":
            return self.client.get(f"{path}?{NOW}{extra}", **({"HTTP_X_HANDLE": handle} if handle else {}))
        return getattr(self.client, method)(f"{path}?{NOW}{extra}", data, **kwargs)

    def signup(self, handle, name=None):
        resp = self.call("post", "/profiles/", {"handle": handle, "display_name": name or handle.title()})
        self.assertEqual(resp.status_code, 201, resp.content)
        return resp.json()


class ProfileFlowTests(FlowBase):
    def test_signup_validation_and_lookup(self):
        created = self.signup("Marisol_V", "Marisol Vega")
        self.assertEqual((created["handle"], created["age_days"], created["followers"]), ("marisol_v", 0, 0))
        self.assertEqual(self.call("get", "/profiles/marisol_v/").json()["display_name"], "Marisol Vega")
        self.assertEqual(self.call("post", "/profiles/", {"handle": "marisol_v", "display_name": "Dup"}).status_code, 409)
        self.assertEqual(self.call("post", "/profiles/", {"handle": "x", "display_name": "Short"}).status_code, 400)
        self.assertEqual(self.call("post", "/profiles/", {"handle": "only_handle"}).status_code, 400)
        self.assertEqual(self.call("get", "/profiles/ghost_one/").status_code, 404)

    def test_limits_endpoint_matches_the_policy(self):
        self.signup("tobias_k")
        limits = self.call("get", "/profiles/me/limits/", handle="tobias_k").json()
        self.assertEqual(limits["post_length"], rules.post_length_limit(0))
        self.assertEqual(limits["posts_per_day"], rules.daily_post_limit(0))
        self.assertEqual(limits["follows_per_day"], rules.follow_limit_per_day(0))
        self.assertEqual(self.call("get", "/profiles/me/limits/").status_code, 401)

    def test_verification_request(self):
        self.signup("tobias_k")
        denied = self.call("post", "/profiles/me/verify/", handle="tobias_k").json()
        self.assertEqual((denied["eligible"], denied["verified"]), (False, False))
        Profile.objects.filter(handle="tobias_k").update(follower_count=rules.verified_follower_floor(0))
        granted = self.call("post", "/profiles/me/verify/", handle="tobias_k").json()
        self.assertEqual((granted["eligible"], granted["verified"]), (True, True))


class FollowFlowTests(FlowBase):
    def test_follow_unfollow_and_block_over_http(self):
        for handle in ("ann_a", "bob_b"):
            self.signup(handle)
        first = self.call("post", "/follows/bob_b/", handle="ann_a")
        again = self.call("post", "/follows/bob_b/", handle="ann_a")
        self.assertEqual((first.status_code, first.json()), (201, {"following": True, "followers": 1}))
        self.assertEqual(again.status_code, 200)
        self.assertEqual(self.call("get", "/follows/bob_b/followers/").json(), {"handle": "bob_b", "followers": ["ann_a"]})
        gone = self.call("delete", "/follows/bob_b/", handle="ann_a")
        self.assertEqual(gone.json(), {"following": False, "followers": 0})
        self.assertEqual(self.call("post", "/follows/ann_a/", handle="ann_a").status_code, 400)
        self.assertEqual(self.call("post", "/follows/bob_b/block/", handle="ann_a").status_code, 201)
        blocked = self.call("post", "/follows/bob_b/", handle="ann_a")
        self.assertEqual((blocked.status_code, blocked.json()["error"]), (403, "blocked"))
        self.assertEqual(self.call("post", "/follows/ghost_x/", handle="ann_a").status_code, 404)

    def test_suggestions_endpoint(self):
        for handle in ("aaa_a", "bbb_b", "ccc_c"):
            self.signup(handle)
        self.call("post", "/follows/bbb_b/", handle="aaa_a")
        self.call("post", "/follows/ccc_c/", handle="bbb_b")
        self.assertEqual(self.call("get", "/follows/suggestions/", handle="aaa_a").json(), {"suggestions": ["ccc_c"]})


class ModerationFlowTests(FlowBase):
    def test_reports_hide_an_update_and_the_moderator_penalises_the_author(self):
        self.signup("writer_w")
        self.signup("reader_r")
        self.call("post", "/follows/writer_w/", handle="reader_r")
        post = self.call("post", "/feed/publish/", {"body": "something rude"}, handle="writer_w").json()
        timeline = self.call("get", "/feed/timeline/", handle="reader_r").json()
        self.assertEqual([i["id"] for i in timeline["items"]], [post["id"]])

        threshold = rules.report_auto_hide_threshold(1)
        for i in range(threshold):
            self.signup(f"critic{i:03d}")
            resp = self.call("post", "/moderation/reports/", {"update_id": post["id"], "reason": "abuse"}, handle=f"critic{i:03d}")
            self.assertEqual(resp.status_code, 201)
            self.assertEqual(resp.json()["hidden"], i + 1 >= threshold)
        self.assertEqual(self.call("get", "/feed/timeline/", handle="reader_r").json()["items"], [])

        self.signup("mod_one")
        Profile.objects.filter(handle="mod_one").update(moderator=True)
        self.assertEqual(self.call("get", "/moderation/queue/", handle="reader_r").status_code, 403)
        queue = self.call("get", "/moderation/queue/", handle="mod_one").json()["queue"]
        self.assertEqual(queue, [{"update_id": post["id"], "author": "writer_w", "reports": threshold, "hidden": True}])

        verdict = self.call("post", f"/moderation/updates/{post['id']}/resolve/", {"decision": "actioned"}, handle="mod_one")
        self.assertEqual(verdict.json(), {"strikes": 1, "handle": "writer_w"})
        blocked = self.call("post", "/feed/publish/", {"body": "i am back"}, handle="writer_w")
        self.assertEqual((blocked.status_code, blocked.json()["error"]), (403, "muted"))
        self.assertEqual(self.call("get", "/moderation/queue/", handle="mod_one").json(), {"queue": []})

    def test_report_errors_over_http(self):
        self.signup("writer_w")
        self.signup("critic_c")
        post = self.call("post", "/feed/publish/", {"body": "hello"}, handle="writer_w").json()
        self.assertEqual(self.call("post", "/moderation/reports/", {"update_id": post["id"]}, handle="writer_w").status_code, 409)
        self.assertEqual(self.call("post", "/moderation/reports/", {"update_id": post["id"]}, handle="critic_c").status_code, 201)
        self.assertEqual(self.call("post", "/moderation/reports/", {"update_id": post["id"]}, handle="critic_c").status_code, 409)
        self.assertEqual(self.call("post", "/moderation/reports/", {"update_id": 9999}, handle="critic_c").status_code, 404)
        self.assertEqual(self.call("post", "/moderation/reports/", {}, handle="critic_c").status_code, 400)


class StateConsistencyTests(FlowBase):
    def test_counts_survive_a_full_session(self):
        for handle in ("ann_a", "bob_b", "cy_cc"):
            self.signup(handle)
        self.call("post", "/follows/ann_a/", handle="bob_b")
        self.call("post", "/follows/ann_a/", handle="cy_cc")
        post = self.call("post", "/feed/publish/", {"body": "welcome #newcomers"}, handle="ann_a").json()
        self.call("post", f"/feed/{post['id']}/like/", handle="bob_b")
        self.call("post", f"/feed/{post['id']}/like/", handle="cy_cc")
        self.call("post", "/feed/publish/", {"body": "thanks", "parent": post["id"]}, handle="bob_b")
        ann = Profile.objects.get(handle="ann_a")
        update = Update.objects.get(pk=post["id"])
        self.assertEqual((ann.follower_count, update.like_count, update.reply_count), (2, 2, 1))
        summary = profile_services.summary(ann, f.TODAY)
        self.assertEqual(summary["followers"], 2)
        timeline = self.call("get", "/feed/timeline/", handle="bob_b").json()["items"]
        self.assertEqual([(i["id"], i["liked"]) for i in timeline], [(post["id"], True)])
