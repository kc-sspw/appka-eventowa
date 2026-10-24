import base64
import hashlib
import secrets
import time
from datetime import timedelta
from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_GET, require_POST

from events.models import Event
from events.security import DomainError, assert_actor, assert_open, fingerprint, scoped

from .adapters import DriveStorage, StorageError
from .crypto import decrypt, encrypt
from .models import OAuthState, StorageConnection

SCOPE = "https://www.googleapis.com/auth/drive.file"


def origin(host):
    port = ":" + settings.PUBLIC_PORT if settings.PUBLIC_PORT else ""
    return f"{settings.PUBLIC_SCHEME}://{host}{port}"


def callback_url():
    return origin(settings.PLATFORM_HOST) + "/oauth/callback"


@require_POST
@scoped("ORGANIZER")
@sensitive_variables()
def start(request):
    if (
        settings.STORAGE_BACKEND != "drive"
        or not settings.GOOGLE_CLIENT_ID
        or not settings.TOKEN_KEY
    ):
        raise DomainError("Operator platformy musi skonfigurować Google OAuth.", 503)
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=request.event.pk)
        assert_open(event)
        OAuthState.objects.create(
            event=event,
            organizer=request.user,
            state_hash=fingerprint(state),
            session_hash=fingerprint(request.session.session_key),
            verifier=verifier,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    return redirect(
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(
            {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": callback_url(),
                "response_type": "code",
                "scope": SCOPE,
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
    )


@require_GET
@sensitive_variables()
def callback(request):
    # No event cookie on callback host: exchange first, then bind finalization to the original session.
    if not request.is_platform:
        raise Http404
    state_hash = fingerprint(request.GET.get("state", ""))
    with transaction.atomic():
        state = (
            OAuthState.objects.select_for_update()
            .filter(
                state_hash=state_hash,
                stage="OPEN",
                expires_at__gt=timezone.now(),
                organizer__role="ORGANIZER",
            )
            .first()
        )
        if not state or state.organizer.event_id != state.event_id:
            return HttpResponse("Nieprawidłowy lub wykorzystany stan OAuth.", status=400)
        state.stage = "EXCHANGED"
        state.save(update_fields=["stage"])
    if request.GET.get("error") or not request.GET.get("code"):
        state.delete()
        return HttpResponse(
            "Połączenie nie zostało zatwierdzone. Wróć do panelu wydarzenia.", status=400
        )
    try:
        response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": request.GET["code"],
                "code_verifier": state.verifier,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": callback_url(),
                "grant_type": "authorization_code",
            },
            timeout=30,
        )
        data = response.json()
        if (
            response.status_code != 200
            or SCOPE not in data.get("scope", "").split()
            or not data.get("refresh_token")
        ):
            raise ValueError
        credentials = {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": time.time() + data["expires_in"],
        }
        ticket = secrets.token_urlsafe(32)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=state.event_id)
            assert_open(event)
            if not OAuthState.objects.filter(pk=state.pk, stage="EXCHANGED").update(
                stage="RETURN",
                ticket_hash=fingerprint(ticket),
                encrypted_credentials=encrypt(credentials),
                verifier="",
            ):
                raise ValueError
        response = redirect(
            origin(event.slug + "." + settings.EVENT_DOMAIN)
            + "/organizer/storage/finish?ticket="
            + ticket
        )
        response["Referrer-Policy"] = "no-referrer"
        return response
    except (httpx.HTTPError, ValueError, KeyError, DomainError):
        state.delete()
        return HttpResponse(
            "Nie udało się połączyć Google Drive. Rozpocznij ponownie w panelu.", status=400
        )


@require_GET
@scoped("ORGANIZER")
@sensitive_variables()
def finish(request):
    state = OAuthState.objects.filter(
        event=request.event,
        organizer=request.user,
        stage="RETURN",
        expires_at__gt=timezone.now(),
        ticket_hash=fingerprint(request.GET.get("ticket", "")),
        session_hash=fingerprint(request.session.session_key),
    ).first()
    if not state:
        raise Http404
    credentials = decrypt(state.encrypted_credentials)
    previous = StorageConnection.objects.filter(event=request.event).first()
    adapter = DriveStorage(
        request.event.pk, previous.folder_id if previous else "", credentials=credentials
    )
    try:
        if previous:
            access = adapter.check_access()
            if previous.owner_id and previous.owner_id != access["owner_id"]:
                raise StorageError("wrong_owner")
            folder_id = previous.folder_id
        else:
            folder_id = adapter.allocate_id()
            adapter.folder_id = folder_id
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=request.event.pk)
            assert_open(event)
            assert_actor(event, request.user, "ORGANIZER")
            consumed = OAuthState.objects.filter(pk=state.pk, stage="RETURN").delete()[0]
            if not consumed:
                raise DomainError("Połączenie zostało już wykorzystane.")
            current = StorageConnection.objects.filter(event=event).first()
            if current and current.folder_id != folder_id:
                raise DomainError("Magazyn został już połączony. Spróbuj ponownie.")
            StorageConnection.objects.update_or_create(
                event=event,
                defaults={"folder_id": folder_id, "encrypted_credentials": encrypt(credentials)},
            )
        adapter.create_event_folder()
        access = adapter.check_access()
        StorageConnection.objects.filter(event=request.event, folder_id=folder_id).update(
            owner_id=access["owner_id"]
        )
    except StorageError:
        raise DomainError(
            "Nie udało się potwierdzić magazynu. Połącz ponownie to samo konto; folder zostanie zachowany.",
            503,
        ) from None
    return redirect("organizer")
