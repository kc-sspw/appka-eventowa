import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from events.lifecycle import begin_close, clean_event
from events.models import Event, RateBucket
from media_storage.models import OAuthState, StorageOperation
from media_storage.services import run_operation


def tick():
    for event in Event.objects.filter(state__in=["ACTIVE", "DRAFT"], ends_at__lte=timezone.now()):
        begin_close(event)
    for pk in StorageOperation.objects.filter(
        status__in=["PENDING", "RETRY", "PROCESSING"], next_attempt_at__lte=timezone.now()
    ).values_list("pk", flat=True)[:200]:
        run_operation(pk)
    for pk in Event.objects.filter(state="CLOSING").values_list("pk", flat=True):
        clean_event(pk)
    RateBucket.objects.filter(expires_at__lt=timezone.now()).delete()
    OAuthState.objects.filter(expires_at__lt=timezone.now()).delete()
    for path in Path(settings.FILE_UPLOAD_TEMP_DIR).rglob("*"):
        if path.is_file() and path.stat().st_mtime < time.time() - 3600:
            path.unlink(missing_ok=True)


class Command(BaseCommand):
    help = "Recover storage jobs, close expired events and remove stale private temporary files."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            close_old_connections()
            try:
                tick()
            except Exception:
                # Do not print provider errors, payloads, URLs or credentials. Lease makes restart safe.
                self.stderr.write("Worker cycle failed; pending leases will be retried.")
                if options["once"]:
                    raise
            if options["once"]:
                return
            time.sleep(5)
