"""Sequential synthetic baseline; deliberately not a concurrent load/SLA test."""

import json
import platform
import time
import uuid
from pathlib import Path

import pytest
from django.db import connection
from django.db.models import Count
from django.test import Client

from game.models import Photo, Task
from game.services import draw
from media_storage.services import upload_photo

pytestmark = pytest.mark.django_db


def test_200_accounts_50_tasks_sequential_baseline(event_factory, user_factory, jpeg):
    event = event_factory("capacity")
    t = time.perf_counter()
    users = [user_factory(event) for _ in range(200)]
    accounts_seconds = time.perf_counter() - t
    Task.objects.bulk_create([Task(event=event, description=f"Kadr {i}") for i in range(50)])
    t = time.perf_counter()
    assignments = [draw(event, user, uuid.uuid4()) for user in users]
    draw_seconds = time.perf_counter() - t
    assert set(Task.objects.annotate(n=Count("assignment")).values_list("n", flat=True)) == {4}
    t = time.perf_counter()
    for user, assignment in zip(users[:24], assignments[:24]):
        upload_photo(event, user, assignment.pk, uuid.uuid4(), 0, jpeg())
    upload_seconds = time.perf_counter() - t
    assert Photo.objects.filter(event=event).count() == 24
    client = Client()
    client.force_login(users[0])
    t = time.perf_counter()
    response = client.get("/gallery", HTTP_HOST="capacity.events.localhost")
    gallery_seconds = time.perf_counter() - t
    assert response.status_code == 200
    result = {
        "python": platform.python_version(),
        "database": connection.vendor,
        "accounts": 200,
        "tasks": 50,
        "draws": 200,
        "generated_photos": 24,
        "accounts_seconds": round(accounts_seconds, 3),
        "draw_seconds": round(draw_seconds, 3),
        "upload_seconds": round(upload_seconds, 3),
        "gallery_html_seconds": round(gallery_seconds, 3),
        "limits": "Sequential service calls, test MD5 hasher, 80x60 generated JPEG, FakeStorage; no cloud/network or concurrent load.",
    }
    root = Path("test-results")
    root.mkdir(exist_ok=True)
    (root / "capacity.json").write_text(json.dumps(result, indent=2))
