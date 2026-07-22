from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversations import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(
    BaseRepository[Conversation],
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)

    async def list_by_user(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> list[Conversation]:

        result = await self.session.execute(
            select(Conversation)
            .where(
                Conversation.organization_id == organization_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .order_by(
                Conversation.created_at.desc(),
            )
        )

        return list(
            result.scalars().all()
        )

    async def list_by_agent(
        self,
        organization_id: UUID,
        agent_id: UUID,
    ) -> list[Conversation]:

        result = await self.session.execute(
            select(Conversation)
            .where(
                Conversation.organization_id == organization_id,
                Conversation.agent_id == agent_id,
                Conversation.deleted_at.is_(None),
            )
        )

        return list(
            result.scalars().all()
        )