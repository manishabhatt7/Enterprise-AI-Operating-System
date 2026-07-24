from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from app.core.config import settings
from app.schemas.tool import ToolResult


class BaseTool(ABC):
    """
    Base interface for all AI tools.
    """

    # Retry configuration
    retryable: bool = False
    max_retries: int = settings.MAX_RETRIES
    initial_backoff: float = settings.INITIAL_BACKOFF

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique tool name exposed to the LLM.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Description used by the LLM.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def input_model(self) -> type[BaseModel]:
        """
        Pydantic model describing tool inputs.
        """
        raise NotImplementedError

    @property
    def parameters(self) -> dict[str, Any]:
        """
        OpenAI-compatible JSON schema.
        """
        return self.input_model.model_json_schema()

    @abstractmethod
    async def execute(
        self,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Execute the tool.
        """
        raise NotImplementedError