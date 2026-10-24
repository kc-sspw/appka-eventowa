import shutil

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import Account, AccountSession, Group, ImportBatch
from game.models import Assignment, Comment, Photo, Task
from information.models import Entry, ScheduleItem
from media_storage.cache import purge_event
from media_storage.models import OAuthState, StorageConnection, StorageOperation
from media_storage.services import _delete_later, run_operation

from .models import Event, RateBucket
from .security import assert_actor


@transaction.atomic
def begin_close(event, organizer=None):
    event = Event.objects.select_for_update().get(pk=event.pk)
    if organizer is not None:
        assert_actor(event, organizer, "ORGANIZER")
    if event.state in {"DRAFT", "ACTIVE"}:
        event.state = "CLOSING"
        event.save(update_fields=["state"])
    purge_event(event.pk)


def clean_event(event_id):
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event_id)
        if event.state != "CLOSING":
            return
        purge_event(event.id)
        shutil.rmtree(settings.PRIVATE_ROOT / "incoming" / str(event.id), ignore_errors=True)
        # Django admin history stores object_repr; remove event account names too.
        account_ids = [
            str(pk) for pk in Account.objects.filter(event=event).values_list("pk", flat=True)
        ]
        LogEntry.objects.filter(
            Q(content_type=ContentType.objects.get_for_model(Event), object_id=str(event.pk))
            | Q(content_type=ContentType.objects.get_for_model(Account), object_id__in=account_ids)
        ).delete()
        keys = AccountSession.objects.filter(account__event=event).values("session_key")
        Session.objects.filter(session_key__in=keys).delete()
        # Delete operational content even if one provider deletion is unavailable.
        Photo.objects.filter(event=event).delete()
        Comment.objects.filter(event=event).delete()
        Assignment.objects.filter(event=event).delete()
        Task.objects.filter(event=event).delete()
        Entry.objects.filter(event=event).delete()
        ScheduleItem.objects.filter(event=event).delete()
        ImportBatch.objects.filter(event=event).delete()
        Group.objects.filter(event=event).delete()
        Account.objects.filter(event=event).delete()
        OAuthState.objects.filter(event=event).delete()
        RateBucket.objects.filter(event=event).delete()
        event.instructions = ""
        event.game_starts_at = event.game_ends_at = None
        event.storage_budget = 0
        event.save(
            update_fields=["instructions", "game_starts_at", "game_ends_at", "storage_budget"]
        )
        for op in StorageOperation.objects.filter(event=event, action="UPLOAD").exclude(
            status="DONE"
        ):
            # An in-flight request can still reach Drive. Keep credentials and reconcile after its lease.
            if not op.lease_until or op.lease_until <= timezone.now():
                _delete_later(op)
        pending = list(
            StorageOperation.objects.filter(event=event)
            .exclude(action="UPLOAD", status="DONE")
            .exclude(action="DELETE", status="DONE")
            .values_list("pk", flat=True)
        )
    for pk in pending:
        run_operation(pk)
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event_id)
        unresolved = StorageOperation.objects.filter(event=event).exclude(status="DONE").exists()
        if unresolved:
            event.cleanup_failed = StorageOperation.objects.filter(
                event=event, status="RETRY"
            ).exists()
            event.save(update_fields=["cleanup_failed"])
            return
        StorageOperation.objects.filter(
            event=event
        ).delete()  # Ready album files are intentionally untouched.
        StorageConnection.objects.filter(event=event).delete()
        event.state = "CLOSED"
        event.cleaned_at = timezone.now()
        event.cleanup_failed = False
        event.save(update_fields=["state", "cleaned_at", "cleanup_failed"])
