import json

from cryptography.fernet import Fernet
from django.conf import settings


def encrypt(value):
    return Fernet(settings.TOKEN_KEY.encode()).encrypt(json.dumps(value).encode()).decode()


def decrypt(value):
    return json.loads(Fernet(settings.TOKEN_KEY.encode()).decrypt(value.encode()))
