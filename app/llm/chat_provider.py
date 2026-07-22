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
    ) -> str:

        response = await self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
        )

        return response.choices[0].message.content


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