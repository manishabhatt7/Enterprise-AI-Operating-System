from openai import AsyncOpenAI

from app.llm.base import BaseLLMProvider


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