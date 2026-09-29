import pytest

from app.services.query import QueryService

import logging

logger = logging.getLogger(__name__)



@pytest.mark.asyncio
async def test_query_service():
    service = QueryService()

    result = await service.query(
        query="Manisha Bhatt graduated date",
        organization_id="39c7280f-97b0-45ba-9d07-01d282fde731",
    )

    logger.info("\nRESULT:")
    logger.info(result.model_dump())

    assert result is not None
