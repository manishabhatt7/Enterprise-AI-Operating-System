from __future__ import annotations

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

    async def get(
        self,
        id: UUID,
    ) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:

        stmt = (
            select(self.model)
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)

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

    async def delete(
        self,
        obj: ModelType,
    ) -> None:

        await self.session.delete(obj)

    async def delete_by_id(
        self,
        id: UUID,
    ) -> None:

        stmt = delete(self.model).where(
            self.model.id == id
        )

        await self.session.execute(stmt)

