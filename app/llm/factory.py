from app.llm.base import BaseLLMProvider
from app.llm.client import client
from app.llm.chat_provider import OpenAICompatibleProvider


class ProviderFactory:

    @staticmethod
    def get_provider(
        provider: str,
    ) -> BaseLLMProvider:

        provider = provider.lower()

        if provider == "groq":
            return OpenAICompatibleProvider(
                client,
            )

        raise ValueError(f"Unsupported provider: {provider}")
