from django import forms

from accounts.models import Group

from .models import Entry, ScheduleItem


class AudienceForm(forms.ModelForm):
    def __init__(self, *args, event, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.event = event
        self.fields["groups"].queryset = Group.objects.filter(event=event)
        self.fields["groups"].label = "Grupy odbiorców"
        self.fields["groups"].widget = forms.CheckboxSelectMultiple()
        self.fields["groups"].widget.choices = self.fields["groups"].choices
        for field in self.fields.values():
            if isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(
                    format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
                )

    def clean(self):
        data = super().clean()
        if data.get("audience") == "GROUPS" and not data.get("groups"):
            self.add_error("groups", "Wybierz co najmniej jedną grupę.")
        if data.get("audience") == "ALL":
            data["groups"] = Group.objects.none()
        return data


class EntryForm(AudienceForm):
    class Meta:
        model = Entry
        fields = ["kind", "title", "body", "pinned", "published_at", "audience", "groups"]
        labels = {
            "kind": "Rodzaj",
            "title": "Tytuł",
            "body": "Treść",
            "pinned": "Przypnij",
            "published_at": "Publikacja (Warszawa)",
            "audience": "Odbiorcy",
        }


class ScheduleForm(AudienceForm):
    class Meta:
        model = ScheduleItem
        fields = ["title", "starts_at", "ends_at", "location", "description", "audience", "groups"]
        labels = {
            "title": "Tytuł",
            "starts_at": "Początek (Warszawa)",
            "ends_at": "Koniec (Warszawa)",
            "location": "Miejsce",
            "description": "Opis",
            "audience": "Odbiorcy",
        }
