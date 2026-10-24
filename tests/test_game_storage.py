import io
import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.http import Http404
from django.utils import timezone
from PIL import Image

from accounts.models import Account, ImportBatch
from events.lifecycle import begin_close, clean_event
from events.models import Event
from events.security import DomainError
from game.models import Assignment, Comment, OrganizerScore, ParticipantRating, Photo, Task
from game.services import comment, delete_comment, draw, rate, withdraw
from media_storage.adapters import FakeStorage, StorageError
from media_storage.cache import thumbnail
from media_storage.images import normalize
from media_storage.models import StorageConnection, StorageOperation
from media_storage.services import finalize, moderate, reserve, run_operation, upload_photo, usage

pytestmark = pytest.mark.django_db


def due(op):
    StorageOperation.objects.filter(pk=op.pk).update(
        next_attempt_at=timezone.now() - timedelta(seconds=1),
        lease_until=timezone.now() - timedelta(seconds=1),
    )
    run_operation(op.pk)
    op.refresh_from_db()


def test_draw_fairness_no_repeats_and_limit(world, photo_factory):
    Task.objects.bulk_create([Task(event=world.a, description=str(i)) for i in range(8)])
    key = uuid.uuid4()
    first = draw(world.a, world.p, key)
    assert draw(world.a, world.p, key) == first
    for _ in range(4):
        draw(world.a, world.p, uuid.uuid4())
    with pytest.raises(DomainError):
        draw(world.a, world.p, uuid.uuid4())
    other = draw(world.a, world.peer, uuid.uuid4())
    assert other.task_id not in world.p.assignment_set.values_list("task_id", flat=True)
    withdraw(world.a, world.o, first.task_id)
    assert Assignment.objects.get(pk=first.pk).status == "CANCELLED"
    draw(world.a, world.p, uuid.uuid4())
    assert Assignment.objects.filter(account=world.p, status="ACTIVE").count() == 5


@pytest.mark.parametrize("timing", ["before", "after", "empty", "exhausted", "draft"])
def test_draw_unavailable(world, timing):
    task = Task.objects.create(event=world.a, description="Jedno zadanie")
    if timing == "before":
        world.a.game_starts_at = timezone.now() + timedelta(hours=1)
    elif timing == "after":
        world.a.game_ends_at = timezone.now() - timedelta(seconds=1)
    elif timing == "empty":
        task.delete()
    elif timing == "draft":
        world.a.state = "DRAFT"
    else:
        a = draw(world.a, world.p, uuid.uuid4())
        a.status = "COMPLETED"
        a.save()
    world.a.save()
    with pytest.raises(DomainError):
        draw(world.a, world.p, uuid.uuid4())


def test_replacement_clears_interactions_and_delays_budget_release(world, photo_factory, jpeg):
    old = photo_factory(world.a, world.p)
    thumbnail(world.a, old)
    rate(world.a, world.peer, old.pk, 4)
    rate(world.a, world.o, old.pk, 0, organizer=True)
    comment(world.a, world.peer, old.pk, "Poprzednie zdjęcie")
    upload_photo(world.a, world.p, old.assignment_id, uuid.uuid4(), 1, jpeg("blue"))
    new = Photo.objects.get(assignment_id=old.assignment_id)
    assert new.pk != old.pk and new.version == 2
    assert (
        not ParticipantRating.objects.exists()
        and not OrganizerScore.objects.exists()
        and not Comment.objects.exists()
    )
    old.operation.refresh_from_db()
    assert old.operation.action == "DELETE" and old.operation.reserved_bytes > 0
    assert usage(world.a) == old.bytes + new.bytes
    due(old.operation)
    assert usage(world.a) == new.bytes
    assert (
        not FakeStorage(world.a.pk)
        ._path(old.operation.external_file_id or str(uuid.uuid4()))
        .exists()
    )


@pytest.mark.parametrize("fault", ["before", "after", "full", "denied"])
def test_upload_fault_preserves_old_and_recovery(world, photo_factory, jpeg, monkeypatch, fault):
    old = photo_factory(world.a, world.p)
    key = uuid.uuid4()
    monkeypatch.setattr(FakeStorage, "fault", fault)
    with pytest.raises(DomainError, match="niedostępny"):
        upload_photo(world.a, world.p, old.assignment_id, key, 1, jpeg("blue"))
    assert Photo.objects.get(assignment_id=old.assignment_id).pk == old.pk
    op = StorageOperation.objects.get(pk=key)
    monkeypatch.setattr(FakeStorage, "fault", None)
    due(op)
    if fault == "after":
        assert op.status == "DONE"
        assert Photo.objects.get(assignment_id=old.assignment_id).version == 2
    else:
        assert op.status == "NEEDS_INPUT"
        assert Photo.objects.get(assignment_id=old.assignment_id).pk == old.pk
        upload_photo(world.a, world.p, old.assignment_id, key, 1, jpeg("blue"))
    assert StorageOperation.objects.filter(pk=key).count() == 1


