from django.contrib import admin, messages

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

    @admin.action(description="Ponów porządkowanie zamykanych wydarzeń")
    def retry_cleanup(self, request, queryset):
        for event in queryset.filter(state="CLOSING"):
            clean_event(event.pk)
        self.message_user(request, "Ponowiono sprzątanie. Sprawdź status.", messages.INFO)
