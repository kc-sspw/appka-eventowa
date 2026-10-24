import json
import os
import re
import time
import uuid

import httpx
from django.conf import settings

from .crypto import decrypt, encrypt
from .models import StorageConnection


class StorageError(Exception):
    def __init__(self, code="provider_unavailable"):
        self.code = code
        super().__init__(code)


class FakeStorage:
    """Private local adapter. Faults are injected by tests, never by HTTP payloads."""

    fault = None

    def __init__(self, event_id, folder_id="", **kwargs):
        if not settings.DEBUG:
            raise StorageError("fake_disabled")
        self.event_id = str(uuid.UUID(str(event_id)))
        self.folder_id = folder_id or self.event_id
        if self.folder_id != self.event_id:
            raise StorageError("scope_mismatch")
        self.root = settings.PRIVATE_ROOT / "fake" / self.event_id

    def create_event_folder(self):
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        return self.folder_id

    def allocate_id(self):
        return str(uuid.uuid4())

    def _path(self, file_id):
        return self.root / (str(uuid.UUID(file_id)) + ".jpg")

    def check_access(self):
        if self.fault == "denied":
            raise StorageError("access_denied")
        if not self.root.is_dir():
            raise StorageError("folder_missing")
        return {"owner_id": "local", "remaining_bytes": None}

    def find_by_operation(self, operation_id, file_id=""):
        self.check_access()
        meta = self.root / (str(uuid.UUID(str(operation_id))) + ".json")
        if meta.exists():
            data = json.loads(meta.read_text())
            if self._path(data["id"]).exists():
                return data
        # Stable file id lets us recover a crash after binary write, before metadata write.
        if file_id and self._path(file_id).exists():
            return {"id": file_id, "size": self._path(file_id).stat().st_size}
        return None

    def upload(self, operation_id, file_id, content):
        existing = self.find_by_operation(operation_id, file_id)
        if existing:
            return existing
        if self.fault in {"full", "before"}:
            raise StorageError("quota_exceeded" if self.fault == "full" else "provider_timeout")
        path = self._path(file_id)
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(content)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        result = {"id": file_id, "size": len(content)}
        (self.root / (str(operation_id) + ".json")).write_text(json.dumps(result))
        if self.fault == "after":
            raise StorageError("provider_timeout")
        return result

    def read(self, file_id):
        self.check_access()
        try:
            with self._path(file_id).open("rb") as source:
                while chunk := source.read(64 * 1024):
                    yield chunk
        except FileNotFoundError:
            raise StorageError("file_missing")

    def delete(self, file_id):
        self.check_access()
        if self.fault == "delete":
            raise StorageError("provider_unavailable")
        self._path(file_id).unlink(missing_ok=True)
        for meta in self.root.glob("*.json"):
            if json.loads(meta.read_text())["id"] == file_id:
                meta.unlink()


