import asyncio

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
import logging

logger = logging.getLogger(__name__)


async def main():

    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "app.mcp.server",
        ],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            tools = await session.list_tools()

            logger.info("\nAvailable MCP tools:")

            for tool in tools.tools:
                logger.info(f"- {tool.name}: {tool.description}")

            result = await session.call_tool(
                "rag_query",
                {
                    "query": "What is this document about?",
                    "knowledge_base_id": "your-knowledge-base-id",
                },
            )

            logger.info("\nResult:")
            logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
