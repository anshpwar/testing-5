import unittest

from socialkit import calc


class CalcTests(unittest.TestCase):
    def test_combined_charge(self):
        self.assertEqual(calc.combined_charge(0), 13)
        self.assertEqual(calc.combined_charge(1), 13)
        self.assertEqual(calc.combined_charge(2), 60)
        self.assertEqual(calc.combined_charge(7), 60)
