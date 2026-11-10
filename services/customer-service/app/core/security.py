from __future__ import annotations
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import jwt
from app.core.config import settings

_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        calculated = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        ).hex()
        return hmac.compare_digest(calculated, digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(customer_id: str) -> tuple[str, int]:
    expires_in = settings.jwt_expire_minutes * 60
    now = datetime.now(timezone.utc)
    claims = {
        "sub": customer_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "token_type": "access",
    }
    token = jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict:
    claims = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if claims.get("token_type") != "access" or not claims.get("sub"):
        raise jwt.InvalidTokenError("Invalid access token claims")
    return claims