def test_db_failure_after_provider_write_recovers_without_duplicate(
    world, photo_factory, jpeg, monkeypatch
):
    old = photo_factory(world.a, world.p)
    key = uuid.uuid4()
    with monkeypatch.context() as m:
        m.setattr(
            "media_storage.services.finalize",
            lambda *args: (_ for _ in ()).throw(DatabaseError("synthetic")),
        )
        with pytest.raises(DatabaseError):
            upload_photo(world.a, world.p, old.assignment_id, key, 1, jpeg("blue"))
    op = StorageOperation.objects.get(pk=key)
    due(op)
    assert op.status == "DONE"
    assert Photo.objects.get(assignment_id=old.assignment_id).version == 2
    assert len(list(FakeStorage(world.a.pk).root.glob("*.jpg"))) == 2


def test_upload_idempotence_and_foreign_key(world, photo_factory, jpeg):
    photo = photo_factory(world.a, world.p)
    repeated = upload_photo(world.a, world.p, photo.assignment_id, photo.operation_id, 0, jpeg())
    assert repeated.pk == photo.operation_id and Photo.objects.count() == 1
    other = photo_factory(world.b, world.q)
    with pytest.raises(Http404):
        upload_photo(world.b, world.q, other.assignment_id, photo.operation_id, 1, jpeg())


def test_budget_counts_pending_delete_and_reservations(world, photo_factory, jpeg, settings):
    photo = photo_factory(world.a, world.p)
    world.a.storage_budget = settings.PHOTO_MAX_BYTES
    world.a.save()
    with pytest.raises(DomainError, match="budżet"):
        upload_photo(world.a, world.p, photo.assignment_id, uuid.uuid4(), 1, jpeg())
    moderate(world.a, world.o, photo.pk)
    assert usage(world.a) == photo.bytes
    due(photo.operation)
    assert usage(world.a) == 0


def test_competing_versions_and_moderation_win(world, photo_factory, jpeg):
    photo = photo_factory(world.a, world.p)
    adapter = FakeStorage(world.a.pk)
    operations = [
        reserve(world.a, world.p, photo.assignment_id, uuid.uuid4(), 1)[0] for _ in range(2)
    ]
    results = [adapter.upload(op.pk, adapter.allocate_id(), normalize(jpeg())) for op in operations]
    assert finalize(operations[0], results[0])
    assert not finalize(operations[1], results[1])
    current = Photo.objects.get(assignment_id=photo.assignment_id)
    op, _ = reserve(world.a, world.p, current.assignment_id, uuid.uuid4(), 2)
    result = adapter.upload(op.pk, adapter.allocate_id(), normalize(jpeg()))
    moderate(world.a, world.o, current.pk)
    assert not finalize(op, result)
    assert not Photo.objects.exists()
    assert Assignment.objects.get(pk=current.assignment_id).status == "REMOVED"


def test_scores_and_comments_enforce_roles(world, photo_factory):
    photo = photo_factory(world.a, world.p)
    for value in [1, 5]:
        rate(world.a, world.peer, photo.pk, value)
    assert photo.ratings.count() == 1 and photo.ratings.get().value == 5
    for value in [0, 6]:
        with pytest.raises(DomainError):
            rate(world.a, world.peer, photo.pk, value)
    with pytest.raises(PermissionDenied):
        rate(world.a, world.p, photo.pk, 5)
    with pytest.raises(PermissionDenied):
        rate(world.a, world.peer, photo.pk, 5, organizer=True)
    for value in [0, 5]:
        rate(world.a, world.o, photo.pk, value, organizer=True)
    assert OrganizerScore.objects.count() == 1
    c = comment(world.a, world.peer, photo.pk, "Tekst")
    with pytest.raises(PermissionDenied):
        delete_comment(world.a, world.p, c.pk)
    delete_comment(world.a, world.o, c.pk)
    with pytest.raises(DomainError):
        comment(world.a, world.p, photo.pk, "x" * 1001)


