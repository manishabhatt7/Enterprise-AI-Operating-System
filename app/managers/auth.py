from app.cache import session_store
from app.core.config import settings
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    create_session_id,
    decode_token,
)
from app.core.security import (
    hash_password,
    verify_password,
)
from app.exceptions.auth import InvalidToken
from app.schemas.auth import TokenPair


class AuthManager:
    async def hash_password(
        self,
        password: str,
    ) -> str:
        return hash_password(password)

    async def verify_password(
        self,
        password: str,
        hashed_password: str,
    ) -> bool:
        return verify_password(
            password,
            hashed_password,
        )

    async def create_token_pair(
        self,
        *,
        user_id: str,
        organization_id: str,
        role: str,
    ) -> TokenPair:

        session_id = create_session_id()

        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        await session_store.create_session(
            session_id=session_id,
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            ttl=ttl,
        )

        access_token = create_access_token(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            session_id=session_id,
        )

        refresh_token = create_refresh_token(
            user_id=user_id,
            session_id=session_id,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> TokenPair:

        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidToken()

        session_id = payload.get("sid")

        if not session_id:
            raise InvalidToken()

        session = await session_store.get_session(
            session_id,
        )

        if not session:
            raise InvalidToken()

        access_token = create_access_token(
            user_id=session["user_id"],
            organization_id=session["organization_id"],
            role=session["role"],
            session_id=session_id,
        )

        refresh_token = create_refresh_token(
            user_id=session["user_id"],
            session_id=session_id,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(
        self,
        refresh_token: str,
    ) -> None:

        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidToken()

        session_id = payload.get("sid")

        if not session_id:
            raise InvalidToken()

        deleted = await session_store.delete_session(
            session_id,
        )

        if not deleted:
            raise InvalidToken("Session already logged out.")


auth_manager = AuthManager()