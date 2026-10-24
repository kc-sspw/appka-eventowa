import json
import uuid
from datetime import timedelta

import pytest
from django.contrib.sessions.models import Session
from django.test import Client
from django.utils import timezone

from accounts.models import Account, AccountSession, Membership
from accounts.services import import_accounts, reset_password
from events.security import DomainError
from game.models import Assignment, Task
from information.models import Entry, ScheduleItem

pytestmark = pytest.mark.django_db
HOST = "event-a.events.localhost"


def test_login_host_binding_and_reset(world):
    c = Client()
    assert (
        c.post(
            "/auth/login",
            {"username": world.p.username, "password": "synthetic-test-password"},
            HTTP_HOST="event-b.events.localhost",
        ).status_code
        == 400
    )
    assert (
        c.post(
            "/auth/login",
            {"username": world.p.username, "password": "synthetic-test-password"},
            HTTP_HOST=HOST,
        ).status_code
        == 302
    )
    key = c.session.session_key
    assert AccountSession.objects.filter(account=world.p, session_key=key).exists()
    assert c.get("/news", HTTP_HOST="event-b.events.localhost").status_code == 403
    assert c.get("/admin/", HTTP_HOST="platform.localhost").status_code == 403
    assert not c.cookies["sessionid"]["domain"]
    assert c.cookies["sessionid"]["httponly"]
    reset_password(world.a, world.o, world.p.pk)
    assert not Session.objects.filter(session_key=key).exists()
    assert c.get("/news", HTTP_HOST=HOST).status_code == 302


@pytest.mark.parametrize(
    "path",
    [
        "/organizer",
        "/organizer/participants",
        "/organizer/import",
        "/organizer/settings",
        "/organizer/tasks",
    ],
)
def test_participant_cannot_manage_event(world, client, path):
    client.force_login(world.p)
    assert client.get(path, HTTP_HOST=HOST).status_code == 403


def test_csrf_and_login_rate_limit(world):
    c = Client(enforce_csrf_checks=True)
    assert c.post("/auth/login", {}, HTTP_HOST=HOST).status_code == 403
    c.get("/auth/login", HTTP_HOST=HOST)
    data = {
        "username": world.p.username,
        "password": "wrong",
        "csrfmiddlewaretoken": c.cookies["csrftoken"].value,
    }
    for _ in range(10):
        assert c.post("/auth/login", data, HTTP_HOST=HOST).status_code == 400
    assert c.post("/auth/login", data, HTTP_HOST=HOST).status_code == 429


@pytest.mark.parametrize("state", ["CLOSING", "CLOSED", "EXPIRED"])
def test_closed_and_unknown_hosts(world, client, state):
    client.force_login(world.p)
    if state == "EXPIRED":
        world.a.ends_at = timezone.now() - timedelta(seconds=1)
        world.a.game_ends_at = world.a.ends_at
    else:
        world.a.state = state
    world.a.save()
    for path in ["/news", "/gallery", "/game", "/auth/login"]:
        response = client.get(path, HTTP_HOST=HOST)
        assert response.status_code == 410
        assert response["Cache-Control"] == "private, no-store"
    assert client.get("/news", HTTP_HOST="unknown.events.localhost").status_code == 404
    assert client.get("/news", HTTP_HOST="evil.invalid").status_code == 400


def test_foreign_ids_and_role_escalation(world, client, photo_factory):
    other = photo_factory(world.b, world.q)
    client.force_login(world.o)
    for path in [
        f"/organizer/participants/{world.q.pk}",
        f"/organizer/groups/{world.gb.pk}",
        f"/photos/{other.pk}",
        f"/photos/{other.pk}/content",
        f"/photos/{other.pk}/thumbnail",
    ]:
        assert client.get(path, HTTP_HOST=HOST).status_code == 404
    for path, data in [
        (f"/organizer/participants/{world.q.pk}/reset", {}),
        (f"/organizer/photos/{other.pk}/delete", {"confirm": "yes"}),
        (f"/photos/{other.pk}/score", {"value": 4}),
    ]:
        assert client.post(path, data, HTTP_HOST=HOST).status_code == 404
    before = Account.objects.count()
    response = client.post(
        "/organizer/participants/new",
        {"first_name": "Ola", "groups": [str(world.gb.pk)]},
        HTTP_HOST=HOST,
    )
    assert response.status_code == 200 and Account.objects.count() == before
    response = client.post(
        "/organizer/participants/new",
        {"first_name": "Ola", "event": str(world.b.pk), "role": "PLATFORM"},
        HTTP_HOST=HOST,
    )
    assert response.status_code == 200
    created = Account.objects.get(first_name="Ola")
    assert created.role == "PARTICIPANT" and created.event_id == world.a.pk


