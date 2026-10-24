import uuid

from django.db import models
from django.utils import timezone


class StorageConnection(models.Model):
    event = models.OneToOneField("events.Event", on_delete=models.CASCADE)
    folder_id = models.CharField(max_length=200)
    owner_id = models.CharField(max_length=200, blank=True)
    encrypted_credentials = models.TextField(blank=True)


class StorageOperation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    assignment = models.ForeignKey(
        "game.Assignment", null=True, blank=True, on_delete=models.SET_NULL
    )
    account = models.ForeignKey(
        "accounts.Account", null=True, blank=True, on_delete=models.SET_NULL
    )
    expected_version = models.PositiveIntegerField(default=0)
    action = models.CharField(max_length=8, default="UPLOAD")
    status = models.CharField(max_length=16, default="PROCESSING")
    external_file_id = models.CharField(max_length=200, blank=True)
    reserved_bytes = models.PositiveIntegerField(default=0)
    content_digest = models.CharField(max_length=64, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now, db_index=True)
    lease_until = models.DateTimeField(null=True, blank=True)
    lease_token = models.UUIDField(null=True, blank=True)
    error_code = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["event", "status", "next_attempt_at"])]


class OAuthState(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    organizer = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    state_hash = models.CharField(max_length=64, unique=True)
    session_hash = models.CharField(max_length=64)
    verifier = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    stage = models.CharField(max_length=10, default="OPEN")
    ticket_hash = models.CharField(max_length=64, blank=True)
    encrypted_credentials = models.TextField(blank=True)
