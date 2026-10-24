import json

from django import forms
from django.contrib import auth
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods, require_POST

from events.security import DomainError, rate_limit, scoped

from .models import AccountSession
from .services import import_accounts


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Login",
        max_length=64,
        widget=forms.TextInput(attrs={"autocomplete": "username", "autocapitalize": "none"}),
    )
    password = forms.CharField(
        label="Hasło",
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


@require_http_methods(["GET", "POST"])
@sensitive_post_parameters("password")
def login(request):
    form = LoginForm(request.POST or None)
    status = 200
    if request.method == "POST" and form.is_valid():
        try:
            rate_limit(request.event, request.META.get("REMOTE_ADDR", ""), "login_ip", 30, 900)
            rate_limit(request.event, form.cleaned_data["username"], "login_account", 10, 900)
            user = auth.authenticate(request, **form.cleaned_data)
            if user is None:
                form.add_error(None, "Nieprawidłowy login lub hasło dla tego wydarzenia.")
                status = 400
            else:
                auth.login(request, user)
                AccountSession.objects.update_or_create(
                    session_key=request.session.session_key, defaults={"account": user}
                )
                return redirect("organizer" if user.role == "ORGANIZER" else "news")
        except DomainError as exc:
            form.add_error(None, exc.message)
            status = exc.status
    return render(request, "login.html", {"form": form}, status=status)


@require_POST
def logout(request):
    AccountSession.objects.filter(session_key=request.session.session_key).delete()
    auth.logout(request)
    return redirect("login")


@require_POST
@scoped("ORGANIZER")
@sensitive_variables()
@sensitive_post_parameters()
def imports(request):
    rate_limit(request.event, str(request.user.pk), "import", 10)
    if request.content_type != "application/json":
        raise DomainError("Oczekiwano JSON z dozwolonymi polami.", 400)
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        raise DomainError("Nieprawidłowy JSON.", 400)
    batch = import_accounts(request.event, request.user, payload)
    rows = list(batch.importrow_set.values("row_id", "created"))
    return JsonResponse(
        {"success": True, "data": {"batch_id": batch.batch_id, "rows": rows}, "error": None}
    )
