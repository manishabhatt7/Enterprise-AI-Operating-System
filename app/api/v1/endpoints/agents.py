from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_uow
from app.models.users import User
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentUpdate,
)
from app.services.agent import AgentService
from app.uow.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent(
    data: AgentCreate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = AgentService(uow)

    return await service.create(
        data,
        current_user,
    )


@router.get(
    "",
    response_model=list[AgentResponse],
)
async def list_agents(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = AgentService(uow)

    return await service.list(
        current_user,
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = AgentService(uow)

    return await service.get(
        agent_id,
        current_user,
    )


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
)
async def update_agent(
    agent_id: UUID,
    data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = AgentService(uow)

    return await service.update(
        agent_id,
        data,
        current_user,
    )


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = AgentService(uow)

    await service.delete(
        agent_id,
        current_user,
    )