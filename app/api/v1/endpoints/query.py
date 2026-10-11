from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.document_processing.schemas.query import (
    QueryRequest,
    QueryResponse,
)
from app.models.users import User
from app.services.query import QueryService

router = APIRouter()

service = QueryService()


@router.post(
    "/query",
    response_model=QueryResponse,
)
async def query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):

    return await service.query(
        query=request.query,
        organization_id=str(current_user.organization_id),
        knowledge_base_id=request.knowledge_base_id,
    )
