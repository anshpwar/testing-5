import datetime as dt
import unittest

from socialkit import pagination, quota


class PaginationTests(unittest.TestCase):
    def test_cursor_round_trip(self):
        for offset in (0, 7, 1234):
            self.assertEqual(pagination.decode_cursor(pagination.encode_cursor(offset)), offset)

    def test_empty_cursor_is_the_start(self):
        self.assertEqual(pagination.decode_cursor(None), 0)
        self.assertEqual(pagination.decode_cursor(""), 0)

    def test_bad_cursors_raise(self):
        for text in ("!!!", "eDE", "bzEyYQ"):
            with self.assertRaises(ValueError, msg=text):
                pagination.decode_cursor(text)

    def test_page_walks_through_all_items(self):
        items = [1, 2, 3, 4, 5]
        first, cursor = pagination.page(items, None, 2)
        second, cursor = pagination.page(items, cursor, 2)
        third, cursor = pagination.page(items, cursor, 2)
        self.assertEqual((first, second, third, cursor), ([1, 2], [3, 4], [5], None))

    def test_exact_fit_has_no_next_cursor(self):
        self.assertEqual(pagination.page([1, 2], None, 2), ([1, 2], None))

    def test_page_size_must_be_positive(self):
        with self.assertRaises(ValueError):
            pagination.page([1], None, 0)


class QuotaTests(unittest.TestCase):
    def test_age_in_days_never_negative(self):
        joined = dt.date(2025, 3, 1)
        self.assertEqual(quota.age_in_days(joined, dt.date(2025, 3, 4)), 3)
        self.assertEqual(quota.age_in_days(joined, dt.date(2025, 2, 1)), 0)

    def test_remaining(self):
        self.assertEqual(quota.remaining(5, 2), 3)
        self.assertEqual(quota.remaining(5, 9), 0)

    def test_require_returns_what_is_left_after_this_action(self):
        self.assertEqual(quota.require(5, 3), 1)

    def test_require_raises_at_the_limit(self):
        with self.assertRaises(quota.QuotaExceeded) as caught:
            quota.require(5, 5)
        self.assertEqual((caught.exception.limit, caught.exception.used), (5, 5))
