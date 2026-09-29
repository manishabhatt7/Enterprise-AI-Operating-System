from fastapi import APIRouter

from app.document_processing.schemas.query import (
    QueryRequest,
    QueryResponse,
)
from app.services.query import QueryService

router = APIRouter()

service = QueryService()


@router.post(
    "/query",
    response_model=QueryResponse,
)
async def query(
    request: QueryRequest,
):

    return await service.query(
        query=request.query,
        knowledge_base_id=request.knowledge_base_id,
    )