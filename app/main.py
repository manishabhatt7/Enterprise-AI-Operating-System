from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.exceptions.handlers import register_exception_handlers
from app.mcp.config import get_mcp_server_params

from app.mcp.client import MCPClient

import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    configure_logging()

    server_params = get_mcp_server_params()

    mcp_client = MCPClient(server_params=server_params)

    await mcp_client.connect()

    app.state.mcp_client = mcp_client

    # logger.info("🚀 AIOS API Started")

    # logger.info("🔌 MCP Client Connected")

    yield

    await mcp_client.close()

    logger.info("🛑 AIOS API Stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(api_router)
