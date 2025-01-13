from django.test import TestCase

from posts.models import Post


class PostModelTests(TestCase):
    def test_defaults(self):
        obj = Post.objects.create(ref="PL-100", amount_cents=500)
        self.assertEqual(obj.status, "open")
        self.assertEqual(str(obj), "PL-100")

    def test_ref_is_unique(self):
        Post.objects.create(ref="PL-101", amount_cents=1)
        with self.assertRaises(Exception):
            Post.objects.create(ref="PL-101", amount_cents=2)
