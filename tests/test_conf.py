import unittest

from socialkit import conf


class ConfTests(unittest.TestCase):
    def test_default(self):
        self.assertEqual(conf.get_setting("MAX_RETRIES"), 3)

    def test_override_wins(self):
        self.assertEqual(conf.get_setting("BATCH_SIZE", {"BATCH_SIZE": 5}), 5)

    def test_unknown_setting_raises(self):
        with self.assertRaises(KeyError):
            conf.get_setting("NOPE")
