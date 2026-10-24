import re

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone

from .models import Event


class HostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        request.event = None
        request.is_platform = host == settings.PLATFORM_HOST
        if request.is_platform:
            if not (request.path.startswith("/admin/") or request.path == "/oauth/callback"):
                return HttpResponse("Platforma — /admin/", status=404)
        else:
            suffix = "." + settings.EVENT_DOMAIN
            slug = host[: -len(suffix)] if host.endswith(suffix) else ""
            if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", slug):
                return HttpResponse("Nie znaleziono.", status=404)
            request.event = Event.objects.filter(slug=slug).first()
            if request.event is None:
                return HttpResponse("Nie znaleziono.", status=404)
            if request.path.startswith("/admin/") or request.path == "/oauth/callback":
                return HttpResponse("Nie znaleziono.", status=404)
        response = self.get_response(request)
        response["Cache-Control"] = "private, no-store"
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        response.setdefault("Referrer-Policy", "same-origin")
        return response


class EventAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user, event = request.user, request.event
        if request.is_platform:
            if request.path == "/admin/login/" and request.method == "POST":
                from .security import DomainError, rate_limit

                try:
                    rate_limit(
                        None, request.META.get("REMOTE_ADDR", ""), "platform_login_ip", 30, 900
                    )
                    rate_limit(
                        None, request.POST.get("username", ""), "platform_login_account", 10, 900
                    )
                except DomainError as exc:
                    return HttpResponse(exc.message, status=exc.status)
            if user.is_authenticated and user.role != "PLATFORM":
                return HttpResponse("Brak dostępu.", status=403)
        elif event:
            if user.is_authenticated and user.event_id != event.id:
                return HttpResponse("Brak dostępu.", status=403)
            closing = event.state in ("CLOSING", "CLOSED") or event.ends_at <= timezone.now()
            if closing:
                allowed = (
                    event.state != "CLOSED"
                    and user.is_authenticated
                    and user.role == "ORGANIZER"
                    and request.path in {"/organizer/cleanup", "/auth/logout"}
                )
                if not allowed:
                    return HttpResponse(
                        "Wydarzenie jest niedostępne.",
                        status=410,
                        headers={"Cache-Control": "private, no-store"},
                    )
            elif event.state == "DRAFT" and user.is_authenticated and user.role == "PARTICIPANT":
                return HttpResponse("Wydarzenie jest w przygotowaniu.", status=403)
        return self.get_response(request)
