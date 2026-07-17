from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organizations import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Organization)

    async def get_by_slug(
        self,
        slug: str,
    ) -> Organization | None:

        stmt = (
            select(Organization)
            .where(Organization.slug == slug)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> Organization | None:

        stmt = (
            select(Organization)
            .where(Organization.name == name)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()