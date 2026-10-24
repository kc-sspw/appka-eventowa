import uuid

from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Audience(models.TextChoices):
    ALL = "ALL", "Wszyscy"
    GROUPS = "GROUPS", "Wybrane grupy"


class Entry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    kind = models.CharField(
        max_length=6, choices=[("NEWS", "Aktualność"), ("STATIC", "Stała informacja")]
    )
    title = models.CharField(max_length=160)
    body = models.TextField(max_length=10000)
    pinned = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    audience = models.CharField(max_length=6, choices=Audience, default=Audience.ALL)
    groups = models.ManyToManyField("accounts.Group", blank=True)

    class Meta:
        ordering = ["-pinned", "-published_at", "id"]
        indexes = [models.Index(fields=["event", "kind", "-published_at"])]


class ScheduleItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    location = models.CharField(max_length=160, blank=True)
    description = models.TextField(max_length=5000, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    audience = models.CharField(max_length=6, choices=Audience, default=Audience.ALL)
    groups = models.ManyToManyField("accounts.Group", blank=True)

    class Meta:
        ordering = ["starts_at", "id"]
        indexes = [models.Index(fields=["event", "starts_at"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__isnull=True) | Q(ends_at__gte=F("starts_at")),
                name="schedule_time_order",
            )
        ]
