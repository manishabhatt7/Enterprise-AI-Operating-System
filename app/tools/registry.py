from __future__ import annotations

from app.tools.base import BaseTool


class ToolRegistry:
    """
    Registry for all available tools.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(
        self,
        tool: BaseTool,
    ) -> None:
        """
        Register a tool instance.
        """

        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")

        self._tools[tool.name] = tool

    def get(
        self,
        name: str,
    ) -> BaseTool:
        """
        Get a tool by name.
        """

        try:
            return self._tools[name]

        except KeyError:
            raise ValueError(f"Unknown tool '{name}'.")

    def exists(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a tool exists.
        """

        return name in self._tools

    def list(
        self,
    ) -> list[BaseTool]:
        """
        Return all registered tools.
        """

        return list(self._tools.values())

    def clear(
        self,
    ) -> None:
        """
        Remove all tools.
        """

        self._tools.clear()

    def schemas(
        self,
    ) -> list[dict]:

        from app.tools.schema import tool_to_openai_schema

        return [
            tool_to_openai_schema(tool)
            for tool in self.list()
    ]


tool_registry = ToolRegistry()

__all__ = ["BaseTool", "ToolRegistry", "tool_registry"]
