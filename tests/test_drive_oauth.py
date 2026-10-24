import time
import uuid
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from django.test import Client
from django.utils import timezone

from events.security import fingerprint
from media_storage.adapters import DriveStorage, StorageError
from media_storage.crypto import decrypt, encrypt
from media_storage.models import OAuthState, StorageConnection
from media_storage.oauth import SCOPE

pytestmark = pytest.mark.django_db


def adapter(event, handler):
    return DriveStorage(
        event.pk,
        "folder_123",
        credentials={"access_token": "synthetic-token", "expires_at": time.time() + 3600},
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def metadata(event, operation):
    return {
        "id": "file_123",
        "size": "123",
        "parents": ["folder_123"],
        "appProperties": {"event": str(event.pk), "operation": str(operation)},
        "trashed": False,
    }


def test_drive_upload_retry_uses_preallocated_id_and_no_public_permissions(world):
    operation = uuid.uuid4()
    calls, saved = [], []

    def handler(request):
        calls.append(request)
        assert request.headers["authorization"] == "Bearer synthetic-token"
        if request.method == "POST":
            assert request.url.params["uploadType"] == "multipart"
            assert b'"id": "file_123"' in request.content
            saved.append(metadata(world.a, operation))
            raise httpx.ReadTimeout("synthetic timeout after commit")
        if request.url.path.endswith("/file_123"):
            return httpx.Response(200, json=saved[0]) if saved else httpx.Response(404)
        return httpx.Response(200, json={"files": []})

    drive = adapter(world.a, handler)
    with pytest.raises(StorageError, match="provider_timeout"):
        drive.upload(operation, "file_123", b"jpeg")
    result = drive.upload(operation, "file_123", b"jpeg")
    assert result == {"id": "file_123", "size": 123}
    assert len([r for r in calls if r.method == "POST"]) == 1
    assert all("permissions" not in r.url.path for r in calls)


@pytest.mark.parametrize("mutation", ["event", "folder", "operation", "trashed"])
def test_drive_refuses_foreign_file_even_with_valid_id(world, mutation):
    op = uuid.uuid4()
    data = metadata(world.a, op)
    if mutation == "event":
        data["appProperties"]["event"] = str(world.b.pk)
    elif mutation == "operation":
        data["appProperties"]["operation"] = str(uuid.uuid4())
    elif mutation == "folder":
        data["parents"] = ["foreign"]
    else:
        data["trashed"] = True
    drive = adapter(world.a, lambda request: httpx.Response(200, json=data))
    with pytest.raises(StorageError, match="scope_mismatch"):
        drive.find_by_operation(op, "file_123")


def test_drive_delete_404_success_and_quota_error(world):
    calls = []

    def missing(request):
        calls.append(request.method)
        return httpx.Response(404)

    adapter(world.a, missing).delete("file_123")
    assert calls == ["GET"]

    def full(request):
        return httpx.Response(403, json={"error": {"errors": [{"reason": "storageQuotaExceeded"}]}})

    with pytest.raises(StorageError, match="quota_exceeded"):
        adapter(world.a, full).allocate_id()


def test_drive_credentials_encrypted_and_refresh(world, settings):
    credentials = {
        "access_token": "expired-synthetic",
        "refresh_token": "refresh-synthetic",
        "expires_at": 0,
    }
    connection = StorageConnection.objects.get(event=world.a)
    connection.encrypted_credentials = encrypt(credentials)
    connection.save()
    assert "refresh-synthetic" not in connection.encrypted_credentials
    assert decrypt(connection.encrypted_credentials) == credentials

    def handler(request):
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "new-synthetic", "expires_in": 3600})
        assert request.headers["authorization"] == "Bearer new-synthetic"
        return httpx.Response(200, json={"ids": ["preallocated"]})

    drive = DriveStorage(
        world.a.pk, "folder_123", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    assert drive.allocate_id() == "preallocated"
    connection.refresh_from_db()
    assert decrypt(connection.encrypted_credentials)["access_token"] == "new-synthetic"


def test_oauth_state_bound_to_session_event_and_single_use(world, settings, monkeypatch):
    settings.STORAGE_BACKEND = "drive"
    settings.GOOGLE_CLIENT_ID = "synthetic-client"
    settings.GOOGLE_CLIENT_SECRET = "synthetic-secret"
    c = Client()
    c.force_login(world.o)
    response = c.post("/organizer/storage/connect", HTTP_HOST="event-a.events.localhost")
    params = parse_qs(urlparse(response.url).query)
    assert params["scope"] == [SCOPE] and params["code_challenge_method"] == ["S256"]
    state = params["state"][0]
    monkeypatch.setattr(
        "media_storage.oauth.httpx.post",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={
                "access_token": "access-synthetic",
                "refresh_token": "refresh-synthetic",
                "expires_in": 3600,
                "scope": SCOPE,
            },
        ),
    )
    callback_client = Client()
    response = callback_client.get(
        "/oauth/callback",
        {"state": state, "code": "synthetic-code"},
        HTTP_HOST="platform.localhost",
    )
    assert response.status_code == 302
    ticket = parse_qs(urlparse(response.url).query)["ticket"][0]
    assert (
        callback_client.get(
            "/oauth/callback",
            {"state": state, "code": "synthetic-code"},
            HTTP_HOST="platform.localhost",
        ).status_code
        == 400
    )
    intruder = Client()
    intruder.force_login(world.o)
    assert (
        intruder.get(
            "/organizer/storage/finish", {"ticket": ticket}, HTTP_HOST="event-a.events.localhost"
        ).status_code
        == 404
    )
    intruder.force_login(world.other_o)
    assert (
        intruder.get(
            "/organizer/storage/finish", {"ticket": ticket}, HTTP_HOST="event-b.events.localhost"
        ).status_code
        == 404
    )
    StorageConnection.objects.filter(event=world.a).delete()
    mock_client = httpx.Client(
        transport=httpx.MockTransport(lambda r: pytest.fail("Unexpected network request"))
    )
    monkeypatch.setattr("media_storage.adapters.httpx.Client", lambda **kwargs: mock_client)
    monkeypatch.setattr(DriveStorage, "allocate_id", lambda self: "new_folder")
    monkeypatch.setattr(DriveStorage, "create_event_folder", lambda self: self.folder_id)
    monkeypatch.setattr(
        DriveStorage, "check_access", lambda self: {"owner_id": "owner", "remaining_bytes": 123}
    )
    assert (
        c.get(
            "/organizer/storage/finish", {"ticket": ticket}, HTTP_HOST="event-a.events.localhost"
        ).status_code
        == 302
    )
    assert (
        c.get(
            "/organizer/storage/finish", {"ticket": ticket}, HTTP_HOST="event-a.events.localhost"
        ).status_code
        == 404
    )
    assert StorageConnection.objects.get(event=world.a).folder_id == "new_folder"


def test_expired_oauth_rejected_without_provider_call(world, monkeypatch):
    OAuthState.objects.create(
        event=world.a,
        organizer=world.o,
        state_hash=fingerprint("expired"),
        session_hash="hash",
        verifier="v",
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    monkeypatch.setattr(
        "media_storage.oauth.httpx.post",
        lambda *a, **k: pytest.fail("Expired state reached Google"),
    )
    assert (
        Client()
        .get("/oauth/callback", {"state": "expired", "code": "x"}, HTTP_HOST="platform.localhost")
        .status_code
        == 400
    )
