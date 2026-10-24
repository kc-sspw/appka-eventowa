import secrets

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404

from events.models import Event
from events.security import DomainError, assert_actor, assert_open

from .models import Assignment, Comment, OrganizerScore, ParticipantRating, Photo, Task


@transaction.atomic
def draw(event, account, request_id):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, account, "PARTICIPANT")
    assert_open(event, game=True)
    previous = Assignment.objects.filter(
        event=event, account=account, request_id=request_id
    ).first()
    if previous:
        return previous
    assignments = Assignment.objects.filter(event=event, account=account)
    if assignments.filter(status="ACTIVE").count() >= 5:
        raise DomainError("Masz już 5 zadań do wykonania. Dodaj zdjęcie, aby wylosować kolejne.")
    pool = (
        Task.objects.filter(event=event, active=True)
        .exclude(pk__in=assignments.values("task_id"))
        .annotate(usage=Count("assignment"))
        .order_by("usage")
    )
    first = pool.first()
    if not first:
        raise DomainError("Nie ma już nowych zadań w puli.")
    task = secrets.choice(list(pool.filter(usage=first.usage)))
    return Assignment.objects.create(event=event, account=account, task=task, request_id=request_id)


@transaction.atomic
def withdraw(event, organizer, task_id):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, organizer, "ORGANIZER")
    assert_open(event)
    task = get_object_or_404(Task, event=event, pk=task_id)
    task.active = False
    task.save(update_fields=["active"])
    Assignment.objects.filter(event=event, task=task, status="ACTIVE").update(status="CANCELLED")


def current_photo(event, photo_id):
    return get_object_or_404(
        Photo.objects.select_related("assignment__account", "assignment__task", "operation"),
        event=event,
        assignment__event=event,
        assignment__status="COMPLETED",
        operation__event=event,
        pk=photo_id,
    )


@transaction.atomic
def rate(event, account, photo_id, value, organizer=False):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, account, "ORGANIZER" if organizer else "PARTICIPANT")
    assert_open(event)
    photo = current_photo(event, photo_id)
    if not organizer and photo.assignment.account_id == account.pk:
        raise PermissionDenied
    if not isinstance(value, int) or not (0 if organizer else 1) <= value <= 5:
        raise DomainError("Ocena poza skalą.", 400)
    if organizer:
        OrganizerScore.objects.update_or_create(
            photo=photo, defaults={"value": value, "organizer": account}
        )
    else:
        ParticipantRating.objects.update_or_create(
            photo=photo, participant=account, defaults={"value": value}
        )


@transaction.atomic
def comment(event, account, photo_id, text):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, account)
    assert_open(event)
    photo = current_photo(event, photo_id)
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 1000:
        raise DomainError("Komentarz musi mieć od 1 do 1000 znaków.", 400)
    return Comment.objects.create(event=event, photo=photo, author=account, text=text.strip())


@transaction.atomic
def delete_comment(event, account, comment_id):
    event = Event.objects.select_for_update().get(pk=event.pk)
    assert_actor(event, account)
    assert_open(event)
    obj = get_object_or_404(Comment, event=event, photo__event=event, pk=comment_id)
    if account.role != "ORGANIZER" and obj.author_id != account.pk:
        raise PermissionDenied
    photo_id = obj.photo_id
    obj.delete()
    return photo_id
