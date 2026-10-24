from django import forms
from django.conf import settings

from accounts.models import Group
from game.models import Task
from media_storage.services import usage

from .models import Event


class EventForm(forms.ModelForm):
    budget_mib = forms.IntegerField(
        label="Budżet zdjęć (MiB)", min_value=1, max_value=settings.STORAGE_MAX_BUDGET // 1024**2
    )

    class Meta:
        model = Event
        fields = ["name", "starts_at", "ends_at", "game_starts_at", "game_ends_at", "instructions"]
        labels = {
            "name": "Nazwa wydarzenia",
            "starts_at": "Początek wydarzenia (Warszawa)",
            "ends_at": "Koniec wydarzenia (Warszawa)",
            "game_starts_at": "Start gry (Warszawa)",
            "game_ends_at": "Koniec gry (Warszawa)",
            "instructions": "Instrukcja gry",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["budget_mib"].initial = self.instance.storage_budget // 1024**2
        for field in self.fields.values():
            if isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(
                    format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
                )

    def clean_budget_mib(self):
        value = self.cleaned_data["budget_mib"]
        if value * 1024**2 < usage(self.instance):
            raise forms.ValidationError(
                "Budżet nie może być mniejszy niż pliki i trwające rezerwacje."
            )
        self.instance.storage_budget = value * 1024**2
        return value


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]
        labels = {"name": "Nazwa grupy"}

    def __init__(self, *args, event, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.event = event

    def clean_name(self):
        name = self.cleaned_data["name"]
        if (
            Group.objects.filter(event=self.instance.event, name=name)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Grupa o tej nazwie już istnieje.")
        return name


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["description"]
        labels = {"description": "Treść zadania"}
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, event, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.event = event
        if self.instance.pk and self.instance.assignment_set.exists():
            self.fields["description"].disabled = True
            self.fields[
                "description"
            ].help_text = "Zadanie już przydzielono. Wycofaj je i utwórz nowe, aby zmienić sens."


class ParticipantForm(forms.Form):
    first_name = forms.CharField(label="Samo imię", max_length=60)
    groups = forms.ModelMultipleChoiceField(
        label="Grupy",
        queryset=Group.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, event, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = Group.objects.filter(event=event)
