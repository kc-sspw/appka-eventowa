"""Operator recovery after independent verification in the owner's Drive account."""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from events.lifecycle import clean_event
from events.models import Event
from media_storage.models import StorageOperation


class Command(BaseCommand):
    help = "Confirm ONE pending deletion only after manually verifying that its file is absent."

    def add_arguments(self, parser):
        parser.add_argument("event_slug")
        parser.add_argument("operation_id")
        parser.add_argument("--file-id", required=True)
        parser.add_argument("--verified-absent", action="store_true")

    def handle(self, *args, **options):
        if not options["verified_absent"]:
            raise CommandError(
                "First verify absence in the owner's account, then use --verified-absent."
            )
        with transaction.atomic():
            event = (
                Event.objects.select_for_update()
                .filter(slug=options["event_slug"], state="CLOSING")
                .first()
            )
            if not event:
                raise CommandError("This command only applies to a closing event.")
            try:
                op = (
                    StorageOperation.objects.select_for_update()
                    .filter(
                        event=event,
                        pk=options["operation_id"],
                        action="DELETE",
                        status__in=["RETRY", "PENDING"],
                    )
                    .first()
                )
            except (ValueError, TypeError, ValidationError):
                op = None
            if not op or not op.external_file_id or op.external_file_id != options["file_id"]:
                raise CommandError("The event, pending deletion and exact file ID must match.")
            if op.lease_until and op.lease_until > timezone.now():
                raise CommandError(
                    "An active operation still holds the lease. Wait for it to settle."
                )
            op.status = "DONE"
            op.reserved_bytes = 0
            op.external_file_id = ""
            op.lease_token = op.lease_until = None
            op.error_code = ""
            op.save()
        clean_event(event.pk)
        self.stdout.write("Verified absence recorded; remaining cleanup was attempted.")
