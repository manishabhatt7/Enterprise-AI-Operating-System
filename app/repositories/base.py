from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing common CRUD operations.
    """

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ):
        self.session = session
        self.model = model

    def _supports_soft_delete(self) -> bool:
        """
        Returns True if the model has a deleted_at column.
        """
        return hasattr(self.model, "deleted_at")

    async def get(
        self,
        id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ModelType | None:

        stmt = select(self.model).where(
            self.model.id == id,
        )

        if self._supports_soft_delete():
            if not include_deleted:
                stmt = stmt.where(
                    self.model.deleted_at.is_(None),
                )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[ModelType]:

        stmt = select(self.model)

        if self._supports_soft_delete():
            if not include_deleted:
                stmt = stmt.where(
                    self.model.deleted_at.is_(None),
                )

        stmt = (
            stmt.offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def count(
        self,
    ) -> int:

        stmt = select(func.count()).select_from(
            self.model,
        )

        if self._supports_soft_delete():
            stmt = stmt.where(
                self.model.deleted_at.is_(None),
            )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def exists(
        self,
        id: UUID,
    ) -> bool:

        return await self.get(id) is not None

    async def create(
        self,
        obj: ModelType,
    ) -> ModelType:

        self.session.add(obj)

        await self.session.flush()

        await self.session.refresh(obj)

        return obj

    async def update(
        self,
        obj: ModelType,
        **kwargs: Any,
    ) -> ModelType:

        for key, value in kwargs.items():
            setattr(obj, key, value)

        await self.session.flush()

        await self.session.refresh(obj)

        return obj

    async def soft_delete(
        self,
        obj: ModelType,
    ) -> None:

        if not self._supports_soft_delete():
            raise NotImplementedError(
                f"{self.model.__name__} does not support soft delete."
            )

        obj.deleted_at = datetime.now(UTC)

        await self.session.flush()

    async def soft_delete_by_id(
        self,
        id: UUID,
    ) -> None:

        obj = await self.get(id)

        if obj is None:
            return

        await self.soft_delete(obj)

    async def delete(
        self,
        obj: ModelType,
    ) -> None:
        """
        Permanently delete an object.
        Use only for admin cleanup, tests, or GDPR requests.
        """

        await self.session.delete(obj)

    async def delete_by_id(
        self,
        id: UUID,
    ) -> None:
        """
        Permanently delete by id.
        """

        stmt = delete(self.model).where(
            self.model.id == id,
        )

        await self.session.execute(stmt)