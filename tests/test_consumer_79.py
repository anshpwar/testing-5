import unittest

from socialkit import consumer_79


class RetryTests(unittest.TestCase):
    def test_attempts(self):
        self.assertEqual(consumer_79.attempts(), 4)
