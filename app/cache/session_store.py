from __future__ import annotations

import json
from typing import Any

from app.cache.base import BaseSessionStore
from app.cache.redis import redis_client


class RedisSessionStore(BaseSessionStore):
    SESSION_PREFIX = "session:"
    USER_PREFIX = "user_sessions:"

    async def create_session(
        self,
        *,
        session_id: str,
        user_id: str,
        organization_id: str,
        role: str,
        ttl: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:

        payload = {
            "user_id": user_id,
            "organization_id": organization_id,
            "role": role,
            "metadata": metadata or {},
        }

        await redis_client.set(
            f"{self.SESSION_PREFIX}{session_id}",
            json.dumps(payload),
            ex=ttl,
        )

        await redis_client.sadd(
            f"{self.USER_PREFIX}{user_id}",
            session_id,
        )

        await redis_client.expire(
            f"{self.USER_PREFIX}{user_id}",
            ttl,
        )

    async def get_session(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:

        data = await redis_client.get(
            f"{self.SESSION_PREFIX}{session_id}"
        )

        if not data:
            return None

        return json.loads(data)

    async def session_exists(
        self,
        session_id: str,
    ) -> bool:

        return bool(
            await redis_client.exists(
                f"{self.SESSION_PREFIX}{session_id}"
            )
        )

    async def delete_session(
        self,
        session_id: str,
    ) -> bool:

        session = await self.get_session(session_id)

        if session:
            await redis_client.srem(
                f"{self.USER_PREFIX}{session['user_id']}",
                session_id,
            )

        deleted = await redis_client.delete(
            f"{self.SESSION_PREFIX}{session_id}"
        )

        return bool(deleted)

    async def delete_user_sessions(
        self,
        user_id: str,
    ) -> None:

        key = f"{self.USER_PREFIX}{user_id}"

        sessions = await redis_client.smembers(key)

        for session_id in sessions:
            await redis_client.delete(
                f"{self.SESSION_PREFIX}{session_id}"
            )

        await redis_client.delete(key)