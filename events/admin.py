from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction

from .lifecycle import clean_event
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "state", "ends_at", "cleanup_failed")
    readonly_fields = ("state", "cleaned_at", "cleanup_failed")
    actions = ["retry_cleanup"]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.state in {"CLOSING", "CLOSED"}:
            return tuple(f.name for f in Event._meta.fields)
        return self.readonly_fields + (("slug",) if obj else ())

    def has_delete_permission(self, request, obj=None):
        return False  # Slugs remain permanently reserved.

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                current = Event.objects.select_for_update().get(pk=obj.pk)
                if current.state in {"CLOSING", "CLOSED"}:
                    raise PermissionDenied("Zamykanego wydarzenia nie można edytować.")
                obj.state = current.state
                obj.slug = current.slug
                obj.cleaned_at = current.cleaned_at
                obj.cleanup_failed = current.cleanup_failed
            super().save_model(request, obj, form, change)

    @admin.action(description="Ponów porządkowanie zamykanych wydarzeń")
    def retry_cleanup(self, request, queryset):
        for event in queryset.filter(state="CLOSING"):
            clean_event(event.pk)
        self.message_user(request, "Ponowiono sprzątanie. Sprawdź status.", messages.INFO)
