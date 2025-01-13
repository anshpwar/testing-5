import unittest

from socialkit import contract


class ContractTests(unittest.TestCase):
    def test_build_summary(self):
        rec = contract.Record("PL-1", 1250, "open")
        self.assertEqual(
            contract.build_summary(rec),
            {"ref": "PL-1", "amount_cents": 1250, "status": "open", "currency": "USD"},
        )

    def test_describe(self):
        summary = {"ref": "PL-2", "status": "closed", "amount_cents": 99, "currency": "EUR"}
        self.assertEqual(contract.describe(summary), "PL-2 closed 99 EUR")