def test_close_cleans_content_preserves_album_and_other_event(world, photo_factory, settings):
    photo = photo_factory(world.a, world.p)
    other = photo_factory(world.b, world.q)
    thumbnail(world.a, photo)
    path = FakeStorage(world.a.pk)._path(photo.operation.external_file_id)
    begin_close(world.a, world.o)
    clean_event(world.a.pk)
    clean_event(world.a.pk)
    world.a.refresh_from_db()
    assert world.a.state == "CLOSED" and world.a.cleaned_at
    assert (
        not world.a.instructions and world.a.storage_budget == 0 and world.a.game_starts_at is None
    )
    for model in [
        Account,
        Task,
        Assignment,
        Photo,
        StorageOperation,
        StorageConnection,
        ImportBatch,
    ]:
        assert not model.objects.filter(event=world.a).exists()
    assert path.exists() and Photo.objects.filter(pk=other.pk).exists()
    assert not (settings.PRIVATE_ROOT / "thumbnails" / str(world.a.pk)).exists()
    assert Event.objects.filter(slug="event-a").exists()


def test_close_with_failed_delete_removes_data_but_waits_for_provider(
    world, photo_factory, monkeypatch
):
    photo = photo_factory(world.a, world.p)
    moderate(world.a, world.o, photo.pk)
    monkeypatch.setattr(FakeStorage, "fault", "delete")
    begin_close(world.a, world.o)
    clean_event(world.a.pk)
    world.a.refresh_from_db()
    assert world.a.state == "CLOSING" and world.a.cleanup_failed
    assert not Account.objects.filter(event=world.a).exists()
    assert StorageConnection.objects.filter(event=world.a).exists()
    monkeypatch.setattr(FakeStorage, "fault", None)
    due(photo.operation)
    clean_event(world.a.pk)
    world.a.refresh_from_db()
    assert world.a.state == "CLOSED"


def test_close_rejects_inflight_upload_and_worker_handles_crashed_upload(
    world, photo_factory, jpeg
):
    photo = photo_factory(world.a, world.p)
    op, _ = reserve(world.a, world.p, photo.assignment_id, uuid.uuid4(), 1)
    adapter = FakeStorage(world.a.pk)
    result = adapter.upload(op.pk, adapter.allocate_id(), normalize(jpeg()))
    begin_close(world.a, world.o)
    clean_event(world.a.pk)
    world.a.refresh_from_db()
    assert world.a.state == "CLOSING"
    assert not finalize(op, result)
    due(op)
    clean_event(world.a.pk)
    world.a.refresh_from_db()
    assert world.a.state == "CLOSED"
    assert not adapter._path(result["id"]).exists()


def test_corrupt_worker_scope_rejected_before_provider(world, photo_factory, monkeypatch):
    photo = photo_factory(world.b, world.q)
    op = StorageOperation.objects.create(
        event=world.a,
        assignment=photo.assignment,
        account=world.p,
        action="DELETE",
        status="PENDING",
        external_file_id=photo.operation.external_file_id,
    )
    monkeypatch.setattr(
        "media_storage.services.storage_for",
        lambda *args: pytest.fail("Provider touched with foreign assignment"),
    )
    run_operation(op.pk)
    op.refresh_from_db()
    assert op.error_code == "scope_mismatch"


def test_image_normalization_strips_metadata_and_rotates():
    source = io.BytesIO()
    exif = Image.Exif()
    exif[274] = 6
    exif[315] = "synthetic-author-must-disappear"
    Image.new("RGB", (100, 60), "green").save(source, "JPEG", exif=exif)
    result = normalize(
        SimpleUploadedFile("image.jpg", source.getvalue(), content_type="image/jpeg")
    )
    image = Image.open(io.BytesIO(result))
    assert image.size == (60, 100) and not image.getexif()
    assert b"synthetic-author" not in result and len(result) <= 1024**2


