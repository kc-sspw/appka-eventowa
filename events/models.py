import re
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Event(models.Model):
    class State(models.TextChoices):
        DRAFT = "DRAFT", "Przygotowanie"
        ACTIVE = "ACTIVE", "Aktywne"
        CLOSING = "CLOSING", "Porządkowanie"
        CLOSED = "CLOSED", "Zamknięte"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, max_length=63)
    name = models.CharField(max_length=160)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    state = models.CharField(max_length=10, choices=State, default=State.DRAFT)
    game_starts_at = models.DateTimeField(null=True, blank=True)
    game_ends_at = models.DateTimeField(null=True, blank=True)
    instructions = models.TextField(blank=True, max_length=10000)
    storage_budget = models.BigIntegerField(default=2 * 1024**3)
    cleaned_at = models.DateTimeField(null=True, blank=True)
    cleanup_failed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")), name="event_time_order"
            ),
            models.CheckConstraint(condition=Q(storage_budget__gte=0), name="positive_budget"),
            models.CheckConstraint(
                condition=Q(game_ends_at__isnull=True) | Q(game_ends_at__lte=F("ends_at")),
                name="game_before_end",
            ),
        ]

    def clean(self):
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", self.slug):
            raise ValidationError("Slug: małe litery, cyfry i myślniki.")
        if bool(self.game_starts_at) != bool(self.game_ends_at):
            raise ValidationError("Ustaw oba terminy gry.")
        if (
            self.game_starts_at
            and not self.starts_at <= self.game_starts_at < self.game_ends_at <= self.ends_at
        ):
            raise ValidationError("Gra musi mieścić się w terminie wydarzenia.")

    def __str__(self):
        return self.name


class RateBucket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True)
    key = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)
