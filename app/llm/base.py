from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


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
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
    ) -> Any:
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
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncGenerator[str, None]:
        ...