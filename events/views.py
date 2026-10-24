from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.models import Account, Group, Membership
from accounts.services import create_participant, reset_password
from game.models import Task
from game.services import withdraw
from information.forms import EntryForm, ScheduleForm
from information.models import Entry, ScheduleItem
from media_storage.adapters import FakeStorage, StorageError, storage_for
from media_storage.models import StorageConnection, StorageOperation
from media_storage.services import usage

from .forms import EventForm, GroupForm, ParticipantForm, TaskForm
from .lifecycle import begin_close
from .models import Event
from .security import DomainError, assert_open, scoped

CRUD = {
    "groups": (Group, GroupForm, "Grupy"),
    "entries": (Entry, EntryForm, "Publikacje"),
    "schedule": (ScheduleItem, ScheduleForm, "Plan ramowy"),
    "tasks": (Task, TaskForm, "Pula zadań"),
}


@require_GET
@scoped("ORGANIZER")
def organizer(request):
    conn = StorageConnection.objects.filter(event=request.event).first()
    context = {
        "participants": Account.objects.filter(event=request.event, role="PARTICIPANT").count(),
        "tasks": Task.objects.filter(event=request.event, active=True).count(),
        "used_mib": round(usage(request.event) / 1024**2, 2),
        "budget_mib": request.event.storage_budget // 1024**2,
        "connection": conn,
        "operations": StorageOperation.objects.filter(event=request.event)
        .exclude(action="UPLOAD", status="DONE")
        .order_by("-created_at")[:40],
    }
    context["local_storage"] = settings.STORAGE_BACKEND == "fake"
    return render(request, "organizer.html", context)


@require_POST
@scoped("ORGANIZER")
def storage_local(request):
    if not settings.DEBUG or settings.STORAGE_BACKEND != "fake":
        raise Http404
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=request.event.pk)
        assert_open(event)
        folder = FakeStorage(event.pk).create_event_folder()
        StorageConnection.objects.get_or_create(
            event=event, defaults={"folder_id": folder, "owner_id": "local"}
        )
    messages.success(request, "Lokalny magazyn testowy jest gotowy.")
    return redirect("organizer")


@require_http_methods(["GET", "POST"])
@scoped("ORGANIZER")
def settings_view(request):
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=request.event.pk)
        assert_open(event)
        form = EventForm(request.POST or None, instance=event)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "Ustawienia zapisane.")
            return redirect("organizer")
    return render(request, "form.html", {"form": form, "title": "Ustawienia wydarzenia"})


@require_POST
@scoped("ORGANIZER")
def activate(request):
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=request.event.pk)
        assert_open(event)
        if not event.game_starts_at or not Task.objects.filter(event=event, active=True).exists():
            raise DomainError("Ustaw terminy gry i dodaj zadania przed aktywacją.")
        event.state = "ACTIVE"
        event.save(update_fields=["state"])
    messages.success(request, "Wydarzenie jest aktywne.")
    return redirect("organizer")


@require_http_methods(["GET", "POST"])
@scoped("ORGANIZER")
def edit(request, kind, object_id=None):
    if kind not in CRUD:
        raise Http404
    model, form_class, title = CRUD[kind]
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=request.event.pk)
        assert_open(event)
        instance = get_object_or_404(model, event=event, pk=object_id) if object_id else None
        form = form_class(request.POST or None, instance=instance, event=event)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "Zapisano.")
            return redirect("entity_list", kind=kind)
    return render(request, "form.html", {"form": form, "title": title})


@require_GET
@scoped("ORGANIZER")
def entity_list(request, kind):
    if kind not in CRUD:
        raise Http404
    model, _, title = CRUD[kind]
    return render(
        request,
        "entity_list.html",
        {"objects": model.objects.filter(event=request.event), "kind": kind, "title": title},
    )


