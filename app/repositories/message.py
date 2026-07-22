from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messages import Message
from app.repositories.base import BaseRepository


class MessageRepository(
    BaseRepository[Message],
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)

    async def list_by_conversation(
        self,
        conversation_id: UUID,
    ) -> list[Message]:

        result = await self.session.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
            )
            .order_by(
                Message.created_at.asc(),
            )
        )

        return list(
            result.scalars().all()
        )