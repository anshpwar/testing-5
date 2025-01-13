from django.db import models


class Profile(models.Model):
    handle = models.CharField(max_length=20, unique=True)
    display_name = models.CharField(max_length=60)
    bio = models.CharField(max_length=160, blank=True, default="")
    joined_on = models.DateField()
    verified = models.BooleanField(default=False)
    moderator = models.BooleanField(default=False)
    strikes = models.PositiveSmallIntegerField(default=0)
    muted_until = models.DateTimeField(null=True, blank=True)
    suspended_until = models.DateTimeField(null=True, blank=True)
    follower_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["handle"]

    def __str__(self):
        return f"@{self.handle}"
