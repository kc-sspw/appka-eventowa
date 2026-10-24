import csv
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Account, Group, Membership
from accounts.services import credentials
from events.models import Event
from game.models import Task
from information.models import Entry, ScheduleItem
from media_storage.adapters import FakeStorage
from media_storage.models import StorageConnection


class Command(BaseCommand):
    help = (
        "Seed two isolated synthetic events. Random credentials go to a private CSV, never stdout."
    )

    def add_arguments(self, parser):
        parser.add_argument("--participants", type=int, default=12)

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG or settings.STORAGE_BACKEND != "fake":
            raise CommandError("Synthetic seed requires DEBUG=1 and FakeStorage.")
        if Event.objects.filter(slug__in=["event-a", "event-b"]).exists():
            raise CommandError("Demo events already exist; seed never overwrites accounts.")
        if not 2 <= options["participants"] <= 500:
            raise CommandError("Choose 2–500 participants.")
        now = timezone.now()
        rows = []
        for slug, count in [("event-a", options["participants"]), ("event-b", 3)]:
            event = Event.objects.create(
                slug=slug,
                name="Wyjazd KC · " + slug[-1].upper(),
                state="ACTIVE",
                starts_at=now - timedelta(hours=1),
                ends_at=now + timedelta(days=4),
                game_starts_at=now - timedelta(minutes=30),
                game_ends_at=now + timedelta(days=3),
                instructions="Wylosuj zadanie, znajdź swój kadr i podziel się zdjęciem. Możesz mieć pięć zadań do wykonania jednocześnie. Fotografuj z szacunkiem i pytaj inne osoby o zgodę.",
            )
            folder = FakeStorage(event.pk).create_event_folder()
            StorageConnection.objects.create(event=event, folder_id=folder, owner_id="local")
            groups = [
                Group.objects.create(event=event, name=name)
                for name in ["Szlak zielony", "Szlak niebieski"]
            ]
            for n in range(count + 1):
                username, password = credentials()
                role = "ORGANIZER" if n == 0 else "PARTICIPANT"
                first_name = (
                    "Organizator" if n == 0 else ["Ala", "Bartek", "Celina", "Darek"][n % 4]
                )
                account = Account.objects.create_user(
                    username,
                    password,
                    event=event,
                    role=role,
                    first_name=first_name,
                    public_number=n + 1,
                )
                if n:
                    Membership.objects.create(account=account, group=groups[n % 2])
                rows.append([slug, role, first_name, username, password])
            prompts = [
                "Znajdź coś w kolorze zielonym",
                "Uchwyć ciekawy cień",
                "Pokaż drogę z innej perspektywy",
                "Sfotografuj detal, który łatwo przeoczyć",
                "Złap kadr z odbiciem",
            ]
            Task.objects.bulk_create(
                [
                    Task(event=event, description=f"{prompts[i % len(prompts)]} · wariant {i + 1}")
                    for i in range(50)
                ]
            )
            Entry.objects.create(
                event=event,
                kind="NEWS",
                title="Zaczynamy wspólną przygodę!",
                body="Witaj na naszym wydarzeniu. Sprawdź plan, poznaj swoją grupę i wylosuj pierwsze zadanie fotograficzne.",
                pinned=True,
            )
            Entry.objects.create(
                event=event,
                kind="STATIC",
                title="Wszystko, co warto wiedzieć",
                body="Punkt organizatora znajdziesz przy recepcji. W razie pytań podejdź do nas podczas przerw.",
            )
            private = Entry.objects.create(
                event=event,
                kind="NEWS",
                title="Informacja dla szlaku zielonego",
                body="Wasza zbiórka przy wejściu głównym.",
                audience="GROUPS",
            )
            private.groups.add(groups[0])
            for i, (title, location) in enumerate(
                [
                    ("Poznajmy się", "Sala wspólna"),
                    ("Czas na spacer", "Przed wejściem"),
                    ("Wieczór razem", "Świetlica"),
                ]
            ):
                ScheduleItem.objects.create(
                    event=event,
                    title=title,
                    location=location,
                    starts_at=now + timedelta(hours=i + 1),
                )
        path = settings.PRIVATE_ROOT / "demo-credentials.csv"
        with path.open("x", newline="") as out:
            import os

            os.chmod(path, 0o600)
            writer = csv.writer(out)
            writer.writerow(["event", "role", "first_name", "login", "password"])
            writer.writerows(rows)
        self.stdout.write(
            f"Created two synthetic events. Credentials saved privately to {path.name}."
        )
