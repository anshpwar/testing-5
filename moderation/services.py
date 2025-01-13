import datetime as dt

from django.db import transaction

from socialkit import screening

from .models import Action, Report


class ReportError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def reports_today(reporter, now):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return Report.objects.filter(reporter=reporter, created_at__gte=start, created_at__lt=start + dt.timedelta(days=1))


def file_report(reporter, update, reason, now):
    """Record a report. Returns the report; hides the update once enough open reports have arrived."""
    if update.author_id == reporter.pk:
        raise ReportError("own_update")
    if Report.objects.filter(update=update, reporter=reporter).exists():
        raise ReportError("duplicate")
    filed = list(reports_today(reporter, now))
    if filed:
        wait = dt.timedelta(minutes=screening.cooldown_minutes(len(filed)))
        if now - filed[-1].created_at < wait:
            raise ReportError("cooldown")
    with transaction.atomic():
        report = Report.objects.create(update=update, reporter=reporter, reason=reason, created_at=now)
        open_count = Report.objects.filter(update=update, status="open").count()
        if not update.hidden and screening.should_auto_hide(open_count, update.author.follower_count):
            update.hidden = True
            update.save(update_fields=["hidden"])
            Action.objects.create(profile=update.author, kind="hide", reason=f"auto-hidden after {open_count} reports", created_at=now)
    return report


def queue():
    """Open reports grouped per update, most reported first."""
    grouped = {}
    for report in Report.objects.filter(status="open").select_related("update", "update__author"):
        grouped.setdefault(report.update_id, []).append(report)
    rows = [{"update": rs[0].update, "reports": rs, "hidden": rs[0].update.hidden} for rs in grouped.values()]
    rows.sort(key=lambda row: (-len(row["reports"]), row["update"].pk))
    return rows


def resolve(update, decision, now):
    """Close every open report on an update. "actioned" adds a strike and applies the matching mute or suspension."""
    if decision not in ("actioned", "dismissed"):
        raise ReportError("bad_decision")
    open_reports = Report.objects.filter(update=update, status="open")
    if not open_reports.exists():
        raise ReportError("nothing_open")
    author = update.author
    with transaction.atomic():
        if decision == "actioned":
            author.strikes += 1
            penalty = screening.penalty(author.strikes)
            author.muted_until = now + dt.timedelta(hours=penalty["mute_hours"])
            Action.objects.create(profile=author, kind="mute", reason=f"strike {author.strikes}", created_at=now,
                                  expires_at=author.muted_until)
            if penalty["suspension_days"]:
                author.suspended_until = now + dt.timedelta(days=penalty["suspension_days"])
                Action.objects.create(profile=author, kind="suspend", reason=f"strike {author.strikes}", created_at=now,
                                      expires_at=author.suspended_until)
            author.save(update_fields=["strikes", "muted_until", "suspended_until"])
            update.hidden = True
        else:
            update.hidden = False
        update.save(update_fields=["hidden"])
        open_reports.update(status=decision, resolved_at=now)
    return author
