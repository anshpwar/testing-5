"""Consumer added independently of the base-side change (scenario 83)."""


from .contract import build_summary


def export_line(record):
    summary = build_summary(record)
    return f"{summary['ref']},{summary['amount_cents']}"