def test_foreign_assignment_and_own_score_denied(world, client, jpeg, photo_factory):
    other = photo_factory(world.b, world.q)
    client.force_login(world.p)
    assert (
        client.post(
            f"/assignments/{other.assignment_id}/photo",
            {"photo": jpeg(), "idempotency_key": uuid.uuid4(), "expected_version": 1},
            HTTP_HOST=HOST,
        ).status_code
        == 404
    )
    own = photo_factory(world.a, world.p)
    for suffix in ["rating", "score"]:
        assert (
            client.post(f"/photos/{own.pk}/{suffix}", {"value": 3}, HTTP_HOST=HOST).status_code
            == 403
        )


def test_group_visibility_navigation_and_xss(world, client):
    Membership.objects.create(account=world.p, group=world.ga)
    public = Entry.objects.create(
        event=world.a, kind="NEWS", title="Wszyscy", body="<script>alert(1)</script>"
    )
    private = Entry.objects.create(
        event=world.a, kind="STATIC", title="Dla grupy", body="Treść", audience="GROUPS"
    )
    private.groups.add(world.ga)
    Entry.objects.create(event=world.b, kind="NEWS", title="Obce wydarzenie", body="Sekret")
    client.force_login(world.peer)
    response = client.get("/news", HTTP_HOST=HOST)
    assert b'href="/information"' not in response.content
    assert b"&lt;script&gt;" in response.content and b"<script>alert" not in response.content
    assert "Obce wydarzenie" not in response.content.decode()
    client.force_login(world.p)
    assert b'href="/information"' in client.get("/news", HTTP_HOST=HOST).content
    assert "Dla grupy" in client.get("/information", HTTP_HOST=HOST).content.decode()
    public.published_at = timezone.now() + timedelta(days=1)
    public.save()
    assert "Wszyscy" not in client.get("/news", HTTP_HOST=HOST).content.decode()
    for hour, title in [(2, "Później"), (1, "Najpierw")]:
        ScheduleItem.objects.create(
            event=world.a, title=title, starts_at=timezone.now() + timedelta(hours=hour)
        )
    html = client.get("/information", HTTP_HOST=HOST).content.decode()
    assert html.index("Najpierw") < html.index("Później")


def payload(group=None):
    return {
        "batch_id": str(uuid.uuid4()),
        "rows": [
            dict(
                row_id=str(uuid.uuid4()),
                first_name="Ala",
                group_ids=[str(group.pk)] if group else [],
                login="u_" + uuid.uuid4().hex,
                initial_password="synthetic-initial-password",
            )
            for _ in range(2)
        ],
    }


def test_import_atomic_idempotent_and_passwords(world, client):
    data = payload(world.ga)
    client.force_login(world.o)
    responses = [
        client.post(
            "/organizer/imports", json.dumps(data), content_type="application/json", HTTP_HOST=HOST
        )
        for _ in range(2)
    ]
    assert [r.status_code for r in responses] == [200, 200]
    for row in data["rows"]:
        account = Account.objects.get(username=row["login"])
        assert account.event_id == world.a.pk and account.check_password(row["initial_password"])
        assert account.password != row["initial_password"]
        assert row["initial_password"] not in responses[0].content.decode()
        assert account.event_groups.get() == world.ga
    data["rows"][0]["first_name"] = "Inna"
    assert (
        client.post(
            "/organizer/imports", json.dumps(data), content_type="application/json", HTTP_HOST=HOST
        ).status_code
        == 409
    )


