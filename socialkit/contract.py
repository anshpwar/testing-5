"""Summary contract shared by the social networking services, the API layer and reports."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    ref: str
    amount_cents: int
    status: str


def build_summary(record, currency="USD"):
    """Summary payload consumed by the API layer and the nightly reports."""
    return {
        "ref": record.ref,
        "amount": record.amount_cents,
        "status": record.status,
        "currency": currency,
    }


def describe(summary):
    """One-line description of a post summary for logs and notifications."""
    return f"{summary['ref']} {summary['status']} {summary['amount']} {summary['currency']}"
