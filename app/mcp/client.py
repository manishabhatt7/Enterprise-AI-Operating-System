from __future__ import annotations

from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class MCPClient:
    def __init__(
        self,
        server_params: StdioServerParameters,
    ) -> None:
        self.server_params = server_params
        self._exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None

    async def connect(self) -> None:
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)

        errlog = open(
            log_path / "mcp_server.log",
            "a",
            encoding="utf-8",
        )

        self._exit_stack.callback(errlog.close)

        read_stream, write_stream = (
            await self._exit_stack.enter_async_context(
                stdio_client(
                    self.server_params,
                    errlog=errlog,
                )
            )
        )

        self.session = await self._exit_stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
            )
        )

        await self.session.initialize()

    async def list_tools(self) -> list[Any]:
        if self.session is None:
            raise RuntimeError(
                "MCP client is not connected."
            )

        result = await self.session.list_tools()
        return result.tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        if self.session is None:
            raise RuntimeError(
                "MCP client is not connected."
            )

        result = await self.session.call_tool(
            name,
            arguments,
        )

        if getattr(result, "is_error", False):
            raise RuntimeError(
                f"MCP tool '{name}' returned an error: "
                f"{result.content}"
            )

        if getattr(result, "structured_content", None) is not None:
            return result.structured_content

        if isinstance(result.content, list):
            texts = [
                getattr(item, "text", str(item))
                for item in result.content
            ]
            return "\n\n".join(texts)

        return result.content

    async def close(self) -> None:
        await self._exit_stack.aclose()