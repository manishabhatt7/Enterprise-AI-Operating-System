from fastapi import Request

from app.mcp.client import MCPClient


def get_mcp_client(request: Request) -> MCPClient:
    return request.app.state.mcp_client