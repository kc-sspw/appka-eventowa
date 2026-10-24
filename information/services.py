from django.db.models import Q
from django.utils import timezone

from .models import Entry, ScheduleItem


def visible(model, event, account):
    queryset = model.objects.filter(event=event)
    if account.role != "ORGANIZER":
        queryset = queryset.filter(
            Q(audience="ALL") | Q(groups__in=account.event_groups.filter(event=event))
        ).distinct()
        if model is Entry:
            queryset = queryset.filter(published_at__lte=timezone.now())
    return queryset


def navigation(request):
    event = getattr(request, "event", None)
    if not event or not request.user.is_authenticated or request.user.event_id != event.id:
        return {}
    return {
        "has_information": visible(Entry, event, request.user).filter(kind="STATIC").exists()
        or visible(ScheduleItem, event, request.user).exists()
    }
