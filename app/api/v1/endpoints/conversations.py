from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_uow
from app.models.users import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.conversation import ConversationService
from app.uow.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)

@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = ConversationService(uow)

    return await service.create(
        data=data,
        current_user=current_user,
    )

@router.get(
    "",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = ConversationService(uow)

    return await service.list(
        current_user=current_user,
    )

@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = ConversationService(uow)

    return await service.get(
        conversation_id=conversation_id,
        current_user=current_user,
    )

@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def update_conversation(
    conversation_id: UUID,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = ConversationService(uow)

    return await service.update(
        conversation_id=conversation_id,
        data=data,
        current_user=current_user,
    )

@router.post(
    "/{conversation_id}/archive",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def archive_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = ConversationService(uow)

    await service.archive(
        conversation_id=conversation_id,
        current_user=current_user,
    )

@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = ConversationService(uow)

    await service.delete(
        conversation_id=conversation_id,
        current_user=current_user,
    )