@require_POST
@scoped("ORGANIZER")
def delete_entity(request, kind, object_id):
    if kind not in CRUD:
        raise Http404
    if kind == "tasks":
        withdraw(request.event, request.user, object_id)
    else:
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=request.event.pk)
            assert_open(event)
            obj = get_object_or_404(CRUD[kind][0], event=event, pk=object_id)
            obj.delete()
    messages.success(request, "Wycofano zadanie." if kind == "tasks" else "Usunięto.")
    return redirect("entity_list", kind=kind)


@require_GET
@scoped("ORGANIZER")
def participants(request):
    from django.core.paginator import Paginator

    accounts = (
        Account.objects.filter(event=request.event, role="PARTICIPANT")
        .prefetch_related("event_groups")
        .order_by("public_number")
    )
    return render(
        request,
        "participants.html",
        {"page": Paginator(accounts, 50).get_page(request.GET.get("page"))},
    )


@require_http_methods(["GET", "POST"])
@scoped("ORGANIZER")
def participant_edit(request, account_id=None):
    account = (
        get_object_or_404(Account, event=request.event, role="PARTICIPANT", pk=account_id)
        if account_id
        else None
    )
    form = ParticipantForm(
        request.POST or None,
        event=request.event,
        initial={"first_name": account.first_name, "groups": account.event_groups.all()}
        if account
        else None,
    )
    if request.method == "POST" and form.is_valid():
        if account:
            with transaction.atomic():
                event = Event.objects.select_for_update().get(pk=request.event.pk)
                assert_open(event)
                account = get_object_or_404(Account, event=event, role="PARTICIPANT", pk=account.pk)
                account.first_name = form.cleaned_data["first_name"]
                account.save(update_fields=["first_name"])
                Membership.objects.filter(account=account).delete()
                Membership.objects.bulk_create(
                    [Membership(account=account, group=g) for g in form.cleaned_data["groups"]]
                )
            return redirect("participants")
        account, password = create_participant(
            request.event,
            request.user,
            form.cleaned_data["first_name"],
            [g.pk for g in form.cleaned_data["groups"]],
        )
        return render(request, "credentials.html", {"account": account, "password": password})
    return render(request, "form.html", {"form": form, "title": "Uczestnik"})


@require_POST
@scoped("ORGANIZER")
def participant_reset(request, account_id):
    account, password = reset_password(request.event, request.user, account_id)
    return render(request, "credentials.html", {"account": account, "password": password})


@require_GET
@scoped("ORGANIZER")
def import_view(request):
    groups = list(Group.objects.filter(event=request.event).values("id", "name"))
    return render(request, "import.html", {"groups": groups})


@require_POST
@scoped("ORGANIZER")
def storage_check(request):
    try:
        access = storage_for(request.event).check_access()
        remaining = access["remaining_bytes"]
        message = "Połączenie działa." + (
            f" Wolne miejsce konta: {remaining // 1024**2} MiB."
            if remaining is not None
            else " Dostawca nie zwrócił limitu miejsca."
        )
        messages.success(request, message)
    except StorageError:
        messages.error(request, "Magazyn jest niedostępny. Sprawdź połączenie i uprawnienia.")
    return redirect("organizer")


@require_POST
@scoped("ORGANIZER")
def retry(request, operation_id):
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=request.event.pk)
        assert_open(event)
        op = get_object_or_404(StorageOperation, event=event, pk=operation_id)
        if op.status == "RETRY":
            op.next_attempt_at = timezone.now()
            op.save(update_fields=["next_attempt_at"])
    messages.success(request, "Worker ponowi oczekującą operację.")
    return redirect("organizer")


@require_http_methods(["GET", "POST"])
@scoped("ORGANIZER")
def close(request):
    if request.method == "POST":
        if request.POST.get("confirm") != request.event.slug:
            raise DomainError("Wpisz slug wydarzenia, aby potwierdzić zamknięcie.", 400)
        begin_close(request.event, request.user)
        return redirect("cleanup")
    return render(
        request,
        "close.html",
        {"connection": StorageConnection.objects.filter(event=request.event).first()},
    )


@require_GET
@scoped("ORGANIZER")
def cleanup(request):
    return render(request, "cleanup.html")
