from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    *,
    user_id: str,
    organization_id: str,
    role: str,
    session_id: str,
) -> str:
    now = datetime.now(UTC)

    payload = {
        "sub": user_id,
        "organization_id": organization_id,
        "role": role,
        "sid": session_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    *,
    user_id: str,
    session_id: str,
) -> str:
    now = datetime.now(UTC)

    payload = {
        "sub": user_id,
        "sid": session_id,
        "jti": str(uuid4()),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_session_id() -> str:
    return str(uuid4())


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return {}