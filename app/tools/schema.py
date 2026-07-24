from __future__ import annotations

from typing import Any

from app.tools.base import BaseTool


def tool_to_openai_schema(
    tool: BaseTool,
) -> dict[str, Any]:
    """
    Convert a BaseTool into OpenAI-compatible
    function calling schema.
    """

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }

