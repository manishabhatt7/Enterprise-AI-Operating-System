from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_uow
from app.models.users import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)
from app.services.auth import AuthService
from app.uow.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    uow: UnitOfWork = Depends(get_uow),
):

    service = AuthService(uow)

    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenPair,
)
async def login(
    data: LoginRequest,
    uow: UnitOfWork = Depends(get_uow),
):

    service = AuthService(uow)

    return await service.login(data)


@router.post(
    "/refresh",
    response_model=TokenPair,
)
async def refresh(
    data: RefreshRequest,
    uow: UnitOfWork = Depends(get_uow),
):

    service = AuthService(uow)

    return await service.refresh(
        data.refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    data: LogoutRequest,
    uow: UnitOfWork = Depends(get_uow),
):

    service = AuthService(uow)

    await service.logout(
        data.refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def me(
    current_user: User = Depends(get_current_user),
):

    return current_user