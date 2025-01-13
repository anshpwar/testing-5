from django.db import models

REASONS = [("spam", "Spam"), ("abuse", "Abuse"), ("misinfo", "Misinformation"), ("other", "Other")]
STATUSES = [("open", "Open"), ("actioned", "Actioned"), ("dismissed", "Dismissed")]
KINDS = [("mute", "Mute"), ("suspend", "Suspend"), ("hide", "Hide")]


class Report(models.Model):
    update = models.ForeignKey("feed.Update", on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="reports_filed")
    reason = models.CharField(max_length=10, choices=REASONS, default="other")
    created_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUSES, default="open")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("update", "reporter")]
        ordering = ["created_at", "id"]


class Action(models.Model):
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="actions")
    kind = models.CharField(max_length=10, choices=KINDS)
    reason = models.CharField(max_length=80, blank=True, default="")
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]