@pytest.mark.parametrize("field", ["email", "pesel", "role", "event_id", "original_row"])
def test_import_rejects_extra_data(world, field):
    data = payload()
    data["rows"][0][field] = "must-not-store"
    before = Account.objects.count()
    with pytest.raises(DomainError):
        import_accounts(world.a, world.o, data)
    assert Account.objects.count() == before


def test_reimport_only_own_accounts_no_password_or_group_updates(world):
    data = payload()
    import_accounts(world.a, world.o, data)
    data["batch_id"] = str(uuid.uuid4())
    for row in data["rows"]:
        row.update(row_id=str(uuid.uuid4()), initial_password=None, group_ids=[str(world.ga.pk)])
    import_accounts(world.a, world.o, data)
    for row in data["rows"]:
        assert not Account.objects.get(username=row["login"]).event_groups.exists()
    data["batch_id"] = str(uuid.uuid4())
    data["rows"][1]["login"] = world.q.username
    with pytest.raises(DomainError):
        import_accounts(world.a, world.o, data)


def test_task_description_immutable_after_draw(world, client):
    task = Task.objects.create(event=world.a, description="Pierwotna treść")
    Assignment.objects.create(event=world.a, account=world.p, task=task, request_id=uuid.uuid4())
    client.force_login(world.o)
    client.post(f"/organizer/tasks/{task.pk}", {"description": "Zmieniony sens"}, HTTP_HOST=HOST)
    task.refresh_from_db()
    assert task.description == "Pierwotna treść"


def test_duplicate_group_returns_form_error(world, client):
    client.force_login(world.o)
    response = client.post("/organizer/groups/new", {"name": world.ga.name}, HTTP_HOST=HOST)
    assert response.status_code == 200
    assert "już istnieje" in response.content.decode()


def test_local_storage_setup_for_new_event(world, client, settings):
    from media_storage.models import StorageConnection

    StorageConnection.objects.filter(event=world.a).delete()
    client.force_login(world.o)
    assert client.post("/organizer/storage/local", HTTP_HOST=HOST).status_code == 302
    assert StorageConnection.objects.get(event=world.a).folder_id == str(world.a.pk)
    settings.STORAGE_BACKEND = "drive"
    assert client.post("/organizer/storage/local", HTTP_HOST=HOST).status_code == 404


def test_platform_login_rate_limit(world, client):
    for _ in range(10):
        assert (
            client.post(
                "/admin/login/",
                {"username": "unknown", "password": "wrong"},
                HTTP_HOST="platform.localhost",
            ).status_code
            == 200
        )
    assert (
        client.post(
            "/admin/login/",
            {"username": "unknown", "password": "wrong"},
            HTTP_HOST="platform.localhost",
        ).status_code
        == 429
    )


def test_gallery_query_count_does_not_grow_per_photo(world, client, photo_factory, user_factory):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    photo_factory(world.a, world.p)
    client.force_login(world.p)
    with CaptureQueriesContext(connection) as first:
        assert client.get("/gallery", HTTP_HOST=HOST).status_code == 200
    for _ in range(23):
        photo_factory(world.a, user_factory(world.a))
    with CaptureQueriesContext(connection) as full:
        assert client.get("/gallery", HTTP_HOST=HOST).status_code == 200
    assert len(full) == len(first)


def test_stale_platform_edit_cannot_reopen_closed_event(world, rf):
    from django.contrib.admin.sites import AdminSite
    from django.core.exceptions import PermissionDenied

    from events.admin import EventAdmin
    from events.models import Event

    stale = world.a
    Event.objects.filter(pk=stale.pk).update(state="CLOSED")
    with pytest.raises(PermissionDenied):
        EventAdmin(Event, AdminSite()).save_model(rf.post("/admin/"), stale, None, change=True)
    assert Event.objects.get(pk=stale.pk).state == "CLOSED"
