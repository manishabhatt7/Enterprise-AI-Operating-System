from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """
    Standard response returned by every tool.
    """

    success: bool

    data: Any | None = None

    error: str | None = None