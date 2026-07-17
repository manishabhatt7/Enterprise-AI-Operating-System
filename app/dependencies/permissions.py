from collections.abc import Callable

from fastapi import Depends

from app.core.security import UserRole
from app.dependencies.auth import get_current_user
from app.exceptions.auth import Forbidden
from app.models.users import User


def require_roles(
    *roles: UserRole,
) -> Callable:
    async def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if current_user.role not in roles:
            raise Forbidden()

        return current_user

    return dependency