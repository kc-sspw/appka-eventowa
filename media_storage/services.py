import hashlib
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from events.models import Event
from events.security import DomainError, assert_actor, assert_open
from game.models import Assignment, Photo
from game.services import current_photo

from .adapters import StorageError, storage_for
from .cache import purge_photo
from .images import normalize
from .models import StorageOperation

LEASE_SECONDS = 180


def usage(event):
    return (
        StorageOperation.objects.filter(event=event).aggregate(total=Sum("reserved_bytes"))["total"]
        or 0
    )


def _delete_later(operation):
    operation.action = "DELETE"
    operation.status = "PENDING"
    operation.lease_until = None
    operation.lease_token = None
    operation.next_attempt_at = timezone.now()
    operation.save(
        update_fields=["action", "status", "lease_until", "lease_token", "next_attempt_at"]
    )


@transaction.atomic
def reserve(event, account, assignment_id, key, expected_version):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, account, "PARTICIPANT")
    assert_open(event, game=True)
    assignment = get_object_or_404(
        Assignment.objects.select_for_update(),
        event=event,
        account=account,
        task__event=event,
        pk=assignment_id,
    )
    existing = StorageOperation.objects.filter(pk=key).first()
    if existing:
        if (
            existing.event_id != event.pk
            or existing.assignment_id != assignment.pk
            or existing.account_id != account.pk
        ):
            from django.http import Http404

            raise Http404
        if existing.expected_version != expected_version:
            raise DomainError("Klucz uploadu jest przypisany do innej wersji.")
        if existing.action == "UPLOAD" and existing.status == "DONE":
            return existing, False
        if existing.action != "UPLOAD" or existing.status in {"CANCELLED"}:
            raise DomainError("Ta operacja nie może być ponowiona. Odśwież zadanie.")
        if existing.lease_until and existing.lease_until > timezone.now():
            raise DomainError("Zdjęcie jest przesyłane. Poczekaj i odśwież zadania.")
    if assignment.version != expected_version or assignment.status not in {"ACTIVE", "COMPLETED"}:
        raise DomainError("Stan zadania zmienił się. Odśwież stronę.")
    extra = settings.PHOTO_MAX_BYTES - (existing.reserved_bytes if existing else 0)
    if usage(event) + extra > event.storage_budget:
        raise DomainError("Wyczerpano budżet zdjęć wydarzenia. Skontaktuj się z organizatorem.")
    operation = existing or StorageOperation(
        id=key,
        event=event,
        assignment=assignment,
        account=account,
        expected_version=expected_version,
    )
    operation.reserved_bytes = settings.PHOTO_MAX_BYTES
    operation.status = "PROCESSING"
    operation.lease_token = uuid.uuid4()
    operation.lease_until = timezone.now() + timedelta(seconds=LEASE_SECONDS)
    operation.error_code = ""
    operation.save()
    return operation, True


@transaction.atomic
def fail(operation, code, needs_input=False):
    Event.objects.select_for_update().get(pk=operation.event_id)
    current = StorageOperation.objects.filter(
        pk=operation.pk, event_id=operation.event_id, lease_token=operation.lease_token
    ).first()
    if not current:
        return
    current.status = "NEEDS_INPUT" if needs_input and not current.external_file_id else "RETRY"
    current.error_code = code
    current.attempts += 1
    current.next_attempt_at = timezone.now() + timedelta(
        seconds=min(3600, 10 * 2 ** min(current.attempts, 8))
    )
    current.lease_until = None
    current.lease_token = None
    if current.status == "NEEDS_INPUT":
        current.reserved_bytes = 0
    current.save()


@transaction.atomic
def finalize(operation, result):
    event = Event.objects.select_for_update().get(pk=operation.event_id)
    current = StorageOperation.objects.filter(
        pk=operation.pk, event=event, lease_token=operation.lease_token, action="UPLOAD"
    ).first()
    if not current:
        return False
    assignment = (
        Assignment.objects.select_for_update()
        .filter(
            pk=current.assignment_id,
            event=event,
            account_id=current.account_id,
            account__event=event,
            task__event=event,
        )
        .first()
    )
    current.external_file_id = result["id"]
    current.reserved_bytes = int(result["size"])
    current.save(update_fields=["external_file_id", "reserved_bytes"])
    now = timezone.now()
    valid = (
        assignment
        and event.state == "ACTIVE"
        and event.game_starts_at
        and event.game_starts_at <= now < event.game_ends_at
        and now < event.ends_at
        and assignment.status in {"ACTIVE", "COMPLETED"}
        and assignment.version == current.expected_version
        and 0 < current.reserved_bytes <= settings.PHOTO_MAX_BYTES
    )
    if not valid:
        _delete_later(current)
        return False
    old = (
        Photo.objects.filter(event=event, assignment=assignment).select_related("operation").first()
    )
    if old:
        purge_photo(old)
        _delete_later(old.operation)
        old.delete()  # Cascades ratings/comments: they describe the old image.
    assignment.version += 1
    assignment.status = "COMPLETED"
    assignment.save(update_fields=["version", "status"])
    Photo.objects.create(
        event=event,
        assignment=assignment,
        operation=current,
        version=assignment.version,
        bytes=current.reserved_bytes,
    )
    current.status = "DONE"
    current.lease_until = None
    current.lease_token = None
    current.error_code = ""
    current.save(update_fields=["status", "lease_until", "lease_token", "error_code"])
    return True


