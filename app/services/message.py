from uuid import UUID

from app.exceptions.conversation import ConversationNotFound
from app.models.messages import Message, MessageRole
from app.models.users import User
from app.schemas.message import MessageCreate
from app.uow.unit_of_work import UnitOfWork


class MessageService:

    def __init__(
        self,
        uow: UnitOfWork,
    ):
        self.uow = uow

    async def create(
        self,
        *,
        conversation_id: UUID,
        data: MessageCreate,
        current_user: User,
    ) -> Message:

        conversation = await self.uow.conversations.get(
            conversation_id,
        )

        if (
            not conversation
            or conversation.organization_id
            != current_user.organization_id
        ):
            raise ConversationNotFound()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=data.content,
        )

        await self.uow.messages.create(
            message,
        )

        await self.uow.commit()

        return message

    async def list(
        self,
        *,
        conversation_id: UUID,
        current_user: User,
    ) -> list[Message]:

        conversation = await self.uow.conversations.get(
            conversation_id,
        )

        if (
            not conversation
            or conversation.organization_id
            != current_user.organization_id
        ):
            raise ConversationNotFound()

        return await self.uow.messages.list_by_conversation(
            conversation_id,
        )