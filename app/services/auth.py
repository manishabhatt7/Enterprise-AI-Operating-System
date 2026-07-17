from app.exceptions.auth import (
    InvalidCredentials,
    UserAlreadyExists,
)
from app.managers.auth import auth_manager
from app.models.users import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenPair,
)
from app.uow.unit_of_work import UnitOfWork


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def register(
        self,
        data: RegisterRequest,
    ) -> User:

        existing = await self.uow.users.get_by_email(
            data.email,
        )

        if existing:
            raise UserAlreadyExists()

        hashed_password = await auth_manager.hash_password(
            data.password,
        )

        user = User(
            organization_id=data.organization_id,
            role=data.role,
            full_name=data.full_name,
            email=data.email,
            hashed_password=hashed_password,
        )

        await self.uow.users.create(user)

        await self.uow.commit()

        return user

    async def login(
        self,
        data: LoginRequest,
    ) -> TokenPair:

        user = await self.uow.users.get_by_email(
            data.email,
        )

        if not user:
            raise InvalidCredentials()

        valid = await auth_manager.verify_password(
            data.password,
            user.hashed_password,
        )

        if not valid:
            raise InvalidCredentials()

        return await auth_manager.create_token_pair(
            user_id=str(user.id),
            organization_id=str(user.organization_id),
            role=user.role.value,
        )

    async def refresh(
        self,
        refresh_token: str,
    ) -> TokenPair:

        return await auth_manager.refresh_tokens(
            refresh_token,
        )

    async def logout(
        self,
        refresh_token: str,
    ) -> None:

        await auth_manager.logout(refresh_token)