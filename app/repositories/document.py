from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID
from app.models.documents import Document
from app.models.knowledge_bases import KnowledgeBase
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class DocumentRepository(
    BaseRepository[Document],
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Document)

    async def list_by_knowledge_base(
        self,
        knowledge_base_id: str,
    ) -> list[Document]:

        stmt = (
            select(Document)
            .where(
                Document.knowledge_base_id
                == knowledge_base_id,
            )
            .order_by(
                Document.created_at.desc(),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return list(
            result.scalars().all(),
        )

    async def get_for_organization(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> Document | None:
        """
        Return a document only if it belongs to the given organization.
        """

        stmt = (
            select(Document)
            .join(
                KnowledgeBase,
                Document.knowledge_base_id == KnowledgeBase.id,
            )
            .options(
                joinedload(Document.knowledge_base),
            )
            .where(
                Document.id == document_id,
                KnowledgeBase.organization_id == organization_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()