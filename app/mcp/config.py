from mcp.client.stdio import StdioServerParameters


def get_mcp_server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "app.mcp.main",
        ],
    )