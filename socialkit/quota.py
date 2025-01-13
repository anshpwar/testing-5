"""Daily allowances and account age."""


class QuotaExceeded(Exception):
    def __init__(self, limit, used):
        super().__init__(f"{used} of {limit} used")
        self.limit = limit
        self.used = used


def age_in_days(joined_on, today):
    return max(0, (today - joined_on).days)


def remaining(limit, used):
    return max(0, limit - used)


def require(limit, used):
    """Raise QuotaExceeded unless one more action fits within limit."""
    if remaining(limit, used) < 1:
        raise QuotaExceeded(limit, used)
    return remaining(limit, used) - 1
