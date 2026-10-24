import tempfile

from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile, UploadedFile
from django.core.files.uploadhandler import (
    FileUploadHandler,
    StopUpload,
    TemporaryFileUploadHandler,
)


class EventTemporaryUploadedFile(TemporaryUploadedFile):
    def __init__(self, name, content_type, charset, content_type_extra, directory):
        handle = tempfile.NamedTemporaryFile(suffix=".upload", dir=directory)
        UploadedFile.__init__(self, handle, name, content_type, 0, charset, content_type_extra)


class PrivateTemporaryUploadHandler(TemporaryFileUploadHandler):
    def new_file(self, *args, **kwargs):
        FileUploadHandler.new_file(self, *args, **kwargs)
        event = getattr(self.request, "event", None)
        directory = settings.PRIVATE_ROOT / "incoming" / (str(event.pk) if event else "platform")
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.file = EventTemporaryUploadedFile(
            self.file_name, self.content_type, self.charset, self.content_type_extra, directory
        )


class BoundedUploadHandler(FileUploadHandler):
    def __init__(self, request=None):
        super().__init__(request)
        self.total = 0

    def receive_data_chunk(self, raw_data, start):
        self.total += len(raw_data)
        if self.total > settings.UPLOAD_MAX_BYTES:
            self.request.upload_too_large = True
            raise StopUpload(connection_reset=False)
        return raw_data

    def file_complete(self, file_size):
        return None
