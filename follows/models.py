from django.db import models


class Follow(models.Model):
    follower = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="following_set")
    followee = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="follower_set")
    created_on = models.DateField()

    class Meta:
        unique_together = [("follower", "followee")]
        ordering = ["id"]

    def __str__(self):
        return f"{self.follower} -> {self.followee}"


class Block(models.Model):
    blocker = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="blocking_set")
    blocked = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="blocked_by_set")
    created_on = models.DateField()

    class Meta:
        unique_together = [("blocker", "blocked")]
        ordering = ["id"]
