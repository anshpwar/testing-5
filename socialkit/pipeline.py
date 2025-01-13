"""End-to-end pipeline: builds summaries and renders fixed-width report lines."""
from . import conf, contract
from .deps import textfmt


def run_pipeline(records, currency="USD"):
    retries = conf.get_setting("RETRY_LIMIT")
    lines = []
    for rec in records:
        summary = contract.build_summary(rec, currency)
        lines.append(textfmt.pad_left(contract.describe(summary), 40))
    return {"retries": retries, "lines": lines}
