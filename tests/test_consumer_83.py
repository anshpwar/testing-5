import unittest

from socialkit import contract, consumer_83


class ExportTests(unittest.TestCase):
    def test_export_line(self):
        rec = contract.Record("PL-9", 700, "open")
        self.assertEqual(consumer_83.export_line(rec), "PL-9,700")
