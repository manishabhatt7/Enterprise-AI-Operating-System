import logging
from typing import TYPE_CHECKING

from app.mcp.server import mcp

if TYPE_CHECKING:
    from app.services.query import QueryService

logger = logging.getLogger(__name__)

_query_service = None


def get_query_service():
    global _query_service

    if _query_service is None:
        logger.info("Initializing QueryService")
        from app.services.query import QueryService

        _query_service = QueryService()
        logger.info("QueryService initialized")

    return _query_service


@mcp.tool()
async def rag_query(
    query: str,
    organization_id: str | None = None,
) -> dict:
    """Search and retrieve authoritative documents, policies, entity information,
    and factual context from the enterprise knowledge base.

    Always call this tool first when answering questions regarding company information,
    documents, people, projects, policies, graduation dates, or domain-specific facts.

    Args:
        query: The search query or question to retrieve context for from the knowledge base.
        organization_id: The organization UUID (optional; automatically injected by the backend).
    """

    logger.info(
        "rag_query START | query=%s | organization_id=%s",
        query,
        organization_id,
    )

    try:
        service = get_query_service()

        logger.info("rag_query | executing QueryService")

        result = await service.query(
            query=query,
            organization_id=organization_id,
        )

        logger.info(
            "rag_query SUCCESS | sources=%d | context_length=%d",
            len(result.sources),
            len(result.context),
        )

        return result.model_dump()

    except Exception:
        logger.exception("rag_query FAILED")
        raise