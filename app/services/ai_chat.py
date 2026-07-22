from uuid import UUID

from app.exceptions.agent import NotFoundException
from app.exceptions.conversation import ConversationNotFound
from app.llm import PromptBuilder
from app.llm.factory import ProviderFactory
from app.models.messages import Message, MessageRole
from app.models.users import User
from app.uow.unit_of_work import UnitOfWork
from app.services.title_generator import TitleGenerator


class AIChatService:

    def __init__(
        self,
        uow: UnitOfWork,
    ):
        self.uow = uow

    async def chat(
        self,
        *,
        conversation_id: UUID,
        content: str,
        current_user: User,
    ) -> Message:

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

        # Load conversation history
        history = await self.uow.messages.list_by_conversation(
            conversation.id,
        )

        # Build prompt
        prompt = PromptBuilder.build(
            agent=agent,
            messages=history,
        )

        # Get provider
        provider = ProviderFactory.get_provider(
            agent.provider,
        )

        # Generate response
        assistant_text = await provider.chat(
            messages=prompt,
            model=agent.model,
            temperature=agent.temperature,
        )

        # Save assistant message
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