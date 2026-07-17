from fastapi import Depends

from app.dependencies.auth import get_current_user
from app.models.organizations import Organization
from app.models.users import User


async def get_current_organization(
    current_user: User = Depends(get_current_user),
) -> Organization:
    return current_user.organization