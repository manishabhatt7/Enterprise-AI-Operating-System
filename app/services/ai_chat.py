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
from app.tools.registry import tool_registry
import json
from app.tools import tool_executor
from app.exceptions.tool import ToolExecutionLimitExceeded
from app.llm.base import BaseLLMProvider


class AIChatService:

    def __init__(
        self,
        uow: UnitOfWork,
    ):
        self.uow = uow

    async def _run_agent_loop(
        self,
        *,
        provider: BaseLLMProvider,
        agent,
        prompt: list[dict],
        max_iterations: int = 5,
    ) -> str:
        """
        Execute the agent until it returns a final response.
        Tool calls are handled in-memory only.
        """

        for _ in range(max_iterations):

            assistant = await provider.chat(
                messages=prompt,
                model=agent.model,
                temperature=agent.temperature,
                tools=tool_registry.schemas(),
            )

            # Final response
            if not assistant.tool_calls:
                return assistant.content or ""

            # Preserve the assistant tool call in memory
            prompt.append(
                assistant.model_dump(
                    exclude_none=True,
                )
            )

            # Execute every requested tool
            for tool_call in assistant.tool_calls:

                arguments = json.loads(
                    tool_call.function.arguments,
                )

                try:

                    result = await tool_executor.execute(
                        tool_name=tool_call.function.name,
                        arguments=arguments,
                    )

                    # Convert ToolResult to dict for JSON serialization
                    if hasattr(result, "model_dump"):
                        result = result.model_dump()

                except Exception as exc:

                    result = {
                        "success": False,
                        "data": None,
                        "error": str(exc),
                    }

                # Feed tool result back to the model
                prompt.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

        raise ToolExecutionLimitExceeded()

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
            or conversation.organization_id != current_user.organization_id
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

        # Validate conversation
        conversation = await self.uow.conversations.get(
            conversation_id,
        )

        if (
            not conversation
            or conversation.organization_id != current_user.organization_id
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

        # Run the complete agent loop
        assistant_text = await self._run_agent_loop(
            provider=provider,
            agent=agent,
            prompt=prompt,
        )

        # Save assistant response
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=assistant_text,
        )

        await self.uow.messages.create(
            assistant_message,
        )

        # Generate conversation title if needed
        if not conversation.title or conversation.title == "New Chat":

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
        if not conversation.title or conversation.title == "New Chat":

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
