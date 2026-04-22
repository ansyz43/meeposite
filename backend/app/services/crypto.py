import base64
import hashlib
import logging
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

logger = logging.getLogger(__name__)


def _derive_key(material: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(material.encode()).digest())


def _primary_fernet() -> Fernet:
    material = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    return Fernet(_derive_key(material))


def _legacy_fernet() -> Fernet | None:
    # Only meaningful when a dedicated ENCRYPTION_KEY is set — older tokens were
    # encrypted using SECRET_KEY, keep them decryptable.
    if settings.ENCRYPTION_KEY and settings.ENCRYPTION_KEY != settings.SECRET_KEY:
        return Fernet(_derive_key(settings.SECRET_KEY))
    return None


def _get_fernet() -> Fernet:
    return _primary_fernet()


def encrypt_token(token: str) -> str:
    """Encrypt bot token with Fernet (AES-128-CBC)."""
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Decrypt bot token. Tries the legacy SECRET_KEY-derived key as a fallback."""
    data = encrypted.encode()
    try:
        return _primary_fernet().decrypt(data).decode()
    except InvalidToken:
        legacy = _legacy_fernet()
        if legacy is None:
            raise
        logger.warning("decrypt_token: falling back to legacy SECRET_KEY-derived Fernet")
        return legacy.decrypt(data).decode()