class DriveStorage:
    API = "https://www.googleapis.com/drive/v3"

    def __init__(self, event_id, folder_id, credentials=None, client=None):
        self.event_id = str(uuid.UUID(str(event_id)))
        self.folder_id = folder_id
        self.credentials = credentials
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(30, connect=10), follow_redirects=False
        )

    def _token(self):
        credentials = self.credentials
        if credentials is None:
            connection = StorageConnection.objects.get(event_id=self.event_id)
            credentials = decrypt(connection.encrypted_credentials)
        if credentials.get("expires_at", 0) < time.time() + 60:
            try:
                response = self.client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "refresh_token": credentials["refresh_token"],
                        "grant_type": "refresh_token",
                    },
                )
                if response.status_code != 200:
                    raise StorageError("access_denied")
                result = response.json()
                credentials.update(
                    access_token=result["access_token"],
                    expires_at=time.time() + result["expires_in"],
                )
                if self.credentials is None:
                    StorageConnection.objects.filter(event_id=self.event_id).update(
                        encrypted_credentials=encrypt(credentials)
                    )
            except (httpx.HTTPError, KeyError, ValueError):
                raise StorageError("access_denied") from None
        return credentials["access_token"]

    def _request(self, method, path, **kwargs):
        headers = {"Authorization": "Bearer " + self._token(), **kwargs.pop("headers", {})}
        url = path if path.startswith("https://www.googleapis.com/") else self.API + path
        try:
            response = self.client.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError:
            raise StorageError("provider_timeout") from None
        if response.status_code == 404:
            return None
        if response.status_code == 409:
            raise StorageError("already_exists")
        if response.status_code in (401, 403):
            reason = "access_denied"
            try:
                if any(
                    x.get("reason") == "storageQuotaExceeded"
                    for x in response.json().get("error", {}).get("errors", [])
                ):
                    reason = "quota_exceeded"
            except ValueError:
                pass
            raise StorageError(reason)
        if response.status_code >= 400:
            raise StorageError("provider_unavailable")
        return response

    @staticmethod
    def _safe_id(file_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", file_id):
            raise StorageError("scope_mismatch")
        return file_id

    def allocate_id(self):
        response = self._request(
            "GET", "/files/generateIds", params={"count": 1, "space": "drive", "type": "files"}
        )
        if response is None:
            raise StorageError()
        return response.json()["ids"][0]

    def _metadata(self, file_id):
        response = self._request(
            "GET",
            "/files/" + self._safe_id(file_id),
            params={"fields": "id,size,parents,appProperties,mimeType,trashed,ownedByMe"},
        )
        return response.json() if response is not None else None

    def _validate_file(self, data, operation_id=None):
        if (
            not data
            or data.get("trashed")
            or data.get("appProperties", {}).get("event") != self.event_id
            or self.folder_id not in data.get("parents", [])
        ):
            raise StorageError("scope_mismatch")
        if operation_id and data.get("appProperties", {}).get("operation") != str(operation_id):
            raise StorageError("scope_mismatch")
        return {"id": data["id"], "size": int(data["size"])}

    def create_event_folder(self):
        if self._metadata(self.folder_id) is None:
            try:
                self._request(
                    "POST",
                    "/files",
                    json={
                        "id": self.folder_id,
                        "name": "Wydarzenie " + self.event_id,
                        "mimeType": "application/vnd.google-apps.folder",
                        "appProperties": {"event": self.event_id},
                    },
                    params={"fields": "id"},
                )
            except StorageError as exc:
                if exc.code != "already_exists":
                    raise
        self.check_access()
        return self.folder_id

    def check_access(self):
        folder = self._metadata(self.folder_id)
        if (
            not folder
            or folder.get("trashed")
            or not folder.get("ownedByMe")
            or folder.get("mimeType") != "application/vnd.google-apps.folder"
            or folder.get("appProperties", {}).get("event") != self.event_id
        ):
            raise StorageError("folder_missing")
        response = self._request(
            "GET", "/about", params={"fields": "user(permissionId),storageQuota"}
        )
        data = response.json()
        quota = data.get("storageQuota", {})
        remaining = int(quota["limit"]) - int(quota.get("usage", 0)) if "limit" in quota else None
        return {"owner_id": data["user"]["permissionId"], "remaining_bytes": remaining}

    def find_by_operation(self, operation_id, file_id=""):
        # Read by preallocated id first: avoids eventually-consistent search duplicates.
        if file_id:
            data = self._metadata(file_id)
            if data:
                return self._validate_file(data, operation_id)
        operation_id = str(uuid.UUID(str(operation_id)))
        folder = self._safe_id(self.folder_id)
        response = self._request(
            "GET",
            "/files",
            params={
                "q": f"'{folder}' in parents and trashed = false and appProperties has {{ key='operation' and value='{operation_id}' }} and appProperties has {{ key='event' and value='{self.event_id}' }}",
                "spaces": "drive",
                "fields": "files(id,size,parents,appProperties,trashed)",
                "pageSize": 10,
            },
        )
        files = response.json().get("files", [])
        if len(files) > 1:
            raise StorageError("duplicate_operation")
        return self._validate_file(files[0], operation_id) if files else None

    def upload(self, operation_id, file_id, content):
        existing = self.find_by_operation(operation_id, file_id)
        if existing:
            return existing
        metadata = {
            "id": file_id,
            "name": str(uuid.uuid4()) + ".jpg",
            "parents": [self.folder_id],
            "appProperties": {"event": self.event_id, "operation": str(operation_id)},
        }
        boundary = uuid.uuid4().hex
        body = (
            (
                f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
                + json.dumps(metadata)
                + f"\r\n--{boundary}\r\nContent-Type: image/jpeg\r\n\r\n"
            ).encode()
            + content
            + f"\r\n--{boundary}--\r\n".encode()
        )
        try:
            self._request(
                "POST",
                "https://www.googleapis.com/upload/drive/v3/files",
                params={"uploadType": "multipart", "fields": "id,size"},
                headers={"Content-Type": "multipart/related; boundary=" + boundary},
                content=body,
            )
        except StorageError as exc:
            if exc.code != "already_exists":
                raise
        data = self.find_by_operation(operation_id, file_id)
        if not data:
            raise StorageError("provider_timeout")
        return data

    def read(self, file_id):
        self._validate_file(self._metadata(file_id))
        try:
            with self.client.stream(
                "GET",
                self.API + "/files/" + self._safe_id(file_id),
                params={"alt": "media"},
                headers={"Authorization": "Bearer " + self._token()},
            ) as response:
                if response.status_code != 200:
                    raise StorageError("file_unavailable")
                yield from response.iter_bytes(64 * 1024)
        except httpx.HTTPError:
            raise StorageError("provider_timeout") from None

    def delete(self, file_id):
        data = self._metadata(file_id)
        if data is None:
            return
        self._validate_file(data)
        self._request("DELETE", "/files/" + self._safe_id(file_id))


def storage_for(event):
    connection = StorageConnection.objects.filter(event=event).first()
    if not connection:
        raise StorageError("not_connected")
    adapter = FakeStorage if settings.STORAGE_BACKEND == "fake" else DriveStorage
    return adapter(event.pk, connection.folder_id)
