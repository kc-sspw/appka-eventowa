from django.contrib.auth.backends import ModelBackend

from .models import Account


class EventBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is None:
            return None
        event = getattr(request, "event", None)
        account = Account.objects.filter(username=username, event=event).first()
        if account is None:
            Account().set_password(password)
            return None
        if account.check_password(password) and account.is_active:
            if event is None and account.role != "PLATFORM":
                return None
            return account
