import base64
import hashlib
import os
from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    secret = os.environ.get("SECRET_KEY", "super-secret-key-change-in-production")
    key = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def decrypt_token(encrypted: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()
