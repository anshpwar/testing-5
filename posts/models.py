from django.db import models


class Post(models.Model):
    ref = models.CharField(max_length=24, unique=True)
    amount_cents = models.BigIntegerField(default=0)
    status = models.CharField(max_length=16, default="open")
    note = models.CharField(max_length=80, blank=True, default="")

    def __str__(self):
        return self.ref
