import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import close_old_connections, connection, connections

from accounts.models import Account, ImportBatch
from accounts.services import import_accounts
from events.lifecycle import begin_close, clean_event
from events.models import Event
from events.security import DomainError
from game.models import Assignment, Photo, Task
from game.services import draw
from media_storage.adapters import FakeStorage
from media_storage.images import normalize
from media_storage.models import StorageOperation
from media_storage.services import finalize, moderate, reserve, usage
from tests.test_access import payload

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.concurrency]


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks required; SQLite is not evidence of concurrency safety")


def race(*functions):
    barrier = threading.Barrier(len(functions))

    def invoke(fn):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                return fn()
            except DomainError as exc:
                return exc
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=len(functions)) as pool:
        futures = [pool.submit(invoke, fn) for fn in functions]
        return [f.result(timeout=30) for f in futures]


def test_simultaneous_draw_at_four_active_never_six(world):
    Task.objects.bulk_create([Task(event=world.a, description=str(i)) for i in range(12)])
    for _ in range(4):
        draw(world.a, world.p, uuid.uuid4())
    results = race(*[lambda: draw(world.a, world.p, uuid.uuid4()) for _ in range(4)])
    assert sum(isinstance(r, Assignment) for r in results) == 1
    assert Assignment.objects.filter(account=world.p, status="ACTIVE").count() == 5


def test_simultaneous_same_request_and_same_import(world):
    Task.objects.bulk_create([Task(event=world.a, description=str(i)) for i in range(10)])
    key = uuid.uuid4()
    results = race(*[lambda: draw(world.a, world.p, key) for _ in range(3)])
    assert len({r.pk for r in results}) == 1
    data = payload(world.ga)
    before = Account.objects.count()
    results = race(*[lambda: import_accounts(world.a, world.o, data) for _ in range(3)])
    assert len({r.pk for r in results}) == 1
    assert Account.objects.count() == before + 2 and ImportBatch.objects.count() == 1


def test_simultaneous_budget_reservations(world, settings):
    world.a.storage_budget = settings.PHOTO_MAX_BYTES
    world.a.save()
    Task.objects.bulk_create([Task(event=world.a, description=str(i)) for i in range(2)])
    assignments = [draw(world.a, world.p, uuid.uuid4()) for _ in range(2)]
    results = race(
        *[lambda a=a: reserve(world.a, world.p, a.pk, uuid.uuid4(), 0) for a in assignments]
    )
    assert sum(isinstance(r, tuple) for r in results) == 1
    assert usage(world.a) == settings.PHOTO_MAX_BYTES


def test_simultaneous_replacements_publish_one_version(world, photo_factory, jpeg):
    photo = photo_factory(world.a, world.p)
    adapter = FakeStorage(world.a.pk)
    operations = [
        reserve(world.a, world.p, photo.assignment_id, uuid.uuid4(), 1)[0] for _ in range(2)
    ]
    results = [adapter.upload(op.pk, adapter.allocate_id(), normalize(jpeg())) for op in operations]
    outcomes = race(
        *[
            lambda op=op, result=result: finalize(op, result)
            for op, result in zip(operations, results)
        ]
    )
    assert outcomes.count(True) == 1 and outcomes.count(False) == 1
    assert Photo.objects.get(assignment_id=photo.assignment_id).version == 2
    assert StorageOperation.objects.filter(event=world.a, action="DELETE").count() == 2


def test_moderation_wins_after_concurrent_reservation(world, photo_factory):
    photo = photo_factory(world.a, world.p)
    race(
        lambda: reserve(world.a, world.p, photo.assignment_id, uuid.uuid4(), 1),
        lambda: moderate(world.a, world.o, photo.pk),
    )
    assert not Photo.objects.exists()
    assert Assignment.objects.get(pk=photo.assignment_id).status == "REMOVED"


def test_close_and_finalize_never_restore_gallery(world, photo_factory, jpeg):
    photo = photo_factory(world.a, world.p)
    op, _ = reserve(world.a, world.p, photo.assignment_id, uuid.uuid4(), 1)
    adapter = FakeStorage(world.a.pk)
    result = adapter.upload(op.pk, adapter.allocate_id(), normalize(jpeg()))
    race(lambda: finalize(op, result), lambda: begin_close(world.a, world.o))
    clean_event(world.a.pk)
    assert not Photo.objects.filter(event=world.a).exists()
    assert Event.objects.get(pk=world.a.pk).state == "CLOSED"
