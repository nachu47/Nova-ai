import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet

from app.core.config import settings

_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
_fernet = Fernet(settings.encryption_key.encode())


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return _hasher.verify(encoded, password)
    except VerifyMismatchError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_random_token(size: int = 32) -> str:
    return secrets.token_urlsafe(size)


def create_jwt(subject: str, token_type: str, expires_delta: timedelta, **claims: Any) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": secrets.token_hex(16),
        **claims,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_jwt(token: str, expected_type: str | None = None) -> dict[str, Any]:
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def encrypt_secret(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()


def sign_payload(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify_signature(secret: str, payload: bytes, signature: str) -> bool:
    return hmac.compare_digest(sign_payload(secret, payload), signature)


def basic_api_key() -> tuple[str, str]:
    prefix = f"nova_{secrets.token_hex(4)}"
    secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    return prefix, f"{prefix}.{secret}"
