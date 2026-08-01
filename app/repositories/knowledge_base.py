from __future__ import annotations

from sqlalchemy import select

from app.models.knowledge_bases import KnowledgeBase
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class KnowledgeBaseRepository(
    BaseRepository[KnowledgeBase],
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, KnowledgeBase)

    async def list_by_organization(
        self,
        organization_id: str,
    ) -> list[KnowledgeBase]:

        stmt = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.organization_id
                == organization_id,
            )
            .order_by(
                KnowledgeBase.created_at.desc(),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return list(
            result.scalars().all(),
        )