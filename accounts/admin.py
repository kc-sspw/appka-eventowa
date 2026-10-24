from django import forms
from django.contrib import admin
from django.contrib.auth.password_validation import validate_password

from .models import Account
from .services import credentials, next_number


class AccountAdminForm(forms.ModelForm):
    new_password = forms.CharField(
        label="Nowe hasło (minimum 16 znaków)", required=False, widget=forms.PasswordInput
    )

    class Meta:
        model = Account
        fields = ("username", "event", "first_name", "role", "is_active")

    def clean_new_password(self):
        value = self.cleaned_data["new_password"]
        if value:
            validate_password(value)
        elif not self.instance.pk or not self.instance.password:
            raise forms.ValidationError("Ustaw początkowe hasło.")
        return value

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get("new_password"):
            obj.set_password(self.cleaned_data["new_password"])
        if commit:
            obj.save()
        return obj


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    form = AccountAdminForm
    list_display = ("username", "role", "event", "is_active")
    list_filter = ("role", "event")
    exclude = ("password", "last_login", "public_number")

    def get_readonly_fields(self, request, obj=None):
        return ("event", "role", "username") if obj else ()

    def get_changeform_initial_data(self, request):
        return {"username": credentials()[0]}

    def save_model(self, request, obj, form, change):
        from django.db import transaction

        from events.models import Event
        from events.security import assert_open

        with transaction.atomic():
            if obj.event_id:
                event = Event.objects.select_for_update().get(pk=obj.event_id)
                assert_open(event)
                if not obj.public_number:
                    obj.public_number = next_number(event)
            super().save_model(request, obj, form, change)
