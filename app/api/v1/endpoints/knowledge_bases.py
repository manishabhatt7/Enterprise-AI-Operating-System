from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_uow
from app.models.users import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_base import (
    KnowledgeBaseService,
)
from app.uow.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/knowledge-bases",
    tags=["Knowledge Bases"],
)


@router.post(
    "",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = KnowledgeBaseService(
        uow,
    )

    return await service.create(
        data=data,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=list[KnowledgeBaseResponse],
)
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = KnowledgeBaseService(
        uow,
    )

    return await service.list(
        current_user=current_user,
    )


@router.get(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
async def get_knowledge_base(
    knowledge_base_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = KnowledgeBaseService(
        uow,
    )

    return await service.get(
        knowledge_base_id=knowledge_base_id,
        current_user=current_user,
    )


@router.patch(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
async def update_knowledge_base(
    knowledge_base_id: UUID,
    data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = KnowledgeBaseService(
        uow,
    )

    return await service.update(
        knowledge_base_id=knowledge_base_id,
        data=data,
        current_user=current_user,
    )


@router.delete(
    "/{knowledge_base_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_knowledge_base(
    knowledge_base_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = KnowledgeBaseService(
        uow,
    )

    await service.delete(
        knowledge_base_id=knowledge_base_id,
        current_user=current_user,
    )