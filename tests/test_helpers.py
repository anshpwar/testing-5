import unittest

from socialkit import helpers


class HelperTests(unittest.TestCase):
    def test_clip_short_text_untouched(self):
        self.assertEqual(helpers.clip("hello", 10), "hello")

    def test_clip_long_text(self):
        self.assertEqual(helpers.clip("abcdefghij", 8), "abcde...")
