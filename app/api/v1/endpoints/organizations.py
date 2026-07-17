from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder

from app.core.responses import APIResponse
from app.dependencies.database import get_uow
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)
from app.services.organization import OrganizationService
from app.uow.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    data: OrganizationCreate,
    uow: UnitOfWork = Depends(get_uow),
):
    service = OrganizationService(uow)
    organization = await service.create(data)

    return APIResponse.success(
        data=jsonable_encoder(organization),
        message="Organization created successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "",
)
async def list_organizations(
    uow: UnitOfWork = Depends(get_uow),
):
    service = OrganizationService(uow)
    organizations = await service.list()

    return APIResponse.success(
        data=jsonable_encoder(organizations),
        message="Organizations retrieved successfully.",
    )


@router.get(
    "/{organization_id}",
)
async def get_organization(
    organization_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
):
    service = OrganizationService(uow)
    organization = await service.get(organization_id)

    return APIResponse.success(
        data=jsonable_encoder(organization),
        message="Organization retrieved successfully.",
    )


@router.patch(
    "/{organization_id}",
)
async def update_organization(
    organization_id: UUID,
    data: OrganizationUpdate,
    uow: UnitOfWork = Depends(get_uow),
):
    service = OrganizationService(uow)
    organization = await service.update(organization_id, data)

    return APIResponse.success(
        data=jsonable_encoder(organization),
        message="Organization updated successfully.",
    )


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_200_OK,  # 200 OK allows sending our JSON success body
)
async def delete_organization(
    organization_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
):
    service = OrganizationService(uow)
    await service.delete(organization_id)

    return APIResponse.success(
        message="Organization deleted successfully.",
    )
