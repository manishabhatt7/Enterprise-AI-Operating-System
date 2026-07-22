from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BaseLLMProvider(ABC):
    """
    Base interface for all LLM providers.
    """

    @abstractmethod
    async def chat(
        self,
        *,
        messages: list[dict],
        model: str,
        temperature: float,
    ) -> str:
        """
        Generate an assistant response.

        Returns:
            Assistant message content.
        """
        raise NotImplementedError


    @abstractmethod
    async def stream_chat(
        self,
        *,
        messages: list[dict],
        model: str,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        ...