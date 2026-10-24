import uuid

from django.db import models
from django.db.models import Q


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    description = models.CharField(max_length=1000)
    active = models.BooleanField(default=True)


class Assignment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Do wykonania"
        COMPLETED = "COMPLETED", "Wykonane"
        CANCELLED = "CANCELLED", "Anulowane"
        REMOVED = "REMOVED", "Zdjęcie usunięte"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Status, default=Status.ACTIVE)
    version = models.PositiveIntegerField(default=0)
    assigned_at = models.DateTimeField(auto_now_add=True)
    request_id = models.UUIDField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["account", "task"], name="no_repeated_task"),
            models.UniqueConstraint(fields=["account", "request_id"], name="draw_idempotency"),
        ]
        indexes = [models.Index(fields=["event", "account", "status"])]


class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name="photo")
    operation = models.OneToOneField("media_storage.StorageOperation", on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    bytes = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [models.Index(fields=["event", "-created_at"])]


class ParticipantRating(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="ratings")
    participant = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["photo", "participant"], name="one_participant_vote"),
            models.CheckConstraint(
                condition=Q(value__gte=1, value__lte=5), name="participant_scale"
            ),
        ]


class OrganizerScore(models.Model):
    photo = models.OneToOneField(Photo, on_delete=models.CASCADE, related_name="organizer_score")
    organizer = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(value__lte=5), name="organizer_scale")]


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    text = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
