from django.db import models


class Update(models.Model):
    author = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="updates")
    body = models.TextField()
    created_at = models.DateTimeField()
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    hidden = models.BooleanField(default=False)
    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"#{self.pk} by {self.author}"


class Like(models.Model):
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="likes")
    update = models.ForeignKey(Update, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        unique_together = [("profile", "update")]
