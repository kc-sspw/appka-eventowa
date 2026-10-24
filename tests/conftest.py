import io
import uuid
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from accounts.models import Account, Group
from events.models import Event
from game.models import Photo, Task
from game.services import draw
from media_storage.adapters import FakeStorage
from media_storage.models import StorageConnection
from media_storage.services import upload_photo


@pytest.fixture(autouse=True)
def private_settings(settings, tmp_path):
    settings.DEBUG = True
    settings.PRIVATE_ROOT = tmp_path
    settings.FILE_UPLOAD_TEMP_DIR = str(tmp_path / "incoming")
    (tmp_path / "incoming").mkdir()


@pytest.fixture
def event_factory():
    def create(slug=None, **kwargs):
        now = timezone.now()
        values = dict(
            slug=slug or uuid.uuid4().hex,
            name="Syntetyczne wydarzenie",
            starts_at=now - timedelta(days=1),
            ends_at=now + timedelta(days=2),
            game_starts_at=now - timedelta(hours=1),
            game_ends_at=now + timedelta(days=1),
            state="ACTIVE",
        )
        values.update(kwargs)
        event = Event.objects.create(**values)
        folder = FakeStorage(event.pk).create_event_folder()
        StorageConnection.objects.create(event=event, folder_id=folder, owner_id="local")
        return event

    return create


@pytest.fixture
def user_factory():
    def create(event, role="PARTICIPANT", **kwargs):
        return Account.objects.create_user(
            "u_" + uuid.uuid4().hex,
            "synthetic-test-password",
            event=event,
            role=role,
            first_name="Ala",
            **kwargs,
        )

    return create


@pytest.fixture
def world(event_factory, user_factory):
    a, b = event_factory("event-a"), event_factory("event-b")
    return SimpleNamespace(
        a=a,
        b=b,
        p=user_factory(a),
        peer=user_factory(a),
        o=user_factory(a, "ORGANIZER"),
        q=user_factory(b),
        other_o=user_factory(b, "ORGANIZER"),
        ga=Group.objects.create(event=a, name="Zieloni"),
        gb=Group.objects.create(event=b, name="Niebiescy"),
    )


@pytest.fixture
def jpeg():
    def create(color="red", size=(80, 60)):
        output = io.BytesIO()
        Image.new("RGB", size, color).save(output, "JPEG")
        return SimpleUploadedFile("synthetic.jpg", output.getvalue(), content_type="image/jpeg")

    return create


@pytest.fixture
def photo_factory(jpeg):
    def create(event, account):
        Task.objects.create(event=event, description="Syntetyczny kadr " + uuid.uuid4().hex)
        assignment = draw(event, account, uuid.uuid4())
        upload_photo(event, account, assignment.pk, uuid.uuid4(), 0, jpeg())
        return Photo.objects.get(assignment=assignment)

    return create
