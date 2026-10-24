"""Create local-only random secrets. Never overwrite an existing environment."""

import base64
import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
path = root / ".env"
values = {
    "DEBUG": "1",
    "SECRET_KEY": secrets.token_urlsafe(48),
    "TOKEN_KEY": base64.urlsafe_b64encode(os.urandom(32)).decode(),
    "PGDATABASE": "event_poc",
    "PGUSER": "event_poc",
    "PGPASSWORD": secrets.token_urlsafe(24),
    "PGHOST": "db",
    "PGPORT": "5432",
    "STORAGE_BACKEND": "fake",
    "EVENT_DOMAIN": "events.localhost",
    "PLATFORM_HOST": "platform.localhost",
    "PUBLIC_SCHEME": "http",
    "PUBLIC_PORT": "8000",
}
with path.open("x") as out:
    os.chmod(path, 0o600)
    for key, value in values.items():
        out.write(f"{key}={value}\n")
print("Created .env with random local secrets. Do not commit it.")
