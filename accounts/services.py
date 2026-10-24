import json
import re
import secrets
import uuid

from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils.crypto import constant_time_compare, salted_hmac

from events.models import Event
from events.security import DomainError, assert_actor, assert_open

from .models import Account, AccountSession, Group, ImportBatch, ImportRow, Membership


def credentials():
    return "u_" + secrets.token_hex(10), secrets.token_urlsafe(24)


def resolve_groups(event, ids):
    try:
        ids = {uuid.UUID(str(value)) for value in ids}
    except (TypeError, ValueError):
        raise DomainError("Nieprawidłowe grupy.", 400)
    groups = list(Group.objects.filter(event=event, pk__in=ids))
    if len(groups) != len(ids):
        from django.http import Http404

        raise Http404
    return groups


def next_number(event):
    return (
        Account.objects.filter(event=event).aggregate(value=Max("public_number"))["value"] or 0
    ) + 1


@transaction.atomic
def create_participant(event, actor, first_name, group_ids=()):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, actor, "ORGANIZER")
    assert_open(event)
    groups = resolve_groups(event, group_ids)
    username, password = credentials()
    account = Account.objects.create_user(
        username, password, event=event, first_name=first_name, public_number=next_number(event)
    )
    for group in groups:
        Membership.objects.create(account=account, group=group)
    return account, password


@transaction.atomic
def reset_password(event, actor, account_id):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, actor, "ORGANIZER")
    assert_open(event)
    account = get_object_or_404(Account, pk=account_id, event=event, role="PARTICIPANT")
    password = credentials()[1]
    account.set_password(password)
    account.save(update_fields=["password"])
    Session.objects.filter(
        session_key__in=AccountSession.objects.filter(account=account).values("session_key")
    ).delete()
    AccountSession.objects.filter(account=account).delete()
    return account, password


@transaction.atomic
def import_accounts(event, actor, payload):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, actor, "ORGANIZER")
    assert_open(event)
    if not isinstance(payload, dict) or set(payload) != {"batch_id", "rows"}:
        raise DomainError("Niedozwolone pola importu.", 400)
    try:
        batch_id = uuid.UUID(payload["batch_id"])
    except (ValueError, TypeError, AttributeError):
        raise DomainError("Nieprawidłowy identyfikator importu.", 400)
    rows = payload["rows"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise DomainError("Import obsługuje od 1 do 500 wierszy.", 400)
    row_ids, logins, prepared = set(), set(), []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "row_id",
            "first_name",
            "group_ids",
            "login",
            "initial_password",
        }:
            raise DomainError(
                "Import przyjmuje wyłącznie imię, grupy i techniczne dane konta.", 400
            )
        try:
            row_id = uuid.UUID(row["row_id"])
        except (ValueError, TypeError, AttributeError):
            raise DomainError("Nieprawidłowy identyfikator wiersza.", 400)
        name, login, password = row["first_name"], row["login"], row["initial_password"]
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
            raise DomainError("Każdy wiersz musi zawierać samo imię (do 60 znaków).", 400)
        if not isinstance(login, str) or not re.fullmatch(r"u_[a-z0-9]{20,48}", login):
            raise DomainError("Nieprawidłowy login techniczny.", 400)
        if row_id in row_ids or login in logins:
            raise DomainError("Powtórzony wiersz lub login.", 400)
        row_ids.add(row_id)
        logins.add(login)
        if not isinstance(row["group_ids"], list):
            raise DomainError("Nieprawidłowe grupy.", 400)
        groups = resolve_groups(event, row["group_ids"])
        if password is not None and (
            not isinstance(password, str) or not 22 <= len(password) <= 128
        ):
            raise DomainError("Nieprawidłowe hasło początkowe.", 400)
        prepared.append((row_id, name.strip(), login, password, groups))
    # Fingerprint only the allowed technical payload. No source spreadsheet cell/hash is accepted.
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = salted_hmac("import-batch", canonical, algorithm="sha256").hexdigest()
    batch = ImportBatch.objects.filter(event=event, batch_id=batch_id).first()
    if batch:
        if not constant_time_compare(batch.fingerprint, digest):
            raise DomainError("Ten identyfikator importu ma już inną zawartość.")
        return batch
    batch = ImportBatch.objects.create(event=event, batch_id=batch_id, fingerprint=digest)
    number = next_number(event)
    for row_id, name, login, password, groups in prepared:
        existing = Account.objects.filter(username=login).first()
        if password is None:
            if not existing or existing.event_id != event.id or existing.role != "PARTICIPANT":
                raise DomainError("Nieznany login lub login spoza tego wydarzenia.", 400)
            account, created = existing, False
        else:
            if existing:
                raise DomainError("Login już istnieje. Reimport nie zmienia haseł.")
            account = Account.objects.create_user(
                login, password, event=event, first_name=name, public_number=number
            )
            number += 1
            created = True
            Membership.objects.bulk_create([Membership(account=account, group=g) for g in groups])
        ImportRow.objects.create(batch=batch, row_id=row_id, account=account, created=created)
    return batch
