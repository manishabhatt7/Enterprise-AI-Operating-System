from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.repositories.agent import AgentRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

        self.organizations = OrganizationRepository(session)
        self.users = UserRepository(session)
        self.agents = AgentRepository(session)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()