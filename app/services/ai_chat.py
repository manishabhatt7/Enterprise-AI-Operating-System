import json
from collections.abc import AsyncGenerator
from uuid import UUID

import openai

from app.enums.message import MessageRole
from app.exceptions.agent import NotFoundException
from app.exceptions.conversation import ConversationNotFound
from app.exceptions.tool import ToolExecutionLimitExceeded
from app.llm.base import BaseLLMProvider
from app.llm.factory import ProviderFactory
from app.llm.prompt_builder import PromptBuilder
from app.mcp.client import MCPClient
from app.models.messages import Message
from app.models.users import User
from app.uow.unit_of_work import UnitOfWork
from app.utils.title_generator import TitleGenerator

import logging 

logger = logging.getLogger(__name__)

GREETING_PHRASES = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "thanks",
    "thank you",
    "who are you",
    "what can you do",
}


def is_conversational_greeting(text: str | None) -> bool:
    if not text:
        return False
    cleaned = text.strip().lower().rstrip("!.,?")
    return cleaned in GREETING_PHRASES


class AIChatService:

    def __init__(
        self,
        uow: UnitOfWork,
        mcp_client: MCPClient,
    ):
        self.uow = uow
        self.mcp = mcp_client

    async def _agent(
        self,
        provider: BaseLLMProvider,
        agent,
        messages: list[dict],
        current_user: User,
        user_query: str = "",
    ) -> str:
        """
        Run the agent/tool-calling loop.

        The LLM can request MCP tools. Tool results are appended
        to the conversation and sent back to the LLM until the
        LLM produces a final response or the tool-call limit is hit.
        """

        # Fetch available MCP tools once.
        mcp_tools = await self.mcp.list_tools()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
            for tool in mcp_tools
        ]
        tools = []
        for tool in mcp_tools:
            parameters = dict(tool.input_schema) if tool.input_schema else {}
            properties = dict(parameters.get("properties", {}))
            required = list(parameters.get("required", []))

            # Hide organization_id from the LLM schema since it is automatically
            # injected by the backend from current_user.organization_id.
            if "organization_id" in properties:
                del properties["organization_id"]
            if "organization_id" in required:
                required.remove("organization_id")

            parameters["properties"] = properties
            parameters["required"] = required

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": parameters,
                    },
                }
            )

        should_force_tool_first = (
            bool(tools) and not is_conversational_greeting(user_query)
        )

        # Prevent infinite tool-calling loops.
        for step in range(5):
            # On the first step for knowledge queries, enforce tool execution first.
            # On subsequent steps (after tool result is returned), allow auto/answer synthesis.
            if step == 0 and should_force_tool_first:
                tool_choice = "required"
            elif tools:
                tool_choice = "auto"
            else:
                tool_choice = "none"

            try:
                response = await provider.chat(
                    messages=messages,
                    model=agent.model,
                    temperature=agent.temperature,
                    tools=tools,
                    tool_choice=tool_choice,
                )
            except openai.BadRequestError as e:
                # Groq returns 400 with code='tool_use_failed' when tool_choice='required'
                # but the model refuses to call a tool (generates text instead).
                # Gracefully fall back: log and return the model's attempted text.
                error_code = getattr(e, "body", {}) or {}
                if isinstance(error_code, dict) and error_code.get("error", {}).get("code") == "tool_use_failed":
                    failed_text = error_code.get("error", {}).get("failed_generation", "")
                    logger.warning(
                        "Model refused to call tool on step=%d "
                        "(tool_use_failed). Falling back to auto. "
                        "failed_generation=%s",
                        step,
                        repr(failed_text[:200]),
                    )
                    if step == 0:
                        # Retry this step with auto to allow the LLM to answer directly
                        response = await provider.chat(
                            messages=messages,
                            model=agent.model,
                            temperature=agent.temperature,
                            tools=tools,
                            tool_choice="auto",
                        )
                    else:
                        raise
                else:
                    raise

            # No tool call means the agent has produced the final answer.
            if not response.tool_calls:
                return response.content or ""

            # Add the assistant's tool-call message to the conversation.
            messages.append(
                response.model_dump(exclude_none=True)
            )

            for call in response.tool_calls:

                try:
                    arguments = json.loads(
                        call.function.arguments
                    )

                    if call.function.name == "rag_query":
                        arguments["organization_id"] = str(
                            current_user.organization_id
                        )

                    logger.info(
                        "Executing MCP tool: %s arguments=%s",
                        call.function.name,
                        arguments,
                    )

                    result = await self.mcp.call_tool(
                        name=call.function.name,
                        arguments=arguments,
                    )

                    logger.info(
                        "MCP tool returned result preview: %s",
                        repr(result)[:300],
                    )

                    if hasattr(result, "model_dump"):
                        result = result.model_dump()

                except Exception as exc:
                    logger.exception(
                        "MCP tool failed: name=%s arguments=%s",
                        call.function.name,
                        arguments,
                    )

                    result = {
                        "error": str(exc),
                    }

                if isinstance(result, str):
                    tool_content = result
                elif isinstance(result, dict | list):
                    tool_content = json.dumps(result, default=str)
                else:
                    tool_content = str(result)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": tool_content,
                    }
                )

        raise ToolExecutionLimitExceeded()

    async def chat(
        self,
        *,
        conversation_id: UUID,
        content: str,
        current_user: User,
    ) -> Message:

        # Validate conversation.
        conversation = await self.uow.conversations.get(
            conversation_id
        )

        if (
            not conversation
            or conversation.organization_id
            != current_user.organization_id
        ):
            raise ConversationNotFound()

        # Get the agent associated with the conversation.
        agent = await self.uow.agents.get(
            conversation.agent_id
        )

        if not agent:
            raise NotFoundException()

        # Store user message.
        await self.uow.messages.create(
            Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=content,
            )
        )

        # Load conversation history.
        history = await self.uow.messages.list_by_conversation(
            conversation.id
        )

        # Build system prompt + conversation messages.
        messages = PromptBuilder.build(
            agent=agent,
            messages=history,
        )

        # Get configured LLM provider.
        provider = ProviderFactory.get_provider(
            agent.provider
        )

        # Run agentic MCP/tool-calling loop.
        answer = await self._agent(
            provider=provider,
            agent=agent,
            messages=messages,
            current_user=current_user,
            user_query=content,
        )

        # Store assistant response.
        response = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=answer,
        )

        await self.uow.messages.create(response)

        # Generate conversation title for new conversations.
        if (
            not conversation.title
            or conversation.title == "New Chat"
        ):
            history = await self.uow.messages.list_by_conversation(
                conversation.id
            )

            conversation.title = await TitleGenerator.generate(
                agent=agent,
                messages=history,
            )

        await self.uow.commit()

        return response

    async def stream_chat(
        self,
        *,
        conversation_id: UUID,
        content: str,
        current_user: User,
    ) -> AsyncGenerator[str, None]:
        """
        Temporary streaming implementation.

        Currently executes the normal non-streaming agent flow
        and yields the final response as a single chunk.

        Real token/tool-event streaming can be implemented later.
        """

        response = await self.chat(
            conversation_id=conversation_id,
            content=content,
            current_user=current_user,
        )

        yield response.content