@pytest.mark.parametrize("kind", ["mime", "invalid", "bytes", "pixels", "animation"])
def test_bad_images_rejected(jpeg, settings, kind):
    file = jpeg()
    if kind == "mime":
        file.content_type = "image/png"
    elif kind == "invalid":
        file = SimpleUploadedFile("bad.jpg", b"not an image", content_type="image/jpeg")
    elif kind == "bytes":
        settings.UPLOAD_MAX_BYTES = 10
    elif kind == "pixels":
        # Header-only image: dimensions trigger the guard before decompression.
        import struct
        import zlib

        def chunk(name, data):
            return (
                struct.pack(">I", len(data))
                + name
                + data
                + struct.pack(">I", zlib.crc32(name + data))
            )

        data = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 10000, 10000, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", b"")
            + chunk(b"IEND", b"")
        )
        file = SimpleUploadedFile("big.png", data, content_type="image/png")
    else:
        buffer = io.BytesIO()
        Image.new("RGB", (10, 10), "red").save(
            buffer, "WEBP", save_all=True, append_images=[Image.new("RGB", (10, 10), "blue")]
        )
        file = SimpleUploadedFile("animated.webp", buffer.getvalue(), content_type="image/webp")
    with pytest.raises(DomainError):
        normalize(file)


def test_fake_storage_disabled_without_debug(world, settings):
    settings.DEBUG = False
    with pytest.raises(StorageError):
        FakeStorage(world.a.pk)


def test_close_removes_scoped_admin_logs_and_temporary_uploads(world, settings, user_factory):
    from django.contrib.admin.models import ADDITION, LogEntry
    from django.contrib.contenttypes.models import ContentType

    platform = user_factory(None, "PLATFORM")
    for account in [world.p, world.q]:
        LogEntry.objects.create(
            user=platform,
            content_type=ContentType.objects.get_for_model(Account),
            object_id=str(account.pk),
            object_repr="Synthetic name",
            action_flag=ADDITION,
        )
        directory = settings.PRIVATE_ROOT / "incoming" / str(account.event_id)
        directory.mkdir(parents=True)
        (directory / "synthetic.upload").write_bytes(b"private")
    begin_close(world.a, world.o)
    clean_event(world.a.pk)
    assert not LogEntry.objects.filter(object_id=str(world.p.pk)).exists()
    assert LogEntry.objects.filter(object_id=str(world.q.pk)).exists()
    assert not (settings.PRIVATE_ROOT / "incoming" / str(world.a.pk)).exists()
    assert (settings.PRIVATE_ROOT / "incoming" / str(world.b.pk) / "synthetic.upload").exists()


def test_multipart_upload_uses_private_event_temp_and_size_limit(world, client, jpeg, settings):
    task = Task.objects.create(event=world.a, description="Syntetyczne zdjęcie")
    assignment = draw(world.a, world.p, uuid.uuid4())
    assert assignment.task_id == task.pk
    client.force_login(world.p)

    def send():
        return client.post(
            f"/assignments/{assignment.pk}/photo",
            {"photo": jpeg(), "idempotency_key": str(uuid.uuid4()), "expected_version": 0},
            HTTP_HOST="event-a.events.localhost",
        )

    settings.UPLOAD_MAX_BYTES = 10
    assert send().status_code == 413
    settings.UPLOAD_MAX_BYTES = 15 * 1024**2
    assert send().status_code == 302
    assert Photo.objects.filter(assignment=assignment).exists()
    assert not list((settings.PRIVATE_ROOT / "incoming").rglob("*.upload"))


def test_manual_cleanup_requires_closing_exact_file_and_explicit_verification(
    world, photo_factory, monkeypatch
):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    photo = photo_factory(world.a, world.p)
    moderate(world.a, world.o, photo.pk)
    file_id = photo.operation.external_file_id
    args = ["confirm_storage_absence", world.a.slug, str(photo.operation_id)]
    with pytest.raises(CommandError):
        call_command(*args, file_id=file_id, verified_absent=True)
    begin_close(world.a, world.o)
    monkeypatch.setattr(FakeStorage, "fault", "delete")
    clean_event(world.a.pk)
    with pytest.raises(CommandError):
        call_command(*args, file_id=file_id)
    with pytest.raises(CommandError):
        call_command(*args, file_id="wrong-file", verified_absent=True)
    with pytest.raises(CommandError):
        call_command(
            "confirm_storage_absence",
            world.a.slug,
            "invalid-uuid",
            file_id=file_id,
            verified_absent=True,
        )
    monkeypatch.setattr(FakeStorage, "fault", None)
    FakeStorage(world.a.pk).delete(file_id)  # Independent operator verification/action.
    call_command(*args, file_id=file_id, verified_absent=True, stdout=io.StringIO())
    world.a.refresh_from_db()
    assert world.a.state == "CLOSED"
    assert StorageConnection.objects.filter(event=world.b).exists()
