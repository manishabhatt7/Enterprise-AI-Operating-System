from app.core.logging import configure_logging
from app.mcp.server import mcp

import app.mcp.tools.rag  # noqa: F401


def main() -> None:

    configure_logging()
    
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()