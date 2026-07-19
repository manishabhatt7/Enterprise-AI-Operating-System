from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agents import Agent
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Agent)

    async def get_by_slug(
        self,
        organization_id: UUID,
        slug: str,
    ) -> Agent | None:

        result = await self.session.execute(
            select(Agent).where(
                Agent.organization_id == organization_id,
                Agent.slug == slug,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        organization_id: UUID,
    ) -> list[Agent]:

        result = await self.session.execute(
            select(Agent).where(Agent.organization_id == organization_id)
        )

        return list(result.scalars().all())
