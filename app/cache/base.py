from abc import ABC, abstractmethod
from typing import Any


class BaseSessionStore(ABC):

    @abstractmethod
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
        ...

    @abstractmethod
    async def get_session(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def session_exists(
        self,
        session_id: str,
    ) -> bool:
        ...

    @abstractmethod
    async def delete_session(
        self,
        session_id: str,
    ) -> bool:
        ...

    @abstractmethod
    async def delete_user_sessions(
        self,
        user_id: str,
    ) -> None:
        ...