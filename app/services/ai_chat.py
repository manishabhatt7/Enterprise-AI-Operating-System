from uuid import UUID

from app.exceptions.agent import NotFoundException
from app.exceptions.conversation import ConversationNotFound
from app.llm import PromptBuilder
from app.llm.factory import ProviderFactory
from app.models.agents import Agent
from app.models.conversations import Conversation
from app.models.messages import Message, MessageRole
from app.models.users import User
from app.services.title_generator import TitleGenerator
from app.uow.unit_of_work import UnitOfWork
from collections.abc import AsyncGenerator


class AIChatService:

    def __init__(
        self,
        uow: UnitOfWork,
    ):
        self.uow = uow

    async def _prepare_chat_context(
        self,
        *,
        conversation_id: UUID,
        current_user: User,
        content: str,
    ) -> tuple[
        Conversation,
        Agent,
        list[dict],
    ]:

        # Validate conversation
        conversation = await self.uow.conversations.get(
            conversation_id,
        )

        if (
            not conversation
            or conversation.organization_id
            != current_user.organization_id
        ):
            raise ConversationNotFound()

        # Load agent
        agent = await self.uow.agents.get(
            conversation.agent_id,
        )

        if not agent:
            raise NotFoundException()

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=content,
        )

        await self.uow.messages.create(
            user_message,
        )

        # Reload history
        history = await self.uow.messages.list_by_conversation(
            conversation.id,
        )

        # Build prompt
        prompt = PromptBuilder.build(
            agent=agent,
            messages=history,
        )

        return (
            conversation,
            agent,
            prompt,
        )

    async def chat(
        self,
        *,
        conversation_id: UUID,
        content: str,
        current_user: User,
    ) -> Message:

        (
            conversation,
            agent,
            prompt,
        ) = await self._prepare_chat_context(
            conversation_id=conversation_id,
            current_user=current_user,
            content=content,
        )

        provider = ProviderFactory.get_provider(
            agent.provider,
        )

        assistant_text = await provider.chat(
            messages=prompt,
            model=agent.model,
            temperature=agent.temperature,
        )

        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=assistant_text,
        )

        await self.uow.messages.create(
            assistant_message,
        )

        # Generate conversation title if needed
        if (
            not conversation.title
            or conversation.title == "New Chat"
        ):

            history = await self.uow.messages.list_by_conversation(
                conversation.id,
            )

            title = await TitleGenerator.generate(
                agent=agent,
                messages=history,
            )

            await self.uow.conversations.update(
                conversation,
                title=title,
            )

        await self.uow.commit()

        return assistant_message

    async def stream_chat(
        self,
        *,
        conversation_id: UUID,
        content: str,
        current_user: User,
    ) -> AsyncGenerator[str, None]:

        (
            conversation,
            agent,
            prompt,
        ) = await self._prepare_chat_context(
            conversation_id=conversation_id,
            current_user=current_user,
            content=content,
        )

        provider = ProviderFactory.get_provider(
            agent.provider,
        )

        assistant_text = ""

        async for token in provider.stream_chat(
            messages=prompt,
            model=agent.model,
            temperature=agent.temperature,
        ):

            assistant_text += token

            yield token

        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=assistant_text,
        )

        await self.uow.messages.create(
            assistant_message,
        )

        # Generate conversation title if needed
        if (
            not conversation.title
            or conversation.title == "New Chat"
        ):

            history = await self.uow.messages.list_by_conversation(
                conversation.id,
            )

            title = await TitleGenerator.generate(
                agent=agent,
                messages=history,
            )

            await self.uow.conversations.update(
                conversation,
                title=title,
            )
           
        await self.uow.commit()