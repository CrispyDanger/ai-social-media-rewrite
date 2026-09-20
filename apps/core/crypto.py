import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

FERNET_PREFIX = 'gAAAAA'


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    if not token:
        return token
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError('Could not decrypt stored value.') from exc


def is_encrypted(value: str) -> bool:
    return isinstance(value, str) and value.startswith(FERNET_PREFIX)


def _fernet() -> Fernet:
    try:
        return Fernet(_encryption_key())
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(
            'FIELD_ENCRYPTION_KEY must be a url-safe base64-encoded 32-byte key.'
        ) from exc


def _encryption_key() -> bytes:
    configured = getattr(settings, 'FIELD_ENCRYPTION_KEY', '') or ''
    if configured:
        return configured.encode() if isinstance(configured, str) else configured
    return _key_from_secret()


def _key_from_secret() -> bytes:
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(digest)
