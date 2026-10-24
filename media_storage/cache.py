import fcntl
import io
import os
import shutil
import time
import uuid
from contextlib import contextmanager

from django.conf import settings
from django.db import transaction
from PIL import Image

from events.models import Event
from events.security import assert_open
from game.services import current_photo

from .adapters import storage_for


@contextmanager
def cache_lock():
    root = settings.PRIVATE_ROOT / "thumbnails"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (root / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield root


def purge_event(event_id):
    with cache_lock() as root:
        shutil.rmtree(root / str(event_id), ignore_errors=True)


def purge_photo(photo):
    with cache_lock() as root:
        for path in (root / str(photo.event_id)).glob(f"{photo.id}-*.jpg"):
            path.unlink(missing_ok=True)


def thumbnail(event, photo):
    name = f"{photo.id}-{photo.version}.jpg"
    with cache_lock() as root:
        path = root / str(event.id) / name
        if path.exists() and path.stat().st_mtime > time.time() - settings.THUMBNAIL_TTL:
            return path.read_bytes()
    data = b"".join(storage_for(event).read(photo.operation.external_file_id))
    output = io.BytesIO()
    with Image.open(io.BytesIO(data)) as source:
        source.thumbnail((600, 600))
        source.convert("RGB").save(output, "JPEG", quality=78)
    result = output.getvalue()
    # Close/moderation/replacement cannot repopulate an invalid cache key after purge.
    with transaction.atomic():
        locked = Event.objects.select_for_update().get(pk=event.pk)
        assert_open(locked)
        current_photo(locked, photo.pk)
        with cache_lock() as root:
            files = sorted(root.glob("*/*.jpg"), key=lambda p: p.stat().st_mtime)
            size = sum(p.stat().st_size for p in files)
            for old in files:
                if (
                    old.stat().st_mtime < time.time() - settings.THUMBNAIL_TTL
                    or size + len(result) > settings.THUMBNAIL_CACHE_BYTES
                ):
                    size -= old.stat().st_size
                    old.unlink(missing_ok=True)
            path.parent.mkdir(mode=0o700, exist_ok=True)
            temporary = path.with_suffix("." + uuid.uuid4().hex)
            temporary.write_bytes(result)
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
    return result
