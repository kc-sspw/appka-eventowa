import hashlib
from datetime import timedelta
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone

from .models import Event, RateBucket


class DomainError(Exception):
    def __init__(self, message, status=409):
        self.message = message
        self.status = status
        super().__init__(message)


def assert_actor(event, actor, role=None):
    if not actor.is_authenticated or actor.event_id != event.id or not actor.is_active:
        raise PermissionDenied
    if role and actor.role != role:
        raise PermissionDenied


def assert_open(event, game=False):
    now = timezone.now()
    if event.state not in (Event.State.ACTIVE, Event.State.DRAFT) or now >= event.ends_at:
        raise DomainError("Wydarzenie jest zamknięte.", 410)
    if game and (
        event.state != Event.State.ACTIVE
        or not event.game_starts_at
        or not event.game_starts_at <= now < event.game_ends_at
    ):
        raise DomainError("Gra nie jest teraz aktywna.")


def scoped(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            assert_actor(request.event, request.user, role)
            try:
                return view(request, *args, **kwargs)
            except DomainError as exc:
                if (
                    request.content_type == "application/json"
                    or request.headers.get("Accept") == "application/json"
                ):
                    return JsonResponse(
                        {"success": False, "data": None, "error": exc.message}, status=exc.status
                    )
                from django.shortcuts import render

                return render(request, "error.html", {"error": exc.message}, status=exc.status)

        return wrapped

    return decorator


def rate_limit(event, identity, action, limit, seconds=60):
    # HMAC-like keyed digest, no raw address/login in DB; DB serializes counters across workers.
    from django.utils.crypto import salted_hmac

    key = salted_hmac(
        "rate", f"{event.pk if event else 'platform'}:{action}:{identity}", algorithm="sha256"
    ).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        bucket, _ = RateBucket.objects.get_or_create(
            key=key, defaults={"event": event, "expires_at": now + timedelta(seconds=seconds)}
        )
        bucket = RateBucket.objects.select_for_update().get(pk=bucket.pk)
        if bucket.expires_at <= now:
            bucket.count = 0
            bucket.expires_at = now + timedelta(seconds=seconds)
        if bucket.count >= limit:
            raise DomainError("Za dużo prób. Poczekaj chwilę i spróbuj ponownie.", 429)
        bucket.count += 1
        bucket.save(update_fields=["count", "expires_at"])


def fingerprint(value):
    return hashlib.sha256(value.encode()).hexdigest()
