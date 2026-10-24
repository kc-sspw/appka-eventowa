import uuid

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from events.security import DomainError, rate_limit, scoped
from information.models import Entry, ScheduleItem
from information.services import visible
from media_storage.adapters import StorageError, storage_for
from media_storage.cache import thumbnail
from media_storage.models import StorageOperation
from media_storage.services import moderate, upload_photo

from .models import Assignment, Photo
from .services import comment, current_photo, delete_comment, draw, rate


@require_GET
@scoped()
def news(request):
    return render(
        request,
        "news.html",
        {"entries": visible(Entry, request.event, request.user).filter(kind="NEWS")},
    )


@require_GET
@scoped()
def information(request):
    return render(
        request,
        "information.html",
        {
            "entries": visible(Entry, request.event, request.user).filter(kind="STATIC"),
            "schedule": visible(ScheduleItem, request.event, request.user),
        },
    )


@require_GET
@scoped()
def game(request):
    assignments = list(
        Assignment.objects.filter(event=request.event, account=request.user)
        .select_related("task", "photo")
        .order_by("assigned_at")
    )
    for assignment in assignments:
        assignment.upload_key = uuid.uuid4()
    now, event = timezone.now(), request.event
    playable = (
        event.state == "ACTIVE"
        and event.game_starts_at
        and event.game_starts_at <= now < event.game_ends_at
    )
    return render(
        request,
        "game.html",
        {
            "active": [a for a in assignments if a.status == "ACTIVE"],
            "completed": [a for a in assignments if a.status == "COMPLETED"],
            "archived": [a for a in assignments if a.status in {"REMOVED", "CANCELLED"}],
            "playable": playable,
            "draw_key": uuid.uuid4(),
            "operations": StorageOperation.objects.filter(
                event=event, account=request.user, action="UPLOAD"
            )
            .exclude(status="DONE")
            .order_by("-created_at")[:10],
        },
    )


@require_POST
@scoped("PARTICIPANT")
def draw_view(request):
    rate_limit(request.event, str(request.user.pk), "draw", 30)
    try:
        key = uuid.UUID(request.POST.get("request_id", ""))
    except ValueError:
        raise DomainError("Brak identyfikatora losowania. Odśwież stronę.", 400)
    draw(request.event, request.user, key)
    messages.success(request, "Nowe zadanie czeka na zdjęcie.")
    return redirect("game")


@require_POST
@scoped("PARTICIPANT")
def upload(request, assignment_id):
    rate_limit(request.event, str(request.user.pk), "upload", 10)
    # Parsing may stop at an oversized file before later multipart form fields.
    data = request.POST
    if getattr(request, "upload_too_large", False):
        raise DomainError("Zdjęcie przekracza 15 MiB.", 413)
    try:
        key = uuid.UUID(data.get("idempotency_key", ""))
        version = int(data.get("expected_version", ""))
    except ValueError:
        raise DomainError("Nieprawidłowa wersja lub identyfikator uploadu.", 400)
    file = request.FILES.get("photo")
    if not file:
        raise DomainError("Wybierz zdjęcie JPEG, PNG lub WebP.", 400)
    upload_photo(request.event, request.user, assignment_id, key, version, file)
    messages.success(request, "Zdjęcie potwierdzone. Zadanie wykonane!")
    return redirect("game")


@require_GET
@scoped()
def gallery(request):
    photos = (
        Photo.objects.filter(
            event=request.event,
            assignment__event=request.event,
            assignment__status="COMPLETED",
            operation__event=request.event,
        )
        .select_related("assignment__account", "assignment__task", "organizer_score")
        .annotate(average=Avg("ratings__value"), votes=Count("ratings"))
    )
    photos = photos.order_by("-created_at", "id")
    if request.GET.get("mine") == "1":
        photos = photos.filter(assignment__account=request.user)
    return render(
        request, "gallery.html", {"page": Paginator(photos, 24).get_page(request.GET.get("page"))}
    )


@require_GET
@scoped()
def photo_detail(request, photo_id):
    photo = current_photo(request.event, photo_id)
    stats = photo.ratings.aggregate(average=Avg("value"), votes=Count("id"))
    own = photo.ratings.filter(participant=request.user).first()
    return render(
        request,
        "photo.html",
        {
            "photo": photo,
            "stats": stats,
            "own": own,
            "comments": photo.comments.select_related("author"),
            "scale": range(1, 6),
            "organizer_scale": range(0, 6),
        },
    )


@require_GET
@scoped()
def photo_content(request, photo_id, small=False):
    photo = current_photo(request.event, photo_id)
    try:
        if small:
            response = HttpResponse(thumbnail(request.event, photo), content_type="image/jpeg")
        else:
            iterator = iter(storage_for(request.event).read(photo.operation.external_file_id))
            first = next(
                iterator
            )  # Provider failures before streaming can return a proper error page.

            def stream():
                yield first
                yield from iterator

            response = StreamingHttpResponse(stream(), content_type="image/jpeg")
        response["Cache-Control"] = "private, no-store"
        response["Content-Disposition"] = 'inline; filename="zdjecie.jpg"'
        return response
    except StorageError:
        raise DomainError("Zdjęcie jest chwilowo niedostępne.", 503) from None


@require_POST
@scoped()
def rating(request, photo_id, organizer=False):
    rate_limit(request.event, str(request.user.pk), "rating", 40)
    try:
        value = int(request.POST.get("value", ""))
    except ValueError:
        raise DomainError("Wybierz ocenę.", 400)
    rate(request.event, request.user, photo_id, value, organizer)
    return redirect("photo", photo_id=photo_id)


@require_POST
@scoped()
def add_comment(request, photo_id):
    rate_limit(request.event, str(request.user.pk), "comment", 10)
    comment(request.event, request.user, photo_id, request.POST.get("text", ""))
    return redirect("photo", photo_id=photo_id)


@require_POST
@scoped()
def remove_comment(request, comment_id):
    photo_id = delete_comment(request.event, request.user, comment_id)
    return redirect("photo", photo_id=photo_id)


@require_POST
@scoped("ORGANIZER")
def remove_photo(request, photo_id):
    if request.POST.get("confirm") != "yes":
        raise DomainError("Potwierdź usunięcie zdjęcia.", 400)
    moderate(request.event, request.user, photo_id)
    messages.success(request, "Zdjęcie ukryte. Worker usuwa plik z magazynu.")
    return redirect("gallery")
