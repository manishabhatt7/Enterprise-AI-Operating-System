from typing import Any
from openai import AsyncOpenAI

from app.llm.base import BaseLLMProvider
from collections.abc import AsyncGenerator


class OpenAICompatibleProvider(BaseLLMProvider):

    def __init__(
        self,
        client: AsyncOpenAI,
    ):
        self.client = client

    async def chat(
        self,
        *,
        messages: list[dict],
        model: str,
        temperature: float,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
    ) -> Any:

        response = await self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
            tools=tools or None,
            tool_choice= tool_choice if tools else "none",

        )

        return response.choices[0].message


    async def stream_chat(
        self,
        *,
        messages: list[dict],
        model: str,
        temperature: float,
    ) -> AsyncGenerator[str, None]:

        stream = await self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
            stream=True,
        )

        async for chunk in stream:

            delta = chunk.choices[0].delta.content

            if delta:
                yield delta