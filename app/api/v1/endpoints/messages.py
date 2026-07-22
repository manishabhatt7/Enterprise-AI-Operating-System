from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_uow
from app.models.users import User
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
)
from app.services.ai_chat import AIChatService
from app.services.message import MessageService
from app.uow.unit_of_work import UnitOfWork
from fastapi.responses import StreamingResponse

router = APIRouter(
    prefix="/conversations/{conversation_id}/messages",
    tags=["Messages"],
)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = AIChatService(uow)

    return await service.chat(
        conversation_id=conversation_id,
        content=data.content,
        current_user=current_user,
    )


@router.post(
    "/stream",
)
async def stream_message(
    conversation_id: UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = AIChatService(uow)

    async def event_generator():

        async for token in service.stream_chat(
            conversation_id=conversation_id,
            content=data.content,
            current_user=current_user,
        ):

            yield f"data: {token}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.get(
    "",
    response_model=list[MessageResponse],
)
async def list_messages(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = MessageService(uow)

    return await service.list(
        conversation_id=conversation_id,
        current_user=current_user,
    )