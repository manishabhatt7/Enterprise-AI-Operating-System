from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.session_store import RedisSessionStore
from app.core.jwt import decode_token
from app.db.dependencies import get_db
from app.exceptions.auth import InvalidToken
from app.models.users import User
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=True)

session_store = RedisSessionStore()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme,
    ),
    session: AsyncSession = Depends(
        get_db,
    ),
) -> User:

    token = credentials.credentials

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise InvalidToken("Invalid access token.")

    session_id = payload.get("sid")

    if not session_id:
        raise InvalidToken("Invalid session.")

    if not await session_store.session_exists(
        session_id,
    ):
        raise InvalidToken("Session has expired.")

    user_id = payload.get("sub")

    if not user_id:
        raise InvalidToken("Invalid token payload.")

    repo = UserRepository(session)

    user = await repo.get(
        UUID(user_id),
    )

    if not user:
        raise InvalidToken("User not found.")

    return user