from uuid import UUID

from app.exceptions.agent import NotFoundException
from app.exceptions.conversation import ConversationNotFound
from app.models.conversations import Conversation
from app.enums.conversation import ConversationStatus
from app.models.users import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
)
from app.uow.unit_of_work import UnitOfWork


class ConversationService:
    def __init__(
        self,
        uow: UnitOfWork,
    ):
        self.uow = uow

    async def create(
        self,
        *,
        data: ConversationCreate,
        current_user: User,
    ) -> Conversation:

        agent = await self.uow.agents.get(
            data.agent_id,
        )

        if not agent:
            raise NotFoundException(
                "Agent not found.",
            )

        conversation = Conversation(
            organization_id=current_user.organization_id,
            agent_id=agent.id,
            user_id=current_user.id,
            title=data.title or f"New {agent.name} Chat",
            status=ConversationStatus.ACTIVE,
        )

        await self.uow.conversations.create(
            conversation,
        )

        await self.uow.commit()

        return conversation

    async def get(
        self,
        *,
        conversation_id: UUID,
        current_user: User,
    ) -> Conversation:

        conversation = await self.uow.conversations.get(
            conversation_id,
        )

        if (
            not conversation
            or conversation.organization_id != current_user.organization_id
        ):
            raise ConversationNotFound()

        return conversation

    async def list(
        self,
        *,
        current_user: User,
    ) -> list[Conversation]:

        return await self.uow.conversations.list_by_user(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
        )

    async def update(
        self,
        *,
        conversation_id: UUID,
        data: ConversationUpdate,
        current_user: User,
    ) -> Conversation:

        conversation = await self.get(
            conversation_id=conversation_id,
            current_user=current_user,
        )

        if data.title is not None:
            conversation.title = data.title

        if data.status is not None:
            conversation.status = data.status

        await self.uow.commit()

        await self.uow.refresh(
            conversation,
        )

        return conversation

    async def archive(
        self,
        *,
        conversation_id: UUID,
        current_user: User,
    ) -> None:

        conversation = await self.get(
            conversation_id=conversation_id,
            current_user=current_user,
        )

        conversation.status = ConversationStatus.ARCHIVED

        await self.uow.commit()

    async def delete(
        self,
        *,
        conversation_id: UUID,
        current_user: User,
    ) -> None:

        conversation = await self.get(
            conversation_id=conversation_id,
            current_user=current_user,
        )

        await self.uow.conversations.soft_delete_by_id(
            conversation.id,
        )

        await self.uow.commit()
