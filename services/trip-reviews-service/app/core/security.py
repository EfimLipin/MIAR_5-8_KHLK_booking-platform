from uuid import UUID
import jwt
from app.core.config import settings


def decode_access_token(token: str) -> str:
    claims = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if claims.get("token_type") != "access" or not claims.get("sub"):
        raise jwt.InvalidTokenError("Invalid token claims")
    return str(UUID(str(claims["sub"])))