def upload_photo(event, account, assignment_id, key, expected_version, upload):
    operation, claimed = reserve(event, account, assignment_id, key, expected_version)
    if not claimed:
        return operation
    try:
        content = normalize(upload)
        digest = hashlib.sha256(content).hexdigest()
        if operation.content_digest and operation.content_digest != digest:
            fail(operation, "different_input")
            raise DomainError(
                "Ponowienie musi używać tego samego zdjęcia. Odśwież stronę, aby rozpocząć nowy upload."
            )
        adapter = storage_for(event)
        file_id = operation.external_file_id or adapter.allocate_id()
        with transaction.atomic():
            locked = Event.objects.select_for_update().get(pk=event.pk)
            assert_open(locked, game=True)
            updated = StorageOperation.objects.filter(
                pk=operation.pk, event=locked, lease_token=operation.lease_token, action="UPLOAD"
            ).update(external_file_id=file_id, content_digest=digest)
            if not updated:
                raise DomainError("Upload został anulowany.")
        operation.external_file_id = file_id
        # Never hold Event/Assignment locks across provider calls.
        result = adapter.upload(operation.pk, file_id, content)
        if not finalize(operation, result):
            raise DomainError(
                "Zdjęcie nie zostało opublikowane: zmienił się stan zadania lub wydarzenia."
            )
        operation.refresh_from_db()
        return operation
    except StorageError as exc:
        fail(operation, exc.code)
        raise DomainError(
            "Magazyn zdjęć jest niedostępny. Zdjęcie nie zostało zaliczone; sprawdź status i ponów próbę.",
            503,
        ) from None
    except DomainError:
        fail(operation, "invalid_or_conflicting_upload", needs_input=True)
        raise
    finally:
        # UploadedFile closes and removes Django's private temporary input.
        upload.close()


@transaction.atomic
def moderate(event, organizer, photo_id):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, organizer, "ORGANIZER")
    assert_open(event)
    photo = current_photo(event, photo_id)
    assignment = Assignment.objects.select_for_update().get(pk=photo.assignment_id, event=event)
    assignment.status = "REMOVED"
    assignment.version += 1
    assignment.save(update_fields=["status", "version"])
    purge_photo(photo)
    _delete_later(photo.operation)
    photo.delete()


def run_operation(operation_id):
    """Claim with a lease/fencing token. No binaries, paths or arbitrary file IDs in jobs."""
    snapshot = StorageOperation.objects.filter(pk=operation_id).first()
    if not snapshot:
        return
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=snapshot.event_id)
        op = StorageOperation.objects.select_for_update().get(pk=operation_id, event=event)
        if op.status in {"DONE", "CANCELLED", "NEEDS_INPUT"} or op.next_attempt_at > timezone.now():
            return
        if op.lease_until and op.lease_until > timezone.now():
            return
        # Corrupt cross-event assignment payloads are rejected before provider access.
        if (
            op.assignment_id
            and not Assignment.objects.filter(
                pk=op.assignment_id,
                event=event,
                account_id=op.account_id,
                account__event=event,
                task__event=event,
            ).exists()
        ):
            op.status, op.error_code = "RETRY", "scope_mismatch"
            op.next_attempt_at = timezone.now() + timedelta(hours=1)
            op.save(update_fields=["status", "error_code", "next_attempt_at"])
            return
        op.lease_token = uuid.uuid4()
        op.lease_until = timezone.now() + timedelta(seconds=LEASE_SECONDS)
        op.status = "PROCESSING"
        op.save(update_fields=["lease_token", "lease_until", "status"])
    try:
        adapter = storage_for(event)
        if op.action == "DELETE":
            found = adapter.find_by_operation(op.pk, op.external_file_id)
            if found:
                adapter.delete(found["id"])
            with transaction.atomic():
                Event.objects.select_for_update().get(pk=event.pk)
                StorageOperation.objects.filter(
                    pk=op.pk, event=event, lease_token=op.lease_token
                ).update(
                    status="DONE",
                    reserved_bytes=0,
                    external_file_id="",
                    lease_until=None,
                    lease_token=None,
                    error_code="",
                )
        else:
            found = adapter.find_by_operation(op.pk, op.external_file_id)
            if found:
                finalize(op, found)
            else:
                with transaction.atomic():
                    Event.objects.select_for_update().get(pk=event.pk)
                    StorageOperation.objects.filter(
                        pk=op.pk, event=event, lease_token=op.lease_token
                    ).update(
                        status="NEEDS_INPUT",
                        reserved_bytes=0,
                        lease_until=None,
                        lease_token=None,
                        error_code="choose_photo_again",
                    )
    except StorageError as exc:
        fail(op, exc.code)